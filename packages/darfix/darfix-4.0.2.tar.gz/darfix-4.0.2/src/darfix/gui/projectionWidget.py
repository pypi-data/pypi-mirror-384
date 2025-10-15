from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot.StackView import StackViewMainWindow

from .. import config
from ..dtypes import ImageDataset
from .chooseDimensions import ChooseDimensionWidget


class ProjectionWidget(qt.QWidget):
    """
    Widget to apply a projection to the chosen dimension.
    """

    sigOkClicked = qt.Signal()
    sigProjectButtonClicked = qt.Signal()
    sigDimensionsChanged = qt.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._sv = StackViewMainWindow()
        self._sv.setColormap(
            Colormap(name=config.DEFAULT_COLORMAP_NAME, normalization="linear")
        )
        self._sv.setKeepDataAspectRatio(True)
        self._chooseDimensionWidget = ChooseDimensionWidget(
            self, vertical=False, values=False, _filter=False
        )
        self._projectButton = qt.QPushButton("Project data")
        self._projectButton.setEnabled(False)
        types = qt.QDialogButtonBox.Ok
        self._buttons = qt.QDialogButtonBox(parent=self)
        self._buttons.setStandardButtons(types)
        self._buttons.setEnabled(False)
        layout = qt.QGridLayout()
        layout.addWidget(self._chooseDimensionWidget, 0, 0, 1, 2)
        layout.addWidget(self._projectButton, 1, 1)
        layout.addWidget(self._sv, 2, 0, 1, 2)
        layout.addWidget(self._buttons, 3, 1)
        self.setLayout(layout)

        self._projectButton.clicked.connect(self.sigProjectButtonClicked.emit)
        self._buttons.accepted.connect(self.sigOkClicked.emit)
        self._chooseDimensionWidget.valueChanged.connect(self.sigDimensionsChanged.emit)

    def setDataset(self, dataset: ImageDataset):
        if not dataset.dims:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setText(
                "This widget has to be used after selecting the dimensions of the dataset. Run the `Dimension definition` widget first."
            )
            msg.exec()
            return

        self._projectButton.setEnabled(True)
        if dataset.dims.ndim > 1:
            self._buttons.setEnabled(True)

        self._chooseDimensionWidget.setDimensions(dataset.dims)
        self._chooseDimensionWidget._updateState(True)
        for i in range(1, dataset.dims.ndim - 1):
            self._chooseDimensionWidget.dimensionWidgets[i][0].addItem("None")
        self._sv.setKeepDataAspectRatio(True)
        self._sv.setGraphTitle(dataset.title)

    def getDimension(self):
        dimension = [self._chooseDimensionWidget.dimension[0]]
        for i in range(1, len(self._chooseDimensionWidget.dimension)):
            dimension += [self._chooseDimensionWidget.dimension[i]]

        return dimension

    def updatePlot(self, dataset: ImageDataset):
        self._projectButton.setEnabled(True)
        self._sv.setStack(dataset.as_array3d())
