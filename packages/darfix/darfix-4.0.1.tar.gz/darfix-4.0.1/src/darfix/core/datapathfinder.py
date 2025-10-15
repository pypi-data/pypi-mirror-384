from __future__ import annotations

import logging
from typing import Optional

import h5py

_logger = logging.getLogger(__name__)


DETECTOR_KEYWORD = r"{detector}"
SCAN_KEYWORD = r"{scan}"
FIRST_SCAN_KEYWORD = r"{first_scan}"
LAST_SCAN_KEYWORD = r"{last_scan}"

EXISTING_KEYWORDS = (
    SCAN_KEYWORD,
    FIRST_SCAN_KEYWORD,
    LAST_SCAN_KEYWORD,
    DETECTOR_KEYWORD,
)


class UnsolvablePatternError(ValueError):
    """Exception raised when a pattern cannot be solved by the DataPathFinder"""

    pass


class DataPathFinder:
    """Util class to format path from a provided pattern
    At the moment it allows the following keywords:
    * {scan}: will replace the '{scan}' by an HDF5 first level group name
    * {first_scan}: will replace the '{first_scan}' by the first HDF5 group of the list
    * {last_scan}: will replace the '{last_scan}' by the first HDF5 group of the list
    * {detector}: will try to detect automatically the dataset to be used as detector
    """

    def __init__(
        self,
        file_: str | h5py.File,
        pattern: str,
        filter_entries: tuple | None = None,
        allowed_keywords: tuple = EXISTING_KEYWORDS,
    ) -> None:
        self.allowed_keywords = allowed_keywords
        self._can_be_solved = None
        self._file = file_
        assert pattern is not None, "pattern must be defined"
        self._initial_pattern = pattern
        self._solved_pattern = None
        self._filter_entries = filter_entries
        self._update_solved_pattern()

    @property
    def file(self) -> str | h5py.File:
        return self._file

    @file.setter
    def file(self, file: str | None):
        if file is not None and not isinstance(file, str):
            raise TypeError(f"file is expected to be None or a str. Get {file}")
        self._file = file
        self._update_solved_pattern()

    @property
    def pattern(self) -> str:
        return self._initial_pattern

    @pattern.setter
    def pattern(self, pattern: str):
        assert pattern is not None
        self._initial_pattern = pattern
        self._update_solved_pattern()

    @property
    def allowed_keywords(self) -> tuple:
        return self._allowed_keywords

    @allowed_keywords.setter
    def allowed_keywords(self, keywords: tuple):
        for keyword in keywords:
            if keyword not in EXISTING_KEYWORDS:
                raise ValueError(
                    f"keyword {keyword} is invalid. Valid values are {EXISTING_KEYWORDS}"
                )
        self._allowed_keywords = keywords

    @property
    def can_be_solved(self) -> bool:
        return self._can_be_solved

    def format(
        self, scan: str | None, first_scan: str | None, last_scan: str | None
    ) -> str | None:
        """Once the class is instanciated we can call the 'format' function
        to replace keywords by the scan, first_scan, last_scan values
        """
        if not self._can_be_solved:
            return None
        if (
            scan is not None
            and SCAN_KEYWORD in self._solved_pattern
            and SCAN_KEYWORD in self.allowed_keywords
        ):
            return self._solved_pattern.format(scan=scan)
        if (
            first_scan is not None
            and FIRST_SCAN_KEYWORD in self._solved_pattern
            and FIRST_SCAN_KEYWORD in self.allowed_keywords
        ):
            return self._solved_pattern.format(first_scan=first_scan)
        if (
            last_scan is not None
            and LAST_SCAN_KEYWORD in self._solved_pattern
            and LAST_SCAN_KEYWORD in self.allowed_keywords
        ):
            return self._solved_pattern.format(last_scan=last_scan)
        else:
            return self._solved_pattern

    @staticmethod
    def format_str_for_scans_keywords(
        my_str: str, scan: str | None, first_scan: str | None, last_scan: str | None
    ):
        keyword_mapping = {
            FIRST_SCAN_KEYWORD: first_scan,
            LAST_SCAN_KEYWORD: last_scan,
            SCAN_KEYWORD: scan,
        }
        format_args = dict(
            filter(
                lambda a: a[0] in my_str,
                keyword_mapping.items(),
            )
        )
        try:
            return my_str.format(
                **{
                    key.lstrip("{").rstrip("}"): value
                    for key, value in format_args.items()
                }
            )
        except ValueError as e:
            raise UnsolvablePatternError(e)

    def _update_solved_pattern(self):
        """
        create a '_solved_pattern' from the `_initial_pattern` to allow .format to be called on it.
        """
        if self.file is None:
            self._solved_pattern = None
            return
        else:
            self._can_be_solved = True
            self._solved_pattern = self._solve_pattern(pattern=self._initial_pattern)

    def _solve_pattern(self, pattern: str) -> str:
        """
        update the pattern to solve all the different keywords like '{detector}'...
        Return the solved pattern
        """
        assert pattern is not None, "pattern shoudn't be None"
        if (
            DETECTOR_KEYWORD not in pattern
            or DETECTOR_KEYWORD not in self.allowed_keywords
        ):
            solve_detector = False
        elif pattern.endswith(DETECTOR_KEYWORD):
            solve_detector = True
            pattern = pattern.replace(DETECTOR_KEYWORD, "")
        else:
            solve_detector = False
            self._can_be_solved = False
            raise UnsolvablePatternError(
                r"'{detector}' can only be placed a the end of the data path"
            )

        if isinstance(self._file, h5py.File):
            pattern = self._solve_keywords(
                self._file, my_pattern=pattern, solve_detector=solve_detector
            )
        else:
            with h5py.File(self._file, mode="r") as h5f:
                pattern = self._solve_keywords(
                    h5f, my_pattern=pattern, solve_detector=solve_detector
                )
        return pattern

    def _solve_keywords(
        self, h5f_input: h5py.Group, my_pattern: str, solve_detector: bool
    ):
        """check of the pattern can be solved and solve all keywords one by one"""
        first_scan = get_first_group(h5f_input, filter_keys=self._filter_entries)
        last_scan = get_last_group(h5f_input, filter_keys=self._filter_entries)
        if first_scan is None or last_scan is None:
            raise UnsolvablePatternError(
                f"the given file ({h5f_input.file.filename}) does not contain any group that can be considered as scan entry"
            )

        if solve_detector:
            # solve '{detector}'
            path_to_detector_data = self.format_str_for_scans_keywords(
                my_str=my_pattern,
                scan=first_scan,
                first_scan=first_scan,
                last_scan=last_scan,
            )
            detector_group = h5f_input.get(path_to_detector_data, default=None)
            if detector_group is None:
                self._can_be_solved = False
                raise UnsolvablePatternError(
                    f"Unable to find detector root group ({path_to_detector_data}) in the file ({h5f_input.file.filename})"
                )
            detector_dataset = self.find_detector_dataset(
                group=detector_group,
            )
            if detector_dataset is None:
                raise UnsolvablePatternError(
                    f"Unable to find any detector in {path_to_detector_data}"
                )
            else:
                _logger.info(f"First found detector is {detector_dataset.name}")

            # if '{scan}' keyword requested move back from 'real' path to 'pattern file'
            if SCAN_KEYWORD in my_pattern and SCAN_KEYWORD in self.allowed_keywords:
                my_pattern = self.from_found_detector_dataset_to_pattern(
                    detector_dataset=detector_dataset.name,
                    scan_path=first_scan,
                )
            else:
                my_pattern = detector_dataset.name
            return my_pattern

        test_on_first_scan = self.format_str_for_scans_keywords(
            my_str=my_pattern,
            scan=first_scan,
            first_scan=first_scan,
            last_scan=last_scan,
        )
        assert isinstance(test_on_first_scan, str)
        self._can_be_solved = test_on_first_scan in h5f_input
        return my_pattern

    @staticmethod
    def find_detector_dataset(
        group: h5py.Group, check_nexus_metadata: bool | None = None
    ) -> Optional[h5py.Dataset]:
        """
        browse all datasets / groups in the group and return the dataset the most likely to be the detector dataset.

        :param group: HDF5 group containing all elements to check.
        :param check_nexus_metadata: policy regarding checking possible metadata.
            * If True will return the first 'data' dataset contained in a group identified as an 'NXdetector' and being 3D.
            * If False will return the first 3D dataset found (can be in a sub group if named 'data')
            * If None then will look first for detector with nexus metadata else without
        """
        if not isinstance(group, h5py.Group):
            raise ValueError(
                f"group is expected to be an instance of {h5py.Group}. Get {type(group)}"
            )

        if check_nexus_metadata is None:
            return DataPathFinder.find_detector_dataset(
                group=group, check_nexus_metadata=True
            ) or DataPathFinder.find_detector_dataset(
                group=group, check_nexus_metadata=False
            )

        for name in group.keys():
            elmt = group.get(name)
            detector_dataset = DataPathFinder.get_detector(
                elmt=elmt, check_nexus_metadata=check_nexus_metadata
            )
            if detector_dataset is not None:
                return detector_dataset
        return None

    @staticmethod
    def check_is_a_3d_dataset(dataset: h5py.Dataset | h5py.Group):
        return (
            dataset is not None
            and isinstance(dataset, h5py.Dataset)
            and dataset.ndim == 3
        )

    @staticmethod
    def get_detector(
        elmt: h5py.Dataset | h5py.Group, check_nexus_metadata: bool
    ) -> Optional[h5py.Dataset]:
        if check_nexus_metadata:
            # check for nexus compliant detector
            if (
                isinstance(elmt, h5py.Group)
                and elmt.attrs.get("NX_class", None) == "NXdetector"
            ):
                data_dataset = elmt.get("data", None)
                if DataPathFinder.check_is_a_3d_dataset(dataset=data_dataset):
                    return data_dataset
            else:
                return None
        else:
            # check root level dataset
            if isinstance(elmt, h5py.Dataset):
                if DataPathFinder.check_is_a_3d_dataset(dataset=elmt):
                    return elmt
            else:
                assert isinstance(
                    elmt, h5py.Group
                ), f"elmt is expected to be a HDF5 Group. Got type({elmt})"
                # check possible 'data' dataset contained in groups
                data_dataset = elmt.get("data", None)
                if DataPathFinder.check_is_a_3d_dataset(dataset=data_dataset):
                    return data_dataset

    @staticmethod
    def from_found_detector_dataset_to_pattern(detector_dataset: str, scan_path: str):
        """
        Recreate the 'detector_dataset' pattern like '/{scan}/path/to/detectors/groups/detector' from
        the path of the detector for a specific entry ("scan_path")
        'existing' pattern like '/{scan}/path/to/detectors/groups/detector/data' or '/{scan}/path/to/detectors/groups/detector_data'
        """
        if not isinstance(detector_dataset, str):
            raise TypeError(
                f"detector_dataset should be a str. Get {type(detector_dataset)}"
            )
        if not isinstance(scan_path, str):
            raise TypeError(f"scan_path should be a str. Get {type(scan_path)}")
        # get rid of possible initial '/'
        detector_dataset = detector_dataset.lstrip("/")
        scan_path = scan_path.lstrip("/")

        if not detector_dataset.startswith(scan_path):
            raise ValueError(
                f"'detector_dataset' ({detector_dataset}) should start by 'scan_path' ({scan_path})"
            )
        # kind of a left replace based on '/' sections. As we tested the 'scan_path' starts the string it should always work
        scan_depth = len(scan_path.split("/"))
        # replace the scan_path by a '{scan}' pattern
        new_detector_dataset = "/".join(detector_dataset.split("/")[scan_depth:])
        new_detector_dataset = "/".join((SCAN_KEYWORD, new_detector_dataset))
        return new_detector_dataset


def sort_bliss_scan_entries(entries: tuple):
    """
    Sort Bliss scans (x.y) according to their scan numbers and processed entries (`entry_xxxx`) according to their entry number.
    """

    def get_entry_scan_num(entry_name):
        # concatenation resulting output entry name is "entry_0000" so let's handle this case.
        if entry_name.startswith("entry_"):
            return int(entry_name.lstrip("entry_"))
        # entries are expected to be given as x.y (bliss policy)
        return int(entry_name.lstrip("/").split(".")[0])

    return sorted(entries, key=get_entry_scan_num)


def _get_next_group(
    h5f: h5py.Group | str,
    reverse_iteration: bool,
    filter_keys: tuple | None = None,
    as_hdf5_item: bool = False,
):
    """util to retrieve the first Group not in filtered_keys of a file."""
    if as_hdf5_item and not isinstance(h5f, h5py.Group):
        raise TypeError(
            "To return the group as an hdf5 item you must provide hf5 as h5py.Group. Else returned group will be closed with the file."
        )
    if filter_keys is not None:
        # remove the left '/' that can sometime bring troubles
        filter_keys = [filter_key.lstrip("/") for filter_key in filter_keys]

    def filter_not_group(root):
        try:
            entries = sort_bliss_scan_entries(root.keys())
        except ValueError:
            _logger.error("Failed to order scans by indices. Take them 'unordered'")
            entries = root.keys()

        if reverse_iteration:
            key_iterator = list(entries)
            key_iterator.reverse()
        else:
            key_iterator = entries
        for key in key_iterator:
            if filter_keys is not None and key.lstrip("/") not in filter_keys:
                continue
            elmt = root.get(key)
            if isinstance(elmt, h5py.Group):
                if as_hdf5_item:
                    return elmt
                else:
                    return elmt.name
        return None

    if isinstance(h5f, str):
        with h5py.File(h5f, mode="r") as root:
            return filter_not_group(root)
    else:
        return filter_not_group(h5f)


def get_first_group(
    h5f: h5py.Group | str, filter_keys: tuple | None = None, as_hdf5_item: bool = False
) -> str | None:
    return _get_next_group(
        h5f=h5f,
        filter_keys=filter_keys,
        reverse_iteration=False,
        as_hdf5_item=as_hdf5_item,
    )


def get_last_group(
    h5f: h5py.Group | str, filter_keys: tuple | None = None, as_hdf5_item: bool = False
) -> str | None:
    return _get_next_group(
        h5f=h5f,
        filter_keys=filter_keys,
        reverse_iteration=True,
        as_hdf5_item=as_hdf5_item,
    )
