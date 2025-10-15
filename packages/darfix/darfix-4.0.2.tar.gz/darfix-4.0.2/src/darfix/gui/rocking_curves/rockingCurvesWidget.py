from __future__ import annotations

import numpy
from ewoksorange.gui.parameterform import block_signals
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D
from silx.io.dictdump import dicttonx

from ... import dtypes
from ...core.dataset import Operation
from ...core.rocking_curves import MAPS_1D
from ...core.rocking_curves import MAPS_2D
from ...core.rocking_curves import generate_rocking_curves_nxdict
from ...core.utils import NoDimensionsError
from ...core.utils import TooManyDimensionsForRockingCurvesError
from ..utils.message import missing_dataset_msg
from ..utils.utils import select_output_hdf5_file_with_dialog
from .fitComboBox import FitComboBox
from .rockingCurvesPlot import RockingCurvesPlot

# "Residuals" are not given by the fit but computed by the widget.
# It needs to be handled separately of other `MAPS` values
MAPS_CB_OPTIONS_1D = [*MAPS_1D, "Residuals"]
MAPS_CB_OPTIONS_2D = [*MAPS_2D, "Residuals"]


def _get_option_label(item: str, dataset: dtypes.ImageDataset):
    if "first motor" in item:
        return item.replace("first motor", dataset.dims.get(0).name)

    if "second motor" in item:
        return item.replace("second motor", dataset.dims.get(1).name)

    return item


class RockingCurvesWidget(qt.QWidget):
    """
    Widget to apply fit to a set of images and plot the amplitude, fwhm, peak position, background and residuals maps.
    """

    sigFitClicked = qt.Signal()

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)

        self.dataset = None
        self.indices = None
        self._update_dataset = None
        self._residuals_cache = None
        self.maps = None
        """ Holds the result of the fit as as a stack of maps"""

        layout = qt.QVBoxLayout()

        self._rockingCurvesPlot = RockingCurvesPlot(parent=self)
        layout.addWidget(self._rockingCurvesPlot)

        fitLayout = qt.QHBoxLayout()
        self._intensityThresholdLE = qt.QLineEdit("15")
        self._intensityThresholdLE.setValidator(qt.QDoubleValidator())
        fitLayout.addWidget(qt.QLabel("Intensity threshold:"))
        fitLayout.addWidget(self._intensityThresholdLE)

        self._fitMethodCB = FitComboBox()
        fitLayout.addWidget(qt.QLabel("Method"))
        fitLayout.addWidget(self._fitMethodCB)

        self._launchFitBtn = qt.QPushButton("Fit data")
        fitLayout.addWidget(self._launchFitBtn)
        self._launchFitBtn.clicked.connect(self._launchFit)
        layout.addLayout(fitLayout)

        self._abortFitBtn = qt.QPushButton("Abort")
        self._abortFitBtn.hide()
        self._abortFitBtn.clicked.connect(self.__abort)
        layout.addWidget(self._abortFitBtn)

        self._mapsCB = qt.QComboBox(self)
        self._mapsCB.hide()
        layout.addWidget(self._mapsCB)
        self._plotMaps = Plot2D(self)
        self._plotMaps.setDefaultColormap(
            Colormap(name="cividis", normalization="linear")
        )
        self._plotMaps.hide()
        layout.addWidget(self._plotMaps)
        self._exportButton = qt.QPushButton("Export maps")
        self._exportButton.hide()
        self._exportButton.clicked.connect(self.exportMaps)
        layout.addWidget(self._exportButton)

        self.setLayout(layout)

        # connect signal / slot
        self._mapsCB.currentTextChanged.connect(self._displayMap)

    def setDataset(self, dataset: dtypes.Dataset):
        if not dataset.dataset.dims.ndim:
            raise NoDimensionsError("RockingCurvesWidget")
        self.dataset = dataset.dataset
        self.indices = dataset.indices
        self._update_dataset = dataset.dataset
        self._residuals_cache = None

        if self.dataset.dims.ndim == 1:
            options = MAPS_CB_OPTIONS_1D
        elif self.dataset.dims.ndim == 2:
            options = MAPS_CB_OPTIONS_2D
        else:
            raise TooManyDimensionsForRockingCurvesError()

        with block_signals(self._mapsCB):
            self._mapsCB.clear()
            for option in options:
                self._mapsCB.addItem(_get_option_label(option, dataset=dataset.dataset))

        self._rockingCurvesPlot.setDataset(dataset)
        self._rockingCurvesPlot.updateStack()

    def _launchFit(self):
        """
        Method called when button for computing fit is clicked
        """
        if self.dataset is None:
            missing_dataset_msg()
            return

        self._launchFitBtn.hide()
        self.sigFitClicked.emit()
        # TODO: Abort button is not working
        # self._abortFit.show()

    def _computeResiduals(self) -> numpy.ndarray | None:
        """Note: The computation is cached as long as the dataset is loaded."""
        if self.dataset is None:
            missing_dataset_msg()
            return

        if self._residuals_cache is not None:
            return self._residuals_cache

        self._residuals_cache = numpy.sqrt(
            numpy.subtract(
                self._update_dataset.zsum(self.indices), self.dataset.zsum(self.indices)
            )
            ** 2
        )
        return self._residuals_cache

    def _displayMap(self, map_name: str):
        """
        :param map_name: Name of the map to display.
        """
        if self.dataset is None:
            return

        if self.maps is None:
            return

        title = self.dataset.title
        if title:
            graph_title = f"{title} - {map_name}"
        else:
            graph_title = map_name

        self._plotMaps.setKeepDataAspectRatio(True)
        self._plotMaps.setGraphTitle(graph_title)
        if map_name == "Residuals":
            self._addImage(self._computeResiduals())
            return

        self._addImage(self.maps[self._mapsCB.currentIndex()])

    def __abort(self):
        self._abortFitBtn.setEnabled(False)
        if self.dataset is not None:
            self.dataset.stop_operation(Operation.FIT)

    def onFitFinished(self):
        self._abortFitBtn.hide()
        self._launchFitBtn.show()

    def updateDataset(self, dataset: dtypes.ImageDataset, maps: numpy.ndarray):
        self._update_dataset, self.maps = dataset, maps
        self._displayMap(self._mapsCB.currentText())
        self._plotMaps.show()
        self._mapsCB.show()
        self._exportButton.show()

    def getIntensityThreshold(self) -> str:
        return self._intensityThresholdLE.text()

    def setIntensityThreshold(self, value: str):
        self._intensityThresholdLE.setText(value)

    def getFitMethod(self) -> str:
        return self._fitMethodCB.currentText()

    def setFitMethod(self, value: str):
        self._fitMethodCB.setCurrentText(value)

    def exportMaps(self):
        """
        Creates dictionary with maps information and exports it to a nexus file
        """
        if self.dataset is None or self.maps is None:
            missing_dataset_msg()
            return

        filename = select_output_hdf5_file_with_dialog()
        if filename:
            nxdict = generate_rocking_curves_nxdict(
                dataset=self.dataset, maps=self.maps, residuals=self._computeResiduals()
            )
            dicttonx(nxdict, filename)

    def _addImage(self, image):
        if self.dataset.transformation is None:
            self._plotMaps.addImage(image, xlabel="pixels", ylabel="pixels")
            return
        if self.dataset.transformation.rotate:
            image = numpy.rot90(image, 3)
        self._plotMaps.addImage(
            image,
            origin=self.dataset.transformation.origin,
            scale=self.dataset.transformation.scale,
            xlabel=self.dataset.transformation.label,
            ylabel=self.dataset.transformation.label,
        )
