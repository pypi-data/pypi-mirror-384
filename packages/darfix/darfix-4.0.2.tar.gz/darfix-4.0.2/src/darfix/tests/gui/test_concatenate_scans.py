import os

import h5py
import numpy
import pytest
from ewoksorange.tests.conftest import qtapp  # noqa F401

from darfix.gui.concatenate_scans import ConcatenateHDF5Scans
from darfix.gui.concatenate_scans import ConcatenateScansWidget
from darfix.gui.concatenate_scans import HDF5ConcatenateWindow
from darfix.gui.concatenate_scans import HDF5EntriesWidget
from darfix.gui.configuration.level import ConfigurationLevel


@pytest.mark.parametrize(
    "config_level", (ConfigurationLevel.ADVANCED, ConfigurationLevel.REQUIRED)
)
def test_HDF5ConcatenateWindow_config_level(config_level, qtapp):  # noqa F811
    """test the HDF5ConcatenateWindow different configuration level"""
    window = HDF5ConcatenateWindow()
    widget = window.getConcatenateScansWidget()
    widget.setConfigurationLevel(config_level)
    required_widgets = (
        widget._inputFileSelector,
        widget._scanEntries,
    )
    advanced_widgets = (
        widget._outputFileSelector,
        widget._autoUpdate,
        widget._positionerDataPath,
        widget._detectorDataPath,
        widget._overwriteOutput,
    )
    window.show()
    for widget in required_widgets:
        assert widget.isVisible()

    for widget in advanced_widgets:
        if config_level >= ConfigurationLevel.ADVANCED:
            assert widget.isVisible()
        else:
            assert not widget.isVisible()


def test_ConcatenateScansWidget(tmp_path, qtapp):  # noqa F811
    """
    test of the ConcatenateScansWidget widget.

    Make sure it is correctly updated when a file is provided
    """
    test_dir = tmp_path / "test_concatenate_widget"
    test_dir.mkdir()

    test_file = os.path.join(test_dir, "test.hdf5")
    n_scan = 4
    with h5py.File(test_file, mode="w") as h5f:
        for i_scan in range(n_scan):
            # measurement
            h5f[f"{i_scan + 1}.1/measurement/detector"] = numpy.linspace(
                0, 100, 1000
            ).reshape((10, 10, 10))
            for pos_name, pos_value in {
                "alpha": 1,
                "beta": numpy.arange(0 + i_scan, 10 + i_scan, 1),
            }.items():
                h5f[f"{i_scan + 1}.1/instrument/positioners/{pos_name}"] = pos_value
        # add a dataset to make sure those are filtered
        h5f["dataset"] = "test"

    widget = ConcatenateScansWidget()
    widget.setInputFile(test_file)
    assert widget.getSelectedEntries() == tuple([f"/{i+1}.1" for i in range(n_scan)])
    assert widget.getOutputFile() == os.path.join(test_dir, "test_darfix_concat.hdf5")
    assert widget.getInputFile() == test_file
    assert (
        widget.getDetectorDataPathSelection().getPattern()
        == ConcatenateHDF5Scans.DEFAULT_DETECTOR_DATA_PATH
    )
    assert (
        widget.getDetectorDataPathSelection().getExample()
        == "/1.1/measurement/detector"
    )
    assert (
        widget.getMetadataPathSelection().getPattern()
        == ConcatenateHDF5Scans.DEFAULT_POSITIONERS_DATA_PATH
    )
    assert (
        widget.getMetadataPathSelection().getExample() == "/1.1/instrument/positioners"
    )


def test_HDF5EntriesWidget(qtapp):  # noqa F811
    """
    test of the HDF5EntriesWidget widget

    common test on selection / unselection of items
    """
    widget = HDF5EntriesWidget()
    n_scan = 5
    widget.setEntries([f"{i+1}.1" for i in range(n_scan)])
    assert len(widget.getEntries()) == n_scan
    assert len(widget.getSelectedEntries()) == n_scan

    widget.setSelectedEntries(("1.1", "2.1"))
    assert widget.getSelectedEntries() == ("1.1", "2.1")

    widget.selectAll()
    assert widget.getSelectedEntries() == tuple([f"{i+1}.1" for i in range(n_scan)])

    widget.unselectAll()
    assert widget.getSelectedEntries() == ()
