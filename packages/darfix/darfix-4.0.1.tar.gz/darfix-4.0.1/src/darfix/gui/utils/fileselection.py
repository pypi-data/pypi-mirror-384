from __future__ import annotations

from silx.gui import qt

from .utils import create_completer


class FileSelector(qt.QWidget):
    """Widget to select a file"""

    sigFileChanged = qt.Signal()

    def __init__(
        self,
        parent: qt.QWidget | None = None,
        label: str = "file:",
        filters=None,
    ) -> None:
        super().__init__(parent)
        self._dialogFileMode = qt.QFileDialog.AnyFile
        self._dialogNameFilters = None  # ["HDF5 file *.h5 *.hdf5 *.nx *.nexus", "nxs"]

        self.setLayout(qt.QHBoxLayout())

        # label
        self._label = qt.QLabel(text=label)
        self.layout().addWidget(self._label)

        # file path QLE and completer
        self._filePath = qt.QLineEdit("")
        self.layout().addWidget(self._filePath)
        self.completer = create_completer(filters)
        self._filePath.setCompleter(self.completer)

        # select button
        self._select = qt.QPushButton("select")
        self.layout().addWidget(self._select)

        # connect signal / slot
        self._select.released.connect(self._selectFile)
        self._filePath.editingFinished.connect(self.sigFileChanged)

    def setDialogFileMode(self, mode: qt.Qt.FileDialog):
        self._dialogFileMode = mode

    def setDialogNameFilters(self, name_filters: tuple | None):
        self._dialogNameFilters = name_filters

    def _selectFile(self):
        dialog = qt.QFileDialog(self)
        dialog.setFileMode(self._dialogFileMode)
        if self._dialogNameFilters is not None:
            dialog.setNameFilters(self._dialogNameFilters)

        if not dialog.exec():
            return

        if len(dialog.selectedFiles()) > 0:
            self.setFilePath(dialog.selectedFiles()[0])

    def getFilePath(self) -> None | str:
        file_path = self._filePath.text()
        if file_path.replace(" ", "") != "":
            return file_path
        else:
            return None

    def setFilePath(self, file_path: None | str) -> None:
        if file_path is None:
            self._filePath.clear()
        else:
            self._filePath.setText(file_path)
        self.sigFileChanged.emit()
