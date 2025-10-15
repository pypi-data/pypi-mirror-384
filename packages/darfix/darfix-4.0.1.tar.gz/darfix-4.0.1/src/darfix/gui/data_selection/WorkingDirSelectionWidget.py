import logging

from silx.gui import qt

from ..utils.utils import create_completer

_logger = logging.getLogger(__name__)


class WorkingDirSelectionWidget(qt.QWidget):
    """
    Widget used to obtain a directory name
    """

    dirChanged = qt.Signal()

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)

        self._dir = qt.QLineEdit("", parent=self)
        self._dir.editingFinished.connect(self.dirChanged)
        self.completer = create_completer()
        self._dir.setCompleter(self.completer)

        self._addButton = qt.QPushButton("Select working directory", parent=self)
        self._addButton.pressed.connect(self._selectWorkingDirectory)
        self.setLayout(qt.QHBoxLayout())

        self.layout().addWidget(self._dir)
        self.layout().addWidget(self._addButton)

    def _selectWorkingDirectory(self):
        """
        Select a folder to be used as working directory (task results will be saved at this location)
        """
        fileDialog = qt.QFileDialog()
        fileDialog.setOption(qt.QFileDialog.ShowDirsOnly)
        fileDialog.setFileMode(qt.QFileDialog.Directory)
        if fileDialog.exec():
            self._dir.setText(fileDialog.directory().absolutePath())
            self.dirChanged.emit()
        else:
            _logger.warning("Could not open directory")

    def getDir(self):
        return str(self._dir.text())

    def setDir(self, _dir):
        self._dir.setText(str(_dir))
        self.dirChanged.emit()
