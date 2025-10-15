import os
from typing import NamedTuple

import numpy
import pytest
from silx.io.dictdump import nxtodict

from darfix.tasks.hdf5_scans_concatenation import ConcatenateHDF5Scans
from darfix.tasks.hdf5_scans_concatenation import _concatenate_dict
from darfix.tasks.hdf5_scans_concatenation import guess_output_file
from darfix.tests.utils import create_scans


class DetectorDataParameter(NamedTuple):
    raw_data_path: str
    data_path_pattern: str


@pytest.mark.parametrize("overwrite", (True, False))
@pytest.mark.parametrize(
    "detector_data_path_and_pattern",
    (
        DetectorDataParameter(
            "{scan}/measurement/my_detector", "{scan}/measurement/{detector}"
        ),
        DetectorDataParameter(
            "{scan}/instrument/my_detector/data", "{scan}/instrument/{detector}"
        ),
    ),
)
def test_scan_concatenation(tmp_path, detector_data_path_and_pattern, overwrite: bool):
    """
    creates 'n' scans and concatenate them together.
    Then check that `ConcatenateHDF5Scans` task is correctly handling it.

    :param detector_data_path: path to the detector. Can contain the full path or the '{detector}' keyword. In this case search of the detector path will be done automatically.
    """
    raw_detector_data_path, pattern = detector_data_path_and_pattern
    test_folder = tmp_path / "test_concatenation"
    test_folder.mkdir()
    input_file = test_folder / "raw_data.hdf5"
    output_file = test_folder / "concatenate_data.hdf5"

    create_scans(file_path=input_file, detector_path=raw_detector_data_path)

    task = ConcatenateHDF5Scans(
        inputs={
            "input_file": input_file,
            "output_file": output_file,
            "detector_data_path": pattern,
            "overwrite": overwrite,
        }
    )
    task.run()

    assert os.path.exists(output_file)
    output_dict = nxtodict(
        h5file=str(output_file),
    )

    def get_nx_dict_key(ddict: dict, data_path):
        for key in data_path.split("/"):
            ddict = ddict.get(key, {})
        return ddict

    output_detector_dataset = get_nx_dict_key(
        output_dict,
        data_path=raw_detector_data_path.format(scan="entry_0000"),
    )

    assert isinstance(
        output_detector_dataset, numpy.ndarray
    ), f"'output_detector_dataset' should be a numpy array. Get {type(output_detector_dataset)}"

    # make sure the detector has been properly concatenated
    raw_detector_dataset = numpy.linspace(0, 5, 100 * 100 * 4).reshape(4, 100, 100)
    numpy.testing.assert_almost_equal(
        output_detector_dataset,
        numpy.concatenate(
            (
                raw_detector_dataset,
                raw_detector_dataset,
                raw_detector_dataset,
            )
        ),
    )
    # make sure the positioners group has been properly concatenated
    output_positioners_group = get_nx_dict_key(
        output_dict,
        ConcatenateHDF5Scans.DEFAULT_POSITIONERS_DATA_PATH.format(scan="entry_0000"),
    )

    # if there is a single value along all the dataset then we save a unique value in the final dataset
    assert output_positioners_group["alpha"] == 1.0
    numpy.testing.assert_array_almost_equal(
        output_positioners_group["beta"],
        numpy.concatenate(
            [
                numpy.arange(4, dtype=numpy.float32),
                numpy.arange(4, dtype=numpy.float32),
                numpy.arange(4, dtype=numpy.float32),
            ]
        ),
    )
    numpy.testing.assert_array_almost_equal(
        output_positioners_group["gamma"],
        numpy.concatenate(
            [
                numpy.linspace(68, 70, 4, dtype=numpy.uint8),
                numpy.linspace(68, 70, 4, dtype=numpy.uint8),
                numpy.linspace(68, 70, 4, dtype=numpy.uint8),
            ]
        ),
    )
    # if there is not enough points (not one per frame) then we concatenate it anyway (but with a warning)
    numpy.testing.assert_array_almost_equal(
        output_positioners_group["delta"],
        numpy.concatenate(
            [
                numpy.arange(2, dtype=numpy.int16),
                numpy.arange(2, dtype=numpy.int16),
                numpy.arange(2, dtype=numpy.int16),
            ]
        ),
    )

    # check that according to the 'overwrite' parameter we can overwrite the file or not
    if overwrite:
        task.run()
    else:
        with pytest.raises(OSError):
            task.run()


@pytest.mark.parametrize("target_processed_data_dir", (True, False))
def test_guess_output_file(target_processed_data_dir):
    """
    Test 'guess_output_file' function. This function is used to determine a 'default' output path for a scan that we want to concatenate.
    """
    input_file = os.path.sep.join(("path", "to", "file.hdf5"))
    expected_output_file = os.path.sep.join(("path", "to", "file_darfix_concat.hdf5"))
    assert (
        guess_output_file(
            input_file=input_file, target_processed_data_dir=target_processed_data_dir
        )
        == expected_output_file
    )

    input_file = os.path.sep.join(("path", "to", "RAW_DATA", "file.nx"))
    if target_processed_data_dir:
        expected_output_file = os.path.sep.join(
            ("path", "to", "PROCESSED_DATA", "file_darfix_concat.nx")
        )
    else:
        expected_output_file = os.path.sep.join(
            ("path", "to", "RAW_DATA", "file_darfix_concat.nx")
        )
    assert (
        guess_output_file(
            input_file=input_file, target_processed_data_dir=target_processed_data_dir
        )
        == expected_output_file
    )


def test__concatenate_dict():
    """test _concatenate_dict function"""
    res = _concatenate_dict(
        {
            "a": numpy.zeros(2),
            "b": numpy.zeros(2),
        },
        {
            "a": numpy.ones(2),
            "c": numpy.ones(2),
        },
    )
    assert tuple(res.keys()) == ("a", "b", "c")
    numpy.testing.assert_array_equal(
        res["a"], numpy.concatenate([numpy.zeros(2), numpy.ones(2)])
    )
    numpy.testing.assert_array_equal(res["b"], numpy.zeros(2))
    numpy.testing.assert_array_equal(res["c"], numpy.ones(2))
