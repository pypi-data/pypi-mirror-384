from __future__ import annotations

from functools import partial
from typing import Any

from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread
from silx.gui import qt

from darfix.gui.data_selection.scan_selection_widgets import ScanSelectionWidget
from darfix.gui.data_selection.scan_selection_widgets import (
    ScanSelectionWidgetWithPositioners,
)
from darfix.gui.utils.message import show_error_msg
from darfix.tasks.hdf5_data_selection import HDF5DataSelection


class HDF5DataSelectionWidgetOW(
    OWEwoksWidgetOneThread,
    ewokstaskclass=HDF5DataSelection,
):
    """
    Widget to select dataset stored as HDF5
    """

    name = "HDF5 data selection"
    icon = "icons/upload_hdf5.svg"
    want_main_area = True
    want_control_area = False

    priority = 1

    _ewoks_inputs_to_hide_from_orange = (
        "raw_detector_data_path",
        "raw_metadata_path",
        "dark_detector_data_path",
        "workflow_title",
        "treated_data_dir",
    )

    def __init__(self):
        super().__init__()

        layout = self.mainArea.layout()
        rawDataGroup = qt.QGroupBox(title="Raw data")
        rawDataLayout = qt.QVBoxLayout(rawDataGroup)
        formLayout = qt.QFormLayout()
        self._rawDataSelection = ScanSelectionWidgetWithPositioners()

        rawDataLayout.addWidget(self._rawDataSelection)
        rawDataLayout.addLayout(formLayout)
        layout.addWidget(rawDataGroup)

        self._darkDataGroup = qt.QGroupBox(title="Dark data")
        self._darkDataGroup.setCheckable(True)
        self._darkDataGroup.setChecked(False)
        darkDataLayout = qt.QVBoxLayout(self._darkDataGroup)
        self._darkDataSelection = ScanSelectionWidget()
        darkDataLayout.addWidget(self._darkDataSelection)
        layout.addWidget(self._darkDataGroup)

        workingDirLayout = qt.QFormLayout()
        self._workingDirLineEdit = qt.QLineEdit()
        workingDirLayout.addRow("Working directory", self._workingDirLineEdit)
        self._workflowTitleLineEdit = qt.QLineEdit()
        workingDirLayout.addRow("Workflow title", self._workflowTitleLineEdit)
        layout.addLayout(workingDirLayout)

        types = qt.QDialogButtonBox.Ok
        _buttons = qt.QDialogButtonBox(parent=self)
        _buttons.setStandardButtons(types)
        self.mainArea.layout().addWidget(_buttons)

        _buttons.accepted.connect(self._executeTask)

        # set up
        self._loadInputs(self.get_task_input_values())

        # connect signal / slot
        self.task_executor.finished.connect(
            self.information,
        )
        self.task_executor.finished.connect(lambda: self.mainArea.setEnabled(True))
        self.task_executor.started.connect(
            partial(self.information, "Downloading dataset. This can take a while...")
        )
        self.task_executor.started.connect(lambda: self.mainArea.setDisabled(True))

    def task_output_changed(self) -> None:
        if self.task_succeeded:
            self.accept()
        else:
            show_error_msg(f"Selection failed with error : \n{self.task_exception}")

        return super().task_output_changed()

    def _loadInputs(self, taskInputValues: dict[str, Any]):
        rawInputFile = taskInputValues.get("raw_input_file")
        if rawInputFile:
            self._rawDataSelection.setFilePath(rawInputFile)

        rawDetectorDataPath = taskInputValues.get("raw_detector_data_path")
        if rawDetectorDataPath:
            self._rawDataSelection.setDetectorPath(rawDetectorDataPath)

        rawMetadataPath = taskInputValues.get("raw_metadata_path")
        if rawMetadataPath:
            self._rawDataSelection.setPositionersPath(rawMetadataPath)

        darkInputFile = taskInputValues.get("dark_input_file")
        if darkInputFile:
            self._darkDataSelection.setFilePath(darkInputFile)
            self._darkDataGroup.setChecked(True)

        darkDetectorDataPath = taskInputValues.get("dark_detector_data_path")
        if darkDetectorDataPath:
            self._darkDataSelection.setDetectorPath(darkDetectorDataPath)
            self._darkDataGroup.setChecked(True)

        treatedDataDir = taskInputValues.get("treated_data_dir")
        if treatedDataDir is not None:
            self._workingDirLineEdit.setText(treatedDataDir)

        workflowTitle = taskInputValues.get("workflow_title")
        if workflowTitle is not None:
            self._workflowTitleLineEdit.setText(workflowTitle)

    def getInputs(self) -> dict[str, Any]:
        inputs = {
            "raw_input_file": self._rawDataSelection.getFilePath(),
            "raw_detector_data_path": self._rawDataSelection.getDetectorPath(),
            "raw_metadata_path": self._rawDataSelection.getPositionersPath(),
        }

        if self._darkDataGroup.isChecked():
            inputs = {
                **inputs,
                "dark_input_file": self._darkDataSelection.getFilePath(),
                "dark_detector_data_path": self._darkDataSelection.getDetectorPath(),
            }

        if self._workingDirLineEdit.text():
            inputs = {
                **inputs,
                "treated_data_dir": self._workingDirLineEdit.text(),
            }

        if self._workflowTitleLineEdit.text():
            inputs = {
                **inputs,
                "workflow_title": self._workflowTitleLineEdit.text(),
            }

        return inputs

    def handleNewSignals(self) -> None:
        # update the input file in case they are provided by another widget (like the hdf5 scan concatenation)
        self._loadInputs(self.get_task_input_values())

    def saveInputs(self):
        for key, value in self.getInputs().items():
            self.set_default_input(key, value)

    def _executeTask(self):
        self.saveInputs()
        self.execute_ewoks_task()

    def closeEvent(self, *a, **kw):
        self.saveInputs()
        super().closeEvent(*a, **kw)
