from __future__ import annotations

from silx.gui import qt

from .WorkingDirSelectionWidget import WorkingDirSelectionWidget


class DataSelectionBase(qt.QTabWidget):
    """Define the base class to define the data selection"""

    sigRawDataInfosChanged = qt.Signal()
    sigDarkDataInfosChanged = qt.Signal()
    sigTreatedDirInfoChanged = qt.Signal()

    def __init__(self, parent: qt.QWidget | None = None) -> None:
        super().__init__(parent)

        self._dataset = None
        self.bg_dataset = None
        self.indices = None
        self.bg_indices = None

        self._rawDataWidget = self.buildRawDataWidget()
        self.addTab(self._rawDataWidget, "raw data")

        self._darkDataWidget = self.buildDarkDataWidget()
        self.addTab(self._darkDataWidget, "dark data")

        self._treatedDirWidget = self.buildProcessedDataWidget()
        self.addTab(self._treatedDirWidget, "treated data")

        # connect signal / slot
        self._treatedDirData.dirChanged.connect(self.sigTreatedDirInfoChanged)

    def getTreatedDir(self) -> str:
        return self._treatedDirData.getDir()

    def setTreatedDir(self, _dir):
        self._treatedDirData.setDir(_dir)

    def buildProcessedDataWidget(self):
        widget = qt.QWidget()
        widget.setLayout(qt.QVBoxLayout())
        self._treatedDirData = WorkingDirSelectionWidget(parent=self)
        widget.layout().addWidget(self._treatedDirData)
        spacer = qt.QWidget()
        spacer.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        widget.layout().addWidget(spacer)
        return widget

    # Base class API to be redefined
    def buildRawDataWidget(self):
        raise NotImplementedError("Base class")

    def buildDarkDataWidget(self):
        raise NotImplementedError("Base class")

    def keepDataOnDisk(self) -> bool:
        raise NotImplementedError("Base class")
