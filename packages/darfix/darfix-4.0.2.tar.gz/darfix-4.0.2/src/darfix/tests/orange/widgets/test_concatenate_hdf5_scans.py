import os

from ewoksorange.tests.conftest import qtapp  # noqa F401

from darfix.gui.utils.qsignalspy import QSignalSpy
from orangecontrib.darfix.widgets.concatenateHDF5 import ConcatenateWidgetOW

from ...tasks.test_hdf5_scans_concatenation import create_scans


def test_ConcatenateWidgetOW(tmp_path, qtapp):  # noqa F811
    """
    test the ConcatenateWidgetOW

    Define inputs from the GUI and launch concatenation.
    Make sure the expected output file exists (but doesn't check the content. The Ewoks task should check this).
    """
    window = ConcatenateWidgetOW()

    assert window.get_task_input_values() == {
        "detector_data_path": r"{scan}/measurement/{detector}",
        "positioners_group_path": r"{scan}/instrument/positioners",
        "overwrite": True,
    }

    test_dir = tmp_path / "test_ConcatenateWidgetOW"
    test_dir.mkdir()
    raw_data_file = os.path.join(str(test_dir), "scan_to_concateante.h5")
    create_scans(file_path=raw_data_file, n_scan=3)

    concat_widget = window._widget._mainWidget
    concat_widget.setOverwrite(False)
    concat_widget.setInputFile(raw_data_file)
    output_file = os.path.join(str(test_dir), "scan_to_concateante_darfix_concat.h5")
    assert window.get_task_input_values() == {
        "detector_data_path": r"{scan}/measurement/{detector}",
        "positioners_group_path": "{scan}/instrument/positioners",
        "overwrite": True,
        "input_file": raw_data_file,
        "output_file": output_file,
    }
    assert not os.path.exists(output_file)

    waiter = QSignalSpy(window.task_executor.finished)
    window.execute_ewoks_task()
    waiter.wait(5000)
    assert os.path.exists(output_file)
    assert window.task_executor.succeeded

    concat_widget.setDetectorPath("/first/path")
    concat_widget.setPositionersGroupPath("/second/path")
    assert window.get_task_input_values() == {
        "overwrite": True,
        "input_file": raw_data_file,
        "output_file": output_file,
        "detector_data_path": "/first/path",
        "positioners_group_path": "/second/path",
    }
    concat_widget.setSelectedEntries(("/1.1", "3.1"))
    assert window.get_task_input_values() == {
        "overwrite": True,
        "entries_to_concatenate": ("/1.1", "/3.1"),
        "input_file": raw_data_file,
        "output_file": output_file,
        "detector_data_path": "/first/path",
        "positioners_group_path": "/second/path",
    }
