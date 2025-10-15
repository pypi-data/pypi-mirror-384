import os

import h5py
import numpy
import pytest
from silx.io.dictdump import dicttoh5

from darfix import dtypes
from darfix.tasks.hdf5_data_selection import HDF5DataSelection


@pytest.mark.parametrize("provide_metadata", (True, False))
@pytest.mark.parametrize("provide_bg", (True, False))
def test_hdf5_data_selection(tmp_path, provide_metadata: bool, provide_bg: bool):
    """test load_process_data function with HDF5 dataset"""
    raw_data_dir = tmp_path / "raw_data"
    raw_data_dir.mkdir()

    raw_data_file = os.path.join(raw_data_dir, "raw.hdf5")
    with h5py.File(raw_data_file, mode="w") as h5f:
        h5f["/path/to/data"] = numpy.arange(0, 100 * 100 * 20).reshape(20, 100, 100)

    if provide_metadata:
        dicttoh5(
            {
                "positioners": {
                    "alpha": 1,
                    "beta": numpy.linspace(0, 1, num=20),
                }
            },
            h5file=raw_data_file,
            h5path="/path/instrument",
            mode="a",
        )
        raw_metadata_path = "/path/instrument/positioners"
    else:
        raw_metadata_path = None

    if provide_bg:
        raw_dark_file = os.path.join(raw_data_dir, "dark.hdf5")
        with h5py.File(raw_dark_file, mode="w") as h5f:
            h5f["/path/to/dark"] = numpy.arange(100 * 100).reshape(1, 100, 100)
        bg_detector_data_path = "/path/to/dark"
    else:
        raw_dark_file = None
        bg_detector_data_path = None

    task = HDF5DataSelection(
        inputs={
            "raw_input_file": raw_data_file,
            "raw_detector_data_path": "/path/to/data",
            "dark_input_file": raw_dark_file,
            "dark_detector_data_path": bg_detector_data_path,
            "raw_metadata_path": raw_metadata_path,
        }
    )
    task.run()
    assert isinstance(task.outputs.dataset, dtypes.Dataset)
    assert task.outputs.dataset.dataset.data is not None
    if provide_bg:
        assert task.outputs.dataset.bg_dataset is not None
    else:
        assert task.outputs.dataset.bg_dataset is None

    if provide_metadata:
        numpy.testing.assert_array_equal(
            task.outputs.dataset.dataset.get_metadata_values(key="beta"),
            numpy.linspace(0, 1, num=20),
        )
    else:
        numpy.testing.assert_array_equal(
            task.outputs.dataset.dataset.get_metadata_values(key="beta"),
            numpy.array([numpy.nan] * 20),
        )
