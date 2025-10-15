import os

import h5py
import numpy
import pytest
from ewoksorange.tests.conftest import qtapp  # noqa F401

from darfix.dtypes import Dataset
from darfix.gui.utils.qsignalspy import QSignalSpy
from orangecontrib.darfix.widgets.hdf5dataselection import HDF5DataSelectionWidgetOW


@pytest.mark.skipif(QSignalSpy is None, reason="Unable to import QSignalSpy")
def test_HDF5DataSelectionWidgetOW(tmp_path, qtapp):  # noqa F811
    raw_data_dir = tmp_path / "raw_data"
    raw_data_dir.mkdir()

    raw_data_file = os.path.join(raw_data_dir, "raw.hdf5")
    with h5py.File(raw_data_file, mode="w") as h5f:
        detector = h5f.create_group("/1.1/instrument/detector/")
        detector["image"] = numpy.arange(0, 100 * 100 * 20).reshape(20, 100, 100)
        detector.attrs["NX_class"] = "NXdetector"
        detector["type"] = "lima"
        h5f["/1.1/measurement/detector"] = h5py.SoftLink(detector.name)

    window = HDF5DataSelectionWidgetOW()
    window._rawDataSelection.setFilePath(raw_data_file)
    expected_inputs = {
        "raw_input_file": raw_data_file,
        "raw_detector_data_path": "/1.1/measurement/detector",
        "raw_metadata_path": "/1.1/instrument/positioners",
    }
    assert window.getInputs() == expected_inputs

    window._rawDataSelection.setDetectorPath("/1.1/instrument/detector/image")
    expected_inputs["raw_detector_data_path"] = "/1.1/instrument/detector/image"
    assert window.getInputs() == expected_inputs

    # this was one of the API question. What to provide if
    # the user don't want to load metadata (like for dark).
    # We went for an empty string "". Because from the task class
    # point of view the most common would be to use the default pattern.
    window._rawDataSelection.setPositionersPath("")
    expected_inputs["raw_metadata_path"] = ""
    assert window.getInputs() == expected_inputs

    window._workflowTitleLineEdit.setText("my workflow title")
    window.saveInputs()
    expected_inputs["workflow_title"] = "my workflow title"
    assert window.getInputs() == expected_inputs

    assert window.task_succeeded is None

    waiter = QSignalSpy(window.task_executor.finished)
    window.execute_ewoks_task()
    # wait for the task_executor to be finished
    waiter.wait(5000)

    dataset = window.get_task_output_value("dataset")
    assert isinstance(dataset, Dataset)
