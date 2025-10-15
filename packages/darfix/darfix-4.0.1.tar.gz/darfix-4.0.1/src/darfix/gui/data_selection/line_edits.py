from __future__ import annotations

from silx.gui import qt
from silx.gui.dialog.DatasetDialog import DatasetDialog
from silx.gui.dialog.GroupDialog import GroupDialog


class _BaseLineEdit(qt.QWidget):
    """
    A line edit for paths that can filled via a selection dialog.

    The dialog creation and result must be implemented in `_getDialogResult`
    """

    dialogSelected = qt.Signal(str)
    editingFinished = qt.Signal()

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent, **kwargs)

        self._lineEdit = qt.QLineEdit()
        browseButton = qt.QPushButton("Browse...")

        layout = qt.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._lineEdit)
        layout.addWidget(browseButton)

        browseButton.clicked.connect(self._openDialog)
        self._lineEdit.editingFinished.connect(self.editingFinished)

    def _getDialogResult(self) -> str | None:
        raise NotImplementedError()

    def _openDialog(self):
        result = self._getDialogResult()
        if not result:
            return

        self._lineEdit.setText(result)
        self.dialogSelected.emit(result)

    def setText(self, text: str):
        self._lineEdit.setText(text)

    def getText(self) -> str:
        return self._lineEdit.text()


class FileLineEdit(_BaseLineEdit):
    """A line edit for file paths that can filled via a file selection dialog"""

    dialogSelected = qt.Signal(str)
    editingFinished = qt.Signal()

    def _getDialogResult(self) -> None | str:
        dialog = qt.QFileDialog()
        result = dialog.exec()

        if not result:
            return None
        return dialog.selectedFiles()[0]


class DatasetLineEdit(_BaseLineEdit):
    """
    A line edit for an HDF5 dataset path that can filled via a dataset selection dialog.
    The file needs to be set beforehand with `setFile`
    """

    dialogSelected = qt.Signal(str)
    editingFinished = qt.Signal()

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._file = None

    def setFile(self, file: str):
        self._file = file

    def _getDialogResult(self) -> None | str:
        dialog = DatasetDialog()
        if self._file is None:
            return None

        dialog.addFile(self._file)
        result = dialog.exec()
        if not result:
            return None

        url = dialog.getSelectedDataUrl()
        return url.data_path() if url else None


class GroupLineEdit(_BaseLineEdit):
    """
    A line edit for an HDF5 group path that can filled via a group selection dialog.
    The file needs to be set beforehand with `setFile`
    """

    dialogSelected = qt.Signal(str)
    editingFinished = qt.Signal()

    def __init__(self, parent: qt.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._file = None

    def setFile(self, file: str):
        self._file = file

    def _getDialogResult(self) -> None | str:
        dialog = GroupDialog()
        if self._file is None:
            return None

        dialog.addFile(self._file)
        result = dialog.exec()
        if not result:
            return None

        url = dialog.getSelectedDataUrl()
        return url.data_path() if url else None
