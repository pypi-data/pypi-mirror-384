from functools import partial

from ewokscore.missing_data import is_missing_data
from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread
from silx.gui import qt

from darfix.gui.concatenate_scans import HDF5ConcatenateWindow
from darfix.gui.configuration.level import ConfigurationLevel
from darfix.tasks.hdf5_scans_concatenation import ConcatenateHDF5Scans


class ConcatenateWidgetOW(OWEwoksWidgetOneThread, ewokstaskclass=ConcatenateHDF5Scans):
    """
    Widget that concatenates a set of scans.

    Note: 'output_detector_data_path' and 'output_positioners_data_path' are never set by the GUI.
    It simplifies usage. We 'force' users to use the default one.
    """

    name = "HDF5 scans concatenation"
    icon = "icons/concatenate_hdf5.svg"
    want_main_area = True
    want_control_area = False

    _ewoks_inputs_to_hide_from_orange = (
        "input_file",
        "output_file",
        "entries_to_concatenate",
        "detector_data_path",
        "positioners_group_path",
        "output_detector_data_path",
        "output_positioners_data_path",
        "overwrite",
        "guess_output_file",
    )

    def __init__(self):
        super().__init__()
        self._widget = HDF5ConcatenateWindow(parent=self)
        self.mainArea.layout().addWidget(self._widget)

        types = qt.QDialogButtonBox.Ok
        self._buttons = qt.QDialogButtonBox(parent=self)
        self._buttons.setStandardButtons(types)
        self.mainArea.layout().addWidget(self._buttons)

        # load settings
        self._loadSettings()

        # connect signal / slot
        concatenateWidget = self._widget._mainWidget
        self._buttons.button(qt.QDialogButtonBox.Ok).released.connect(self.validate)
        concatenateWidget.sigInputFileChanged.connect(self._inputFileChanged)
        concatenateWidget.sigOutputFileChanged.connect(self._outputFileChanged)
        concatenateWidget.sigOverwriteChanged.connect(self._overwriteOutputChanged)
        concatenateWidget.sigDetectorPathChanged.connect(self._detectorPathChanged)
        concatenateWidget.sigMetadataPathChanged.connect(self._metadataPathChanged)
        concatenateWidget.sigEntriesToConcatenateChanged.connect(
            self._entriesToConcatenateChanged
        )
        concatenateWidget._autoUpdate.toggled.connect(self._autoUpdateChanged)

        self.task_executor.finished.connect(
            self.information,
        )
        self.task_executor.started.connect(
            partial(self.information, "Concatenating scans...")
        )

    def _loadSettings(self):
        upgrade_settings_mode = False
        concatenateWidget = self._widget._mainWidget
        input_file = self.get_task_input_value("input_file")
        if not is_missing_data(input_file):
            concatenateWidget.setInputFile(input_file)
            # if the file is not set, skip settings entries. There will be None but that is fine
            entries_to_concatenate = self.get_task_input_value("entries_to_concatenate")
            if not is_missing_data(entries_to_concatenate):
                concatenateWidget.setSelectedEntries(entries=entries_to_concatenate)

        output_file = self.get_task_input_value("output_file")
        if not is_missing_data(output_file):
            concatenateWidget.setOutputFile(output_file)

        overwrite = self.get_task_input_value("overwrite")
        if not is_missing_data(overwrite):
            concatenateWidget.setOverwrite(overwrite)
        else:
            # update overwrite value because the value from the gui is different from the task one
            self._overwriteOutputChanged(overwrite=concatenateWidget.getOverwrite())

        detector_data_path = self.get_task_input_value("detector_data_path")
        if not is_missing_data(detector_data_path):
            concatenateWidget.setDetectorPath(detector_data_path)
        else:
            # make sure the pattern is registered
            self._detectorPathChanged(concatenateWidget._detectorDataPath.getPattern())

        positioners_group_path = self.get_task_input_value("positioners_group_path")
        if not is_missing_data(positioners_group_path):
            concatenateWidget.setPositionersGroupPath(positioners_group_path)
        else:
            # make sure the pattern is registered
            self._metadataPathChanged(
                concatenateWidget._positionerDataPath.getPattern()
            )

        guess_output_file = self.get_task_input_value("guess_output_file")
        if not is_missing_data(guess_output_file):
            concatenateWidget._autoUpdate.setChecked(guess_output_file)
            if not guess_output_file:
                upgrade_settings_mode = True

        if upgrade_settings_mode:
            # if an advanced option has been set, display all the settings
            concatenateWidget.setConfigurationLevel(ConfigurationLevel.ADVANCED)

    def validate(self):
        self.execute_ewoks_task()
        self.accept()

    def handleNewSignals(self) -> None:
        pass
        # Do not call super().handleNewSignals() to make sure the processing is not triggered

    # ewoks input setter
    def _inputFileChanged(self, file_path: str):
        self.set_default_input("input_file", file_path)

    def _outputFileChanged(self, file_path: str):
        self.set_default_input("output_file", file_path)

    def _overwriteOutputChanged(self, overwrite: bool):
        self.set_default_input("overwrite", overwrite)

    def _detectorPathChanged(self, data_path: str):
        self.set_default_input("detector_data_path", data_path)

    def _metadataPathChanged(self, data_path: str):
        self.set_default_input("positioners_group_path", data_path)

    def _entriesToConcatenateChanged(self):
        self.set_default_input(
            "entries_to_concatenate", self._widget._mainWidget.getSelectedEntries()
        )

    def _autoUpdateChanged(self, activated: bool):
        self.set_default_input("guess_output_file", activated)
