import os

import h5py
import numpy
import pytest
from silx.io.dictdump import dicttonx

from darfix.tasks.hdf5_scans_concatenation import DataPathFinder


def test_find_detector_dataset(tmp_path):
    """
    test the 'find_detector_dataset' function

    Make sure that:
     * NX_class 'NXdetector' is recognized and get the first priority other any 'untagged' 3d dataset by default.
     * Any 3D dataset is consider to be a detector in the case the NX_class is ignored.
    During processing we will first look for dataset with a NX_class defined as NXdetector
    Then only look for 3D dataset
    """
    test_folder = tmp_path / "test_find_detector_dataset"
    test_folder.mkdir()

    file_path = os.path.join(test_folder, "dataset.hdf5")
    dicttonx(
        {
            "group": {
                "data": "test",
            },
            "my_2d_detector": {
                "data": numpy.linspace(0, 100, 100).reshape(10, 10),
            },
            "my_3d_detector": {
                "data": numpy.linspace(0, 100, 1000).reshape(10, 10, 10),
            },
            "my_2d_nx_detector": {
                "@NX_class": "NXdetector",
                "data": numpy.linspace(0, 100, 100).reshape(10, 10),
            },
            "my_3d_nx_detector": {
                "@NX_class": "NXdetector",
                "data": numpy.linspace(0, 100, 1000).reshape(10, 10, 10),
            },
        },
        h5file=file_path,
        h5path="entry/positioners",
    )

    with h5py.File(file_path, mode="r") as h5f:
        assert (
            DataPathFinder.find_detector_dataset(
                h5f["entry/positioners"], check_nexus_metadata=None
            )
            == h5f["entry/positioners/my_3d_nx_detector/data"]
        )
    with h5py.File(file_path, mode="r") as h5f:
        assert (
            DataPathFinder.find_detector_dataset(
                h5f["entry/positioners"], check_nexus_metadata=False
            )
            == h5f["entry/positioners/my_3d_detector/data"]
        )

    dicttonx(
        {
            "group": {
                "data": "test",
            },
            "my_2d_detector": numpy.linspace(0, 100, 100).reshape(10, 10),
            "my_3d_detector": numpy.linspace(0, 100, 1000).reshape(10, 10, 10),
        },
        h5file=file_path,
        h5path="entry/positioners",
    )

    with h5py.File(file_path, mode="r") as h5f:
        assert (
            DataPathFinder.find_detector_dataset(
                h5f["entry/positioners"], check_nexus_metadata=False
            )
            == h5f["entry/positioners/my_3d_detector"]
        )


def test_from_found_detector_dataset_to_pattern():
    """
    test 'from_found_detector_dataset_to_pattern' static function.
    This function is used during '{detector}' keyword resolution
    """
    assert (
        DataPathFinder.from_found_detector_dataset_to_pattern(
            detector_dataset="1.1/positioners/detector/data",
            scan_path="1.1",
        )
        == r"{scan}/positioners/detector/data"
    )

    assert (
        DataPathFinder.from_found_detector_dataset_to_pattern(
            detector_dataset="1.1/positioners/detector",
            scan_path="1.1",
        )
        == r"{scan}/positioners/detector"
    )

    assert (
        DataPathFinder.from_found_detector_dataset_to_pattern(
            detector_dataset="new/path/positioners/detector",
            scan_path="new/path",
        )
        == r"{scan}/positioners/detector"
    )

    with pytest.raises(ValueError):
        DataPathFinder.from_found_detector_dataset_to_pattern(
            detector_dataset="new/path/positioners/detector",
            scan_path="tot",
        )
