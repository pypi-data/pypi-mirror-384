from __future__ import annotations

from typing import Optional

import numpy
from silx.gui import qt
from silx.gui.plot import Plot1D

from darfix import dtypes


class DataPartitionWidget(qt.QMainWindow):
    sigComputeHistogram = qt.Signal()
    "emit when the user ask for computing the histogram"
    sigPartitionData = qt.Signal()
    "emit when the user ask for filtering the data"
    sigAbort = qt.Signal()
    "emit when user request to abort the processing"
    sigNbBinsChanged = qt.Signal(int)
    "emit when the number of bins has changed"
    sigBottomBinChanged = qt.Signal(int)
    "emit when the bottom bin has changed"
    sigTopBinChanged = qt.Signal(int)
    "emit when the top bin has changed"

    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)
        self._dataset = None

        self._plot = Plot1D()

        binsLabel = qt.QLabel("Number of histogram bins:")
        filterRangeLabel = qt.QLabel("Filter range:")
        self._bins = qt.QLineEdit("")
        self._bins.setToolTip(
            "Defines the number of equal-width bins in the given range for the histogram"
        )
        self._bins.setValidator(qt.QIntValidator())
        self._bottomBinsNumber = qt.QLineEdit("")
        self._bottomBinsNumber.setPlaceholderText("First bin")
        self._bottomBinsNumber.setToolTip(
            "Minimum bin to use. It is 0 if nothing is entered."
        )
        self._topBinsNumber = qt.QLineEdit("")
        self._topBinsNumber.setPlaceholderText("Last bin")
        self._topBinsNumber.setToolTip(
            "Maximum bin to use. It is the number of bins if nothing is entered"
        )
        self._bottomBinsNumber.setValidator(qt.QIntValidator())
        self._topBinsNumber.setValidator(qt.QIntValidator())
        self._computeHistogramPB = qt.QPushButton("Compute histogram")
        self._computePartitionPB = qt.QPushButton("Filter")
        self._abortPB = qt.QPushButton("Abort")
        widget = qt.QWidget(parent=self)
        layout = qt.QGridLayout()
        layout.addWidget(binsLabel, 0, 0, 1, 1)
        layout.addWidget(self._bins, 0, 1, 1, 1)
        layout.addWidget(filterRangeLabel, 1, 0, 1, 1)
        layout.addWidget(self._bottomBinsNumber, 1, 1)
        layout.addWidget(self._topBinsNumber, 1, 2)
        layout.addWidget(self._computeHistogramPB, 0, 2, 1, 1)
        layout.addWidget(self._computePartitionPB, 2, 2, 1, 1)
        layout.addWidget(self._abortPB, 3, 2, 1, 1)
        layout.addWidget(self._plot, 3, 0, 1, 3)
        widget.setLayout(layout)
        widget.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
        self.setCentralWidget(widget)
        self._plot.hide()

        self.setProcessingButtonsEnabled(enable=False)

        # set up
        self._abortPB.hide()

        # connect signal / slot
        self._abortPB.pressed.connect(self.sigAbort)
        self._computeHistogramPB.released.connect(self.sigComputeHistogram)
        self._computePartitionPB.released.connect(self.sigPartitionData)
        self._bins.editingFinished.connect(self._nbBinsChanged)
        self._bottomBinsNumber.editingFinished.connect(self._nbBottomBinChanged)
        self._topBinsNumber.editingFinished.connect(self._nbTopBinChanged)

    def _nbBinsChanged(self):
        self.sigNbBinsChanged.emit(self.getBins())

    def _nbBottomBinChanged(self):
        self.sigBottomBinChanged.emit(self.getBottomBin())

    def _nbTopBinChanged(self):
        self.sigTopBinChanged.emit(self.getTopBin())

    def setDataset(self, dataset):
        if not isinstance(dataset, dtypes.Dataset):
            raise dtypes.DatasetTypeError(dataset)
        self.setBins(dataset.dataset.nframes)
        self.setProcessingButtonsEnabled(enable=True)

    def _showHistogramCallback(self):
        sender = self.sender()
        frames_intensity = sender.data
        self.showHistogram(frames_intensity=frames_intensity)

    def showHistogram(self, frames_intensity: Optional[numpy.array]):
        """
        Plots the frame intensity histogram.
        """
        self._abortPB.hide()
        self._abortPB.setEnabled(True)
        self._computePartitionPB.setEnabled(True)
        self._computeHistogramPB.setEnabled(True)
        self._plot.clear()
        if frames_intensity is not None:
            values, bins = numpy.histogram(
                frames_intensity, numpy.arange(self.getBins())
            )
            self._plot.addHistogram(values, bins, fill=True)
            self._plot.show()

    # bins getter / setter
    def getBins(self) -> Optional[int]:
        text = self._bins.text().replace(" ", "")
        if text == "":
            return None
        else:
            return int(text)

    def setBins(self, value: int | str | None):
        if value in ("", None):
            self._bins.clear()
        else:
            self._bins.setText(str(value))

    def getBottomBin(self) -> Optional[int]:
        text = self._bottomBinsNumber.text().replace(" ", "")
        if text == "":
            return None
        else:
            return int(text)

    def setBottomBin(self, value: int | str | None):
        if value in ("", None):
            self._bottomBinsNumber.clear()
        else:
            self._bottomBinsNumber.setText(str(value))

    def getTopBin(self) -> Optional[int]:
        text = self._topBinsNumber.text().replace(" ", "")
        if text == "":
            return None
        else:
            return int(text)

    def setTopBin(self, value: int | str | None):
        if value in ("", None):
            self._topBinsNumber.clear()
        else:
            self._topBinsNumber.setText(str(value))

    # util function
    def setProcessingButtonsEnabled(self, enable: bool):
        self._abortPB.setEnabled(not enable)
        self._computePartitionPB.setEnabled(enable)
        self._computeHistogramPB.setEnabled(enable)
