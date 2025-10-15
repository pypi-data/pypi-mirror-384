from __future__ import annotations

import logging

import numpy
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot.StackView import StackViewMainWindow

from darfix import config
from darfix import dtypes
from darfix.core.dataset import ImageDataset
from darfix.core.noiseremoval import BackgroundType
from darfix.core.noiseremoval import NoiseRemovalOperation
from darfix.core.state_of_operation import Operation

from .operationHistory import OperationHistoryWidget
from .parametersWidget import ParametersWidget

_logger = logging.getLogger(__name__)


class NoiseRemovalWidget(qt.QWidget):
    """
    Widget to apply noise removal from a dataset.
    For now it can apply both background subtraction and hot pixel removal.
    For background subtraction the user can choose the background to use:
    dark frames, low intensity data or all the data. From these background
    frames, an image is computed either using the mean or the median.
    """

    sigLaunchOperation = qt.Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._incomingOperations: list[NoiseRemovalOperation] = []
        self._input_dataset: ImageDataset | None = None
        self.indices: numpy.ndarray | None = None
        self.bg_indices: numpy.ndarray | None = None
        self.bg_dataset: ImageDataset | None = None
        self.setWindowFlags(qt.Qt.WindowType.Widget)

        self._parametersWidget = ParametersWidget()
        self._sv = StackViewMainWindow()
        self._sv.setColormap(
            Colormap(
                name=config.DEFAULT_COLORMAP_NAME,
                normalization=config.DEFAULT_COLORMAP_NORM,
            )
        )
        self._sv.setKeepDataAspectRatio(True)
        self._size = None
        self._method = None
        self._background = self._parametersWidget.bsBackgroundCB.currentText()
        self._bottom_threshold = self._parametersWidget.bottomLE.text()
        self._top_threshold = self._parametersWidget.topLE.text()

        self._operationHistory = OperationHistoryWidget()

        layout = qt.QVBoxLayout()
        layout.addWidget(self._sv)
        layout.addWidget(self._parametersWidget)
        layout.addWidget(self._operationHistory)
        self.setLayout(layout)

        # Add connections
        self._parametersWidget.computeBS.clicked.connect(
            self._launchBackgroundSubtraction
        )
        self._parametersWidget.computeHP.clicked.connect(self._launchHotPixelRemoval)
        self._parametersWidget.computeTP.clicked.connect(self._launchThresholdRemoval)
        self._parametersWidget.computeMR.clicked.connect(self._launchMaskRemoval)

    def refreshPlot(self):
        # TODO is there another way to refresh data plot ?
        self.setStack()

    def setDataset(self, dataset: dtypes.Dataset):
        """Saves the dataset and updates the stack with the dataset data."""

        self._operationHistory.clear()

        self._dataset = dataset.dataset
        self.indices = dataset.indices
        if self._dataset.title != "":
            self._sv.setTitleCallback(lambda idx: self._dataset.title)
        self.setStack()
        self.bg_indices = dataset.bg_indices
        self.bg_dataset = dataset.bg_dataset

        self._parametersWidget.computeBS.show()
        self._parametersWidget.computeHP.show()
        self._parametersWidget.computeTP.show()
        self._parametersWidget.computeMR.show()

        """
        Sets the available background for the user to choose.
        """
        self._parametersWidget.bsBackgroundCB.clear()
        if dataset.bg_dataset is not None:
            self._parametersWidget.bsBackgroundCB.addItem(
                BackgroundType.DARK_DATA.value
            )
        if dataset.bg_indices is not None:
            self._parametersWidget.bsBackgroundCB.addItem(
                BackgroundType.UNUSED_DATA.value
            )
        self._parametersWidget.bsBackgroundCB.addItem(BackgroundType.DATA.value)

    def _launchBackgroundSubtraction(self):
        self._background = self._parametersWidget.bsBackgroundCB.currentText()

        self._method = self._parametersWidget.bsMethodsCB.currentText()

        operation = NoiseRemovalOperation(
            type=Operation.BS,
            parameters={
                "method": self.method,
                "background_type": self._background,
            },
        )
        self._launchOperationInThread(operation)

    def _launchHotPixelRemoval(self):
        self._size = self._parametersWidget.hpSizeCB.currentText()

        operation = NoiseRemovalOperation(
            type=Operation.HP,
            parameters={
                "kernel_size": int(self._size),
            },
        )
        self._launchOperationInThread(operation)

    def _launchThresholdRemoval(self):
        self._bottom_threshold = self._parametersWidget.bottomLE.text()
        self._top_threshold = self._parametersWidget.topLE.text()

        operation = NoiseRemovalOperation(
            type=Operation.THRESHOLD,
            parameters={
                "bottom": int(self._bottom_threshold),
                "top": int(self._top_threshold),
            },
        )
        self._launchOperationInThread(operation)

    def _launchMaskRemoval(self):
        mask = self.mask
        if mask is None:
            return
        operation = NoiseRemovalOperation(
            type=Operation.MASK,
            parameters={"mask": mask},
        )
        self._launchOperationInThread(operation)

    def _launchOperationInThread(self, operation: NoiseRemovalOperation):
        self.sigLaunchOperation.emit(operation)

    def setStack(self, dataset=None):
        """
        Sets new data to the stack.
        Mantains the current frame showed in the view.

        :param Dataset dataset: if not None, data set to the stack will be from the given dataset.
        """
        new_dataset = dataset if dataset is not None else self._dataset
        if new_dataset is None:
            return
        old_nframe = self._sv.getFrameNumber()
        self._sv.setStack(new_dataset.as_array3d(self.indices))
        self._sv.setFrameNumber(old_nframe)

    def setDefaultParameters(self, operations: list[NoiseRemovalOperation]):
        """
        Set default values un widget parameters based on previous user history

        :param history: previous user history
        """
        self._parametersWidget.set_default_values(operations)

    def extendOperationHistory(self):
        self._operationHistory.extend(self._incomingOperations)
        self._incomingOperations.clear()

    def abortIncomingOperations(self):
        for op in self._incomingOperations:
            op["aborted"] = True
        self._operationHistory.extend(self._incomingOperations)
        self._incomingOperations.clear()

    def getOperationHistory(self):
        return self._operationHistory.getOperations()

    def setIncomingOperations(
        self, operations: list[NoiseRemovalOperation], clear=False
    ):
        if self.hasIncomingOperations() and not clear:
            _logger.error(
                f"These operations have not been executed : {self._incomingOperations}"
            )
        self._incomingOperations = operations

    def hasIncomingOperations(self) -> bool:
        return len(self._incomingOperations) > 0

    def getIncomingOperations(self) -> tuple[NoiseRemovalOperation]:
        return self._incomingOperations

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size
        self._parametersWidget.hpSizeCB.setCurrentText(size)

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, method):
        self._method = method
        self._parametersWidget.bsMethodsCB.setCurrentText(method)

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, background):
        if self._parametersWidget.bsBackgroundCB.findText(background) >= 0:
            self._background = background
            self._parametersWidget.bsBackgroundCB.setCurrentText(background)

    @property
    def bottom_threshold(self):
        return self._bottom_threshold

    @bottom_threshold.setter
    def bottom_threshold(self, bottom):
        self._bottom_threshold = bottom
        self._parametersWidget.bottomLE.setText(bottom)

    @property
    def top_threshold(self):
        return self._top_threshold

    @top_threshold.setter
    def top_threshold(self, top):
        self._top_threshold = top
        self._parametersWidget.topLE.setText(top)

    @property
    def _dataset(self):
        return self._input_dataset

    @_dataset.setter
    def _dataset(self, dataset):
        self._input_dataset = dataset
        self.__clearMaskWithWrongShape()

    @property
    def mask(self):
        return self._svPlotWidget.getSelectionMask()

    @mask.setter
    def mask(self, mask):
        self.__storeMask(mask)
        self.__clearMaskWithWrongShape()

    def __storeMask(self, mask):
        if mask is None:
            self._svPlotWidget.clearMask()
        else:
            self._svPlotWidget.setSelectionMask(mask)

    @property
    def _svPlotWidget(self):
        return self._sv.getPlotWidget()

    def __clearMaskWithWrongShape(self):
        mask = self.mask
        if mask is None:
            return
        if self._dataset is None or self._dataset.data is None:
            return
        stack_shape = self._dataset.data.shape[-2:]
        mask_shape = mask.shape
        if stack_shape == mask_shape:
            return
        self.__storeMask(mask)
