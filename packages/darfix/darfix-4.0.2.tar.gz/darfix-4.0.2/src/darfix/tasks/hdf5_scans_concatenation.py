from __future__ import annotations

import logging
import os
from typing import Optional

import h5py
import numpy
from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.missing_data import is_missing_data
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict
from pydantic import Field
from silx.io.dictdump import dicttoh5
from silx.utils.enum import Enum as _Enum

from darfix.core.datapathfinder import DETECTOR_KEYWORD
from darfix.core.datapathfinder import SCAN_KEYWORD
from darfix.core.datapathfinder import DataPathFinder
from darfix.core.datapathfinder import sort_bliss_scan_entries
from darfix.core.settings import PROCESSED_DATA
from darfix.core.settings import RAW_DATA

_logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class VDS_POLICY(_Enum):
    """
    Virtual dataset policy. Values can be:
    * 'absolute': in this case the links will be done with the absolute path. Safer for 'single' shot processing.
    * 'relative': in this case the links will be done with relative path. Safer if we want to move files. Links will be preserved as long as relative paths are preserved.
    """

    RELATIVE = "relative"
    ABSOLUTE = "absolute"


def _concatenate_dict(
    dict_1: dict[str, numpy.ndarray], dict_2: dict[str, numpy.ndarray]
) -> dict[str, numpy.ndarray]:
    """
    concatenate two dicts into a third dict. Keys are str and values are numpy.ndarray.
    If a dict contains the same key then the two values (numpy array) will be concatenated.
    """
    assert isinstance(dict_1, dict)
    assert isinstance(dict_2, dict)
    res = {}
    # concatenate keys. Note: we create a new list to keep keys ordering and be consistent.
    # creating a set for example we reorder the keys
    keys = list(dict_1.keys())
    keys.extend(filter(lambda key: key not in dict_1.keys(), dict_2.keys()))
    for key in keys:
        if key in dict_1.keys() and key in dict_2.keys():
            res[key] = numpy.concatenate((dict_1[key], dict_2[key]))
        elif key in dict_1.keys():
            res[key] = dict_1[key]
        else:
            res[key] = dict_2[key]
    return res


def _check_positioners_consistency(my_dict: dict) -> None:
    """
    make sure all the values of 'my_dict' have the same number of elements
    """
    n_elmts = numpy.median([len(value) for value in my_dict.values()])
    for key, value in my_dict.items():
        if len(value) != n_elmts:
            _logger.warning(
                f"Found inconsistent positioner dataset '{key}'. Get {len(value)} elements when {n_elmts} expected"
            )


def _filter_static_positioners(my_dict: dict) -> None:
    """
    replace all positioners which have a unique value by a scalar
    """
    keys = tuple(my_dict.keys())
    for key in keys:
        uniques = numpy.unique(my_dict[key])
        if len(uniques) == 1:
            my_dict[key] = uniques[0]


def create_virtual_source(
    input_dataset: h5py.Dataset,
    output_file: str,
    vds_policy: str | VDS_POLICY = VDS_POLICY.RELATIVE,
) -> h5py.VirtualSource:
    """
    create the VirtualSource according to the defined policy
    """
    vds_policy = VDS_POLICY(vds_policy)
    if vds_policy is VDS_POLICY.ABSOLUTE:
        return h5py.VirtualSource(input_dataset)
    elif vds_policy is VDS_POLICY.RELATIVE:
        relpath = os.path.relpath(
            os.path.abspath(input_dataset.file.filename),
            os.path.dirname(os.path.abspath(output_file)),
        )
        if not relpath.startswith("./"):
            relpath = "./" + relpath
        return h5py.VirtualSource(
            path_or_dataset=relpath,
            name=input_dataset.name,
            shape=input_dataset.shape,
            dtype=input_dataset.dtype,
        )
    else:
        raise ValueError(
            f"VDS_POLICY should be 'absolute' or 'relative'. Get '{VDS_POLICY}'"
        )


def concatenate_scans(
    input_file: str,
    entries_to_concatenate: Optional[tuple],
    output_file: str,
    detector_data_path: str,
    positioners_group_path: str,
    output_entry_name: str = "entry_0000",
    overwrite: bool = False,
    vds_policy: str | VDS_POLICY = VDS_POLICY.RELATIVE,
) -> None:
    """
    :param input_file: proposal file containing link to all the detector frame...
    :param entries_to_concatenate: tuple of all entries to concatenate. Order will be preserved. If None provided then all entries will be concatenated
    :param output_file: location of the output file
    :param detector_data_path: path to the detector dataset. Expected to be provided as '{scan}/path/to/detector/dataset' (a) or '{scan}/path/to/{detector}' (b).

        * in the use case (a) the relative (to {scan}) path is fully provided and will be take 'as such'
        * in the use case (b) only a folder path is provided and the keyword {detector} must be provided at the end. In this case the function will call the 'find_detector_dataset' function. And will browse the group for any detector.
          First groups with 'nexus' attributes fitting a 3D detector will be search. If none are found then it will return the first 3D dataset found.
    :param positioners_group_path: path to the positioners datasets (containing motor positions). Expected to be provided as a '{scan}/path/to/group' pattern. Where the '{scan}' part will be replaced by input file first level items.
    :param output_entry_name: HDF5 group name that will contain the concatenated detector data + metadata.
    :param overwrite: if False and output file exist then will not overwrite it
    :param vds_policy: policy regarding the VirtualDataSet. Either "absolute" or "relative"
    """
    _logger.info("start concatenation")
    # check inputs
    if os.path.exists(output_file) and not overwrite:
        raise OSError(
            f"output file exists ({output_file}). Please remove it before processing or set 'overwrite to True'"
        )
    if not isinstance(detector_data_path, str):
        raise TypeError("detector_dataset_path should be a str")
    if not isinstance(output_entry_name, str):
        raise TypeError("output_entry_name should be a str")
    if not isinstance(positioners_group_path, str):
        raise TypeError("positioners_dataset_path should be a str")

    detector_data_path_finder = DataPathFinder(
        file_=input_file,
        pattern=detector_data_path,
        filter_entries=entries_to_concatenate,
        allowed_keywords=(SCAN_KEYWORD, DETECTOR_KEYWORD),
    )
    positioners_data_path_finder = DataPathFinder(
        file_=input_file,
        pattern=positioners_group_path,
        filter_entries=entries_to_concatenate,
        allowed_keywords=(SCAN_KEYWORD, DETECTOR_KEYWORD),
    )

    # concatenate
    with h5py.File(input_file, mode="r") as h5f_input:
        if entries_to_concatenate is None:
            # sort entries to concatenate
            try:
                entries_to_concatenate = sort_bliss_scan_entries(h5f_input.keys())
            except ValueError:
                _logger.error("Failed to order scans by indices. Take them 'unordered'")
                entries_to_concatenate = tuple(h5f_input.keys())

        _logger.info(f"(sorted) entries to concatenate {entries_to_concatenate}")
        entries_n_frame = []
        # store the number of frames along all entries
        frame_shape = None
        detector_data_type = None
        positioners = {}
        virtual_sources = []

        # number of frame concatenateed
        for entry in entries_to_concatenate:

            # update the entry_detector_path. Note: first_scan and last_scan have no meaning in the case
            # of concatenation.
            entry_detector_path = detector_data_path_finder.format(
                scan=entry, first_scan=None, last_scan=None
            )

            if entry_detector_path not in h5f_input:
                _logger.error(
                    f"Unable to find detector path '{entry_detector_path}' from file '{input_file}'"
                )
                continue
            if h5f_input[entry_detector_path].ndim != 3:
                raise ValueError(
                    f"detector dataset are expected to be 3D. Get {h5f_input[entry_detector_path].ndim}"
                )
            # 1.1: get metadata from the dataset and make sure it is coherent along all the detector datasets
            entry_n_frame = h5f_input[entry_detector_path].shape[0]
            entry_frame_shape = h5f_input[entry_detector_path].shape[1:]
            entries_n_frame.append(entry_n_frame)
            if frame_shape is None:
                frame_shape = entry_frame_shape
            elif entry_frame_shape != frame_shape:
                raise ValueError(
                    f"Incoherent frame shape. {entry} get {entry_frame_shape} when {frame_shape} expected"
                )
            if detector_data_type is None:
                detector_data_type = h5f_input[entry_detector_path].dtype
            elif detector_data_type != h5f_input[entry_detector_path].dtype:
                raise TypeError(
                    f"Inconsistent data type between the scan. {entry} get {h5f_input[entry_detector_path].dtype} when {detector_data_type} expected"
                )
            # 1.2: create VirtualSource to be used once entries browse

            virtual_sources.append(
                create_virtual_source(
                    input_dataset=h5f_input[entry_detector_path],
                    output_file=output_file,
                    vds_policy=vds_policy,
                )
            )
            # 2.0 handle positioners.
            # note: positioners dataset will be copied
            # number of frame in the current entry / scan
            entry_positioner_path = positioners_data_path_finder.format(
                scan=entry, first_scan=None, last_scan=None
            )
            if entry_positioner_path not in h5f_input:
                _logger.error(
                    f"Unable to find positioners path '{entry_positioner_path}' from file '{input_file}'"
                )
                continue
            entry_positioners_grp = h5f_input[entry_positioner_path]
            # HDF5 group containing the positioners
            entry_positioners = {}
            # dict used to concatenate all the positioners as numpy array
            for key in entry_positioners_grp:
                dataset = entry_positioners_grp[key]
                if not isinstance(dataset, h5py.Dataset):
                    _logger.warning(
                        f"Found a none h5py.Dataset in entry {entry_positioners_grp}: {key}"
                    )
                elif dataset.ndim > 2:
                    # in case a dataset with more than 2 dimensions is part of the positioners, simply ignore it.
                    _logger.debug(f"Skip a dataset higher than 2D ({dataset.name})")
                else:
                    value = dataset[()]
                    if numpy.isscalar(value) or len(value.shape) == 0:
                        # convert scalars to arrays. As a value can be static in a scan context but
                        # dynamic / array in the scope of the full acquisition
                        value = numpy.array([value] * entry_n_frame)
                    entry_positioners[key] = value

            positioners = _concatenate_dict(positioners, entry_positioners)

        # create output directory in case not existing (h5py won't do it)
        os.makedirs(
            os.path.dirname(os.path.abspath(output_file)),
            exist_ok=True,
        )
        # write the detector virtual dataset (VDS) to output file
        with h5py.File(output_file, mode="a") as h5f_output:
            raw_entry_name = detector_data_path.split("/")[0]
            entry_name = raw_entry_name.format(
                scan=output_entry_name,
                first_scan=None,
                last_scan=None,
            )
            if entry_name in h5f_output and overwrite:
                del h5f_output[entry_name]

            output_detector_dataset_path = detector_data_path_finder.format(
                scan=output_entry_name,
                first_scan=None,
                last_scan=None,
            )
            n_frames = numpy.sum(entries_n_frame)
            virtual_layout = h5py.VirtualLayout(
                shape=(n_frames, frame_shape[0], frame_shape[1]),
                dtype=detector_data_type,
            )
            assert len(virtual_sources) == len(
                entries_n_frame
            ), "we expect one virtual source per entry"
            virtual_layout_index = 0
            for entry_n_frame, virtual_source in zip(entries_n_frame, virtual_sources):
                virtual_layout[
                    virtual_layout_index : virtual_layout_index + entry_n_frame
                ] = virtual_source
                virtual_layout_index += entry_n_frame

            h5f_output.create_virtual_dataset(
                output_detector_dataset_path, virtual_layout
            )
    # check number of elements is coherent else warm the user
    _check_positioners_consistency(positioners)
    _filter_static_positioners(positioners)

    dicttoh5(
        positioners,
        h5file=output_file,
        h5path=positioners_group_path.format(scan=output_entry_name),
        mode="a",
    )

    _logger.info(
        f"concatenation finished. You can run 'silx view {output_file}' to check the result"
    )


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    input_file: str = Field(
        examples=["/path/to/input/file.h5"],
        description="Path to the input file containing scans to concatenate.",
    )
    entries_to_concatenate: tuple[str, ...] | MissingData = Field(
        default=MISSING_DATA,
        examples=[("/1.1", "/2.1", "/3.1")],
        description="Entries (scans) in the file to concatenate. If not provided, all entries will be concatenated.",
    )
    detector_data_path: str | MissingData = Field(
        default=MISSING_DATA,
        examples=[
            "{scan}/instrument/measurement/my_detector",
            "{scan}/instrument/measurement/{detector}",
        ],
        description="Path pattern to the detector data in the input file. If `{detector}` is in the pattern then all the datasets from the subpath will be browsed in order to 'guess' the detector to be used. If not provided, {scan}/measurement/{detector} is the default pattern",
    )
    positioners_group_path: str | MissingData = Field(
        default=MISSING_DATA,
        examples=["{scan}/instrument/positioners"],
        description="Path pattern to the positioners group in the input file. If not provided, {scan}/instrument/positioners is the default pattern",
    )
    overwrite: bool | MissingData = Field(
        default=MISSING_DATA,
        description="If True then will overwrite the output file if it exists. False if not provided.",
    )
    output_file: str | MissingData = Field(
        default=MISSING_DATA,
        examples=["/path/to/output/file.h5"],
        description="Path to the output file. Must be provided if guess_output_file is False.",
    )
    """Path to the output file. If not provided then will try to guess it from the input file."""
    guess_output_file: bool | MissingData = Field(
        default=MISSING_DATA,
        description="If True then will try to guess the output file from the input file. False if not provided.",
    )


class ConcatenateHDF5Scans(
    Task,
    input_model=Inputs,
    output_names=[
        "output_file",
    ],
):
    """
    Concatenate a set of scans / entries contained in 'input_file'.
    If entries_to_concatenate is None then all entries will be concatenated

    * 'detector_data_path' is the pattern to find all the detector data path. It
    is expected to look like '{scan}/instrument/measurement/my_detector'. In this case
    it will look for each scan at the same location. So for the scan '1.1' it
    will look for '1.1/instrument/measurement/my_detector'. For the scan 2.1 it will look for '2.1/instrument/measurement/my_detector'...
    If the {detector} is provided then all the dataset part of the upper path will be browse in order to 'guess' the detector to be used.
    Using the 'find_detector' function.
    * 'positioners_group_path' is the pattern to find all positioner groups. And should look like '{scan}/instrument/positioners'
    For the scan '1.1' it will look for '1.1/instrument/positioners'...
    """

    DEFAULT_DETECTOR_DATA_PATH = SCAN_KEYWORD + "/measurement/" + DETECTOR_KEYWORD

    DEFAULT_POSITIONERS_DATA_PATH = SCAN_KEYWORD + "/instrument/positioners"

    def run(self):
        detector_data_path = self.get_input_value(
            "detector_data_path", self.DEFAULT_DETECTOR_DATA_PATH
        )
        positioners_group_path = self.get_input_value(
            "positioners_group_path", self.DEFAULT_POSITIONERS_DATA_PATH
        )
        output_file = self.get_input_value("output_file")
        if is_missing_data(output_file):
            if not self.get_input_value("guess_output_file", False):
                raise ValueError(
                    "Either the output file should be provided or you should ask to determine automatically output file ('guess_output_file')"
                )
            output_file = guess_output_file(input_file=output_file)
        concatenate_scans(
            input_file=self.inputs.input_file,
            entries_to_concatenate=self.get_input_value("entries_to_concatenate", None),
            output_file=output_file,
            detector_data_path=detector_data_path,
            positioners_group_path=positioners_group_path,
            overwrite=self.get_input_value("overwrite", False),
        )
        self.outputs.output_file = self.inputs.output_file


def find_scan_data_path(file_path, pattern_data_path):
    with h5py.File(file_path) as h5f:
        pattern_data_path = pattern_data_path.lstrip("/")
        if pattern_data_path.startswith("{scan}"):
            try:
                first_scan = h5f.get(next(h5f.keys()))
            except StopIteration:
                # in case the hdf5 is empty
                return None
            path_search = pattern_data_path.replace("{scan}", "")
        else:
            first_scan = None
            path_search = pattern_data_path

        if path_search not in h5f:
            return None

        if first_scan is not None:
            result = pattern_data_path.replace(scan=first_scan.name)
        else:
            result = path_search
        return result


def guess_output_file(input_file: str, target_processed_data_dir: bool = True):
    """
    propose an output file path for scan concatenation from an input file

    :param input_file: file containing the scans to concatenate
    :param target_processed_data_dir: If true then will try to make the output file as part of 'PROCESSED_DATA' folder.
    """

    file_path, ext = os.path.splitext(input_file)
    output_file = "".join(
        (
            "_".join((file_path, "darfix_concat")),
            ext,
        )
    )
    if target_processed_data_dir:
        splitted_paths = output_file.split(os.path.sep)
        # reverse it to find the lower level value of '_RAW_DATA_DIR_NAME' if by any 'chance' has several in the path
        # in this case this is most likely what we want
        splitted_paths = splitted_paths[::-1]
        try:
            index_raw_data = splitted_paths.index(RAW_DATA)
        except ValueError:
            # in the case RAW_DATA dir name is not contained
            pass
        else:
            splitted_paths[index_raw_data] = PROCESSED_DATA
        output_file = os.sep.join(splitted_paths[::-1])
    return output_file
