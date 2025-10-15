from __future__ import annotations

import numpy
from silx.gui import qt
from silx.gui.plot import Plot1D

from darfix import dtypes

from .operationThread import OperationThread


class PCAPlot(Plot1D):
    def __init__(self, parent=None, backend=None):
        super().__init__(parent, backend)
        self.setDataMargins(0.05, 0.05, 0.05, 0.05)
        self.setGraphXLabel("Components")
        self.setGraphYLabel("Singular values")

    def setData(self, vals: numpy.ndarray, title=None):
        if not isinstance(vals, numpy.ndarray):
            raise TypeError(
                f"vals should be an instance of {numpy.ndarray}. got {type(vals)} instead"
            )
        if title is None:
            title = ""
        self.setGraphTitle("Components representation of the dataset " + title)
        self.addCurve(numpy.arange(len(vals)), vals, symbol=".", linestyle=" ")


class PCAWidget(qt.QMainWindow):
    """
    Widget to apply PCA to a set of images and plot the eigenvalues found.
    """

    sigComputed = qt.Signal()

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)

        self._plot = PCAPlot()
        self.setCentralWidget(self._plot)

    def _computePCA(self):
        try:
            self._thread = OperationThread(self, self._dataset.pca)
            self._thread.setArgs(return_vals=True, indices=self.indices)
            self._thread.finished.connect(self._updateData)
            self._thread.start()
        except Exception as e:
            raise e

    def setDataset(self, dataset: dtypes.Dataset):
        self._dataset = dataset.dataset
        self.indices = dataset.indices
        self.bg_indices = dataset.bg_indices
        self.bg_dataset = dataset.bg_dataset
        self._computePCA()

    def _updateData(self):
        """
        Plots the eigenvalues.
        """
        self._thread.finished.disconnect(self._updateData)
        vals = self._thread.data
        self._plot.setData(vals, self._dataset.title)
        self.sigComputed.emit()
