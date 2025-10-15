from __future__ import annotations

from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot.StackView import StackViewMainWindow

import darfix

from ..dtypes import Dataset
from .filterByDimension import FilterByDimensionWidget


class ZSumWidget(qt.QMainWindow):
    sigAxisChanged = qt.Signal(int)
    sigResetFiltering = qt.Signal()

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)

        self._sv = StackViewMainWindow()
        self._sv.setColormap(
            Colormap(
                name=darfix.config.DEFAULT_COLORMAP_NAME,
                normalization=darfix.config.DEFAULT_COLORMAP_NORM,
            )
        )
        self._sv.setKeepDataAspectRatio(True)

        self._selector = FilterByDimensionWidget()

        self._selector.axisChanged.connect(self.sigAxisChanged)
        self._selector.stateDisabled.connect(self.sigResetFiltering)

        self.setCentralWidget(self._sv)
        toolbar = qt.QToolBar()
        toolbar.addWidget(self._selector)
        self.addToolBar(qt.Qt.ToolBarArea.BottomToolBarArea, toolbar)

    def setDataset(self, dataset: Dataset):
        self.dataset = dataset.dataset
        self.indices = dataset.indices
        self._selector.setDimensions(self.dataset.dims)
        self._sv.setGraphTitle(self.dataset.title)

    def setZSum(self, zsum):
        self._sv.setStack(zsum)
