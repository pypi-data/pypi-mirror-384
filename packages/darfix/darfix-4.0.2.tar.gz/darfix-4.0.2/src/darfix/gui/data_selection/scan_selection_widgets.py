from __future__ import annotations

import logging
import os

import silx.io
from ewoksorange.gui.qtsignals import block_signals
from silx.gui import qt

from darfix.gui.data_selection.utils import find_detector_name
from darfix.gui.data_selection.utils import find_scan_names
from darfix.gui.utils.message import show_error_msg

from .line_edits import DatasetLineEdit
from .line_edits import FileLineEdit
from .line_edits import GroupLineEdit

_logger = logging.getLogger(__file__)


class ScanSelectionWidget(qt.QWidget):
    """
    Widget to select a scan (file + scan_number) and a detector in the scan.

    Autofills the detector path when the scan is updated.
    """

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent=parent, **kwargs)

        self._fileLineEdit = FileLineEdit()
        self._scanNameComboBox = qt.QComboBox()
        self._detectorLineEdit = DatasetLineEdit()

        layout = qt.QFormLayout(self)

        layout.addRow("File selection", self._fileLineEdit)
        layout.addRow("Scan number", self._scanNameComboBox)
        layout.addRow("Detector", self._detectorLineEdit)

        self._scanNameComboBox.currentTextChanged.connect(self._updateDetectorPath)
        self._fileLineEdit.editingFinished.connect(self._onNewFileEdit)
        self._fileLineEdit.dialogSelected.connect(self._onNewFile)

    def _onNewFileEdit(self):
        path = self._fileLineEdit.getText()
        if os.path.exists(path):
            self._onNewFile(path)
        else:
            show_error_msg(f"File '{path}' does not exist")

    def _onNewFile(self, filePath: str):
        self._detectorLineEdit.setFile(filePath)

        try:
            scanNames = find_scan_names(filePath)
        except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
            _logger.warning(f"Could not find scan names in {filePath}. Reason: {e}")
            scanNames = tuple()

        with block_signals(self._scanNameComboBox):
            self._scanNameComboBox.clear()
        self._scanNameComboBox.addItems(scanNames)

    def _updateDetectorPath(self, scanNumber: str):
        scanUrl = f"{self._fileLineEdit.getText()}::/{scanNumber}"
        with silx.io.open(scanUrl) as scan:
            detectorName = find_detector_name(scan)

        if detectorName:
            self._detectorLineEdit.setText(f"/{scanNumber}/measurement/{detectorName}")

    def setFilePath(self, file: str):
        self._fileLineEdit.setText(file)
        self._onNewFile(file)

    def getFilePath(self) -> str:
        return self._fileLineEdit.getText()

    def setDetectorPath(self, path: str):
        self._detectorLineEdit.setText(path)
        scanNumber = path.lstrip("/").split("/")[0]
        with block_signals(self._scanNameComboBox):
            self._scanNameComboBox.setCurrentText(scanNumber)

    def getDetectorPath(self) -> str:
        return self._detectorLineEdit.getText()


class ScanSelectionWidgetWithPositioners(ScanSelectionWidget):
    """
    Adds an autofillable positioner path to ScanSelectionWidget
    """

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        layout = self.layout()
        assert isinstance(layout, qt.QFormLayout)

        self._positionersLineEdit = GroupLineEdit()
        layout.addRow("Positioners", self._positionersLineEdit)

        self._scanNameComboBox.currentTextChanged.connect(self._updatePositionersPath)

    def _onNewFile(self, file_path: str):
        super()._onNewFile(file_path)
        self._positionersLineEdit.setFile(file_path)

    def _updatePositionersPath(self, scan_number: str):
        self._positionersLineEdit.setText(f"/{scan_number}/instrument/positioners")

    def setPositionersPath(self, data_url: str):
        self._positionersLineEdit.setText(data_url)

    def getPositionersPath(self) -> str:
        return self._positionersLineEdit.getText()
