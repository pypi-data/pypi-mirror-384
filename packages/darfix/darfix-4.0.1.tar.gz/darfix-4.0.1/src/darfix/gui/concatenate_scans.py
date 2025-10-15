from __future__ import annotations

import logging
import os

import h5py
from ewoksorange.gui.parameterform import block_signals
from silx.gui import qt

from darfix.core.datapathfinder import DETECTOR_KEYWORD
from darfix.core.datapathfinder import SCAN_KEYWORD
from darfix.gui.configuration.action import AdvancedConfigurationAction
from darfix.gui.configuration.action import RequiredConfigurationAction
from darfix.gui.configuration.level import ConfigurationLevel
from darfix.gui.data_selection.hdf5_data_selection_widgets import (
    HDF5DatasetSelectionWidget,
)
from darfix.gui.utils.fileselection import FileSelector
from darfix.tasks.hdf5_scans_concatenation import ConcatenateHDF5Scans
from darfix.tasks.hdf5_scans_concatenation import guess_output_file

_logger = logging.getLogger(__name__)


class HDF5ConcatenateWindow(qt.QMainWindow):
    """Main window giving access to the different options to concatenate HDF5 scans"""

    def __init__(self, parent: qt.QWidget | None = None) -> None:
        super().__init__(parent)

        # define toolbar
        toolbar = qt.QToolBar(self)
        self.addToolBar(qt.Qt.TopToolBarArea, toolbar)

        self.__configurationModesAction = qt.QAction(self)
        self.__configurationModesAction.setCheckable(False)
        menu = qt.QMenu(self)
        self.__configurationModesAction.setMenu(menu)
        toolbar.addAction(self.__configurationModesAction)

        self.__configurationModesGroup = qt.QActionGroup(self)
        self.__configurationModesGroup.setExclusive(True)
        self.__configurationModesGroup.triggered.connect(self._userModeChanged)

        self._requiredConfigAction = RequiredConfigurationAction(toolbar)
        menu.addAction(self._requiredConfigAction)
        self.__configurationModesGroup.addAction(self._requiredConfigAction)
        self._advancedConfigAction = AdvancedConfigurationAction(toolbar)
        menu.addAction(self._advancedConfigAction)
        self.__configurationModesGroup.addAction(self._advancedConfigAction)

        # define main widget
        self._mainWidget = ConcatenateScansWidget(self)
        self.setCentralWidget(self._mainWidget)

        self._advancedConfigAction.setChecked(True)
        self._userModeChanged(self._advancedConfigAction)

    def getConcatenateScansWidget(self):
        return self._mainWidget

    def _userModeChanged(self, action):
        self.__configurationModesAction.setIcon(action.icon())
        self.__configurationModesAction.setToolTip(action.tooltip())
        if action is self._requiredConfigAction:
            level = ConfigurationLevel.REQUIRED
        elif action is self._advancedConfigAction:
            level = ConfigurationLevel.ADVANCED
        else:
            raise NotImplementedError
        self.setConfigurationLevel(level=level)

    # expose API
    def setConfigurationLevel(self, level: ConfigurationLevel | str):
        self._mainWidget.setConfigurationLevel(level)


class ConcatenateScansWidget(HDF5DatasetSelectionWidget):
    """
    Widget to concatenate a series of scans together.
    Same API as the HDF5DatasetSelectionWidget but adds an instance of HDF5EntriesWidget
    """

    AVAILABLE_KEYWORDS = (
        DETECTOR_KEYWORD,
        SCAN_KEYWORD,
    )

    sigOutputFileChanged = qt.Signal(str)
    sigOverwriteChanged = qt.Signal(bool)
    sigAutoUpdateOutputFile = qt.Signal(bool)
    sigDetectorPathChanged = qt.Signal(str)
    sigMetadataPathChanged = qt.Signal(str)
    sigEntriesToConcatenateChanged = qt.Signal()

    def __init__(
        self,
        parent: qt.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        # update layout for the exising widget from HDF5DatasetSelectionWidget
        self.layout().addWidget(self._inputFileSelector, 0, 0, 1, 5)
        self.layout().addWidget(self._detectorDataPath, 4, 0, 1, 5)
        self.layout().addWidget(self._positionerDataPath, 5, 0, 1, 5)

        # scan list
        self._scanEntries = HDF5EntriesWidget()
        self._scanEntries.setSizePolicy(
            qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding
        )
        self.layout().addWidget(self._scanEntries, 1, 0, 2, 5)

        # output file selector
        self._outputFileSelector = FileSelector(label="output file:")
        self._outputFileSelector.setDialogFileMode(qt.QFileDialog.AnyFile)
        self._outputFileSelector.setDialogNameFilters(
            ("HDF5 files (*.h5 *.hdf5 *.nx *.nxs *.nexus)",)
        )
        # overwrite output
        self.layout().addWidget(self._outputFileSelector, 6, 0, 1, 3)
        self._overwriteOutput = qt.QCheckBox("overwrite")
        self._overwriteOutput.setSizePolicy(qt.QSizePolicy.Fixed, qt.QSizePolicy.Fixed)

        self.layout().addWidget(self._overwriteOutput, 6, 3, 1, 1)

        # auto update
        self._autoUpdate = qt.QCheckBox("auto update")
        self._autoUpdate.setSizePolicy(qt.QSizePolicy.Fixed, qt.QSizePolicy.Fixed)
        self.layout().addWidget(self._autoUpdate, 6, 4, 1, 1)
        self._autoUpdate.setToolTip(
            "update advanced option automatically when input file changed"
        )

        # set up
        self._overwriteOutput.setChecked(True)
        self._autoUpdate.setChecked(True)
        self._detectorDataPath.setPattern(
            ConcatenateHDF5Scans.DEFAULT_DETECTOR_DATA_PATH,
            store_as_default=True,
        )
        self._detectorDataPath.setAvailableKeywords(
            self.AVAILABLE_KEYWORDS,
        )
        self._positionerDataPath.setPattern(
            ConcatenateHDF5Scans.DEFAULT_POSITIONERS_DATA_PATH,
            store_as_default=True,
        )
        self._positionerDataPath.setAvailableKeywords(
            self.AVAILABLE_KEYWORDS,
        )

        # connect signal / slot
        self._outputFileSelector.sigFileChanged.connect(self._outputFileChanged)
        self._positionerDataPath.sigPatternChanged.connect(self.sigMetadataPathChanged)
        self._detectorDataPath.sigPatternChanged.connect(self.sigDetectorPathChanged)
        self._scanEntries.sigSelectedChanged.connect(
            self.sigEntriesToConcatenateChanged
        )

    def _outputFileChanged(self):
        self.sigOutputFileChanged.emit(self._outputFileSelector.getFilePath())

    def _inputFileChanged(self):
        input_file = self.getInputFile()
        if input_file is not None and not os.path.exists(input_file):
            _logger.debug(f"{input_file} doesn't exist")
        else:
            self._updateEntries()
            if self._autoUpdate.isChecked():
                self._deduceOutputFile()
        super()._inputFileChanged()

    # expose API
    def getSelectedEntries(self):
        return self._scanEntries.getSelectedEntries()

    def setSelectedEntries(self, entries: tuple):
        self._scanEntries.setSelectedEntries(entries=entries)

    def _updateEntries(self):
        input_file = self.getInputFile()
        if input_file is None:
            entries = ()
        else:
            with h5py.File(input_file, mode="r") as h5f:
                valid_items = filter(
                    lambda a: isinstance(a, h5py.Group),
                    [h5f.get(item) for item in h5f],
                )
                entries = [item.name for item in valid_items]
        self._scanEntries.setEntries(entries)

    def _deduceOutputFile(self, target_processed_data_dir: bool = True):
        input_file = self.getInputFile()
        if input_file is None:
            return
        if not h5py.is_hdf5(input_file):
            _logger.error("unable to deduce output file. Input is not an HDF5 file")
            return
        output_file = guess_output_file(
            input_file=input_file, target_processed_data_dir=target_processed_data_dir
        )
        self.setOutputFile(output_file)

    def setOutputFile(self, file_path: str):
        self._outputFileSelector.setFilePath(file_path=file_path)
        self.sigOutputFileChanged.emit(file_path)

    def getOutputFile(self) -> str | None:
        return self._outputFileSelector.getFilePath()

    def setOverwrite(self, overwrite: bool):
        self._overwriteOutput.setChecked(overwrite)

    def getOverwrite(self) -> bool:
        return self._overwriteOutput.isChecked()

    def setDetectorPath(self, detector_path: str):
        self._detectorDataPath.setPattern(detector_path)

    def setPositionersGroupPath(self, positioners_group_path: str):
        self._positionerDataPath.setPattern(positioners_group_path)

    def setConfigurationLevel(self, level: ConfigurationLevel | str):
        level = ConfigurationLevel.from_value(level)
        self._positionerDataPath.setVisible(level > ConfigurationLevel.REQUIRED)
        self._detectorDataPath.setVisible(level > ConfigurationLevel.REQUIRED)
        self._outputFileSelector.setVisible(level > ConfigurationLevel.REQUIRED)
        self._overwriteOutput.setVisible(level > ConfigurationLevel.REQUIRED)
        self._autoUpdate.setVisible(level > ConfigurationLevel.REQUIRED)


class HDF5EntriesWidget(qt.QDialog):
    """Dialog to select the entries to use"""

    sigSelectedChanged = qt.Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setLayout(qt.QVBoxLayout())

        # list widget
        self._listWidget = qt.QListWidget()
        self.layout().addWidget(self._listWidget)

        types = qt.QDialogButtonBox.YesToAll | qt.QDialogButtonBox.NoToAll
        self._buttons = qt.QDialogButtonBox(parent=self)
        self._buttons.setStandardButtons(types)
        self.layout().addWidget(self._buttons)

        selectAllButton = self._buttons.button(qt.QDialogButtonBox.YesToAll)
        selectAllButton.setText("select all")
        selectAllButton.released.connect(self.selectAll)

        unselectAllButton = self._buttons.button(qt.QDialogButtonBox.NoToAll)
        unselectAllButton.setText("unselect all")
        unselectAllButton.released.connect(self.unselectAll)

    def setEntries(self, entries: tuple[str]):
        """clear existing list, set provided entries and select them"""
        self._listWidget.clear()
        for entry in entries:
            item = qt.QListWidgetItem(parent=self._listWidget)
            checkbox = qt.QCheckBox(entry, parent=self._listWidget)
            checkbox.setChecked(True)
            item.setData(qt.Qt.UserRole, entry)
            self._listWidget.setItemWidget(item, checkbox)
            # connect signal / slot
            checkbox.toggled.connect(self.sigSelectedChanged)

    def _getEntriesItems(self) -> tuple[qt.QListWidgetItem]:
        return [
            self._listWidget.item(i_item) for i_item in range(self._listWidget.count())
        ]

    def getEntries(self) -> tuple[str]:
        return tuple([item.data(qt.Qt.UserRole) for item in self._getEntriesItems()])

    def selectAll(self):
        self.setSelectedEntries(self.getEntries())

    def unselectAll(self):
        self.setSelectedEntries(())

    def getSelectedEntries(self) -> tuple[str]:
        filtered_items = filter(
            lambda a: self._listWidget.itemWidget(a).isChecked(),
            self._getEntriesItems(),
        )
        return tuple([item.data(qt.Qt.UserRole) for item in filtered_items])

    def setSelectedEntries(self, entries: tuple[str]):
        entries = [self._clean_entry_name(entry) for entry in entries]

        with block_signals(self):
            # send sigSelectedChanged once only
            for item in self._getEntriesItems():
                itemWidget = self._listWidget.itemWidget(item)
                checked = self._clean_entry_name(item.data(qt.Qt.UserRole)) in entries
                itemWidget.setChecked(checked)
        self.sigSelectedChanged.emit()

    @staticmethod
    def _clean_entry_name(entry):
        """clean entry names regarding the name use either 1.1 or /1.1"""
        return entry.lstrip("/")
