from __future__ import annotations

import logging
from typing import Any
from typing import Dict

import numpy
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot.StackView import StackViewMainWindow

import darfix

from ... import dtypes
from ...core.dataset import ImageDataset
from ..filterByDimension import FilterByDimensionWidget
from ..operationProcess import OperationProcess
from ..utils.message import missing_dataset_msg
from .shiftInput import ShiftInput

_logger = logging.getLogger(__file__)


class ShiftCorrectionWidget(qt.QMainWindow):
    """
    A widget to apply shift correction to a stack of images
    """

    correctSignal = qt.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(qt.Qt.WindowType.Widget)
        self._input_dataset: ImageDataset | None = None
        self.indices = None
        self.bg_indices = None
        self.bg_dataset = None
        self._axis = None

        self._shiftWidget = ShiftInput(parent=self)
        self._shiftWidget.correctionB.setEnabled(False)
        self._shiftWidget.correctionB.clicked.connect(self.correctSignal.emit)

        self._sv = StackViewMainWindow()
        self._sv.setColormap(
            Colormap(name=darfix.config.DEFAULT_COLORMAP_NAME, normalization="linear")
        )
        self._sv.setKeepDataAspectRatio(True)

        self._filterByDimensionWidget = FilterByDimensionWidget()

        toolbar = qt.QToolBar()
        toolbar.addWidget(self._filterByDimensionWidget)
        toolbar.addWidget(self._shiftWidget)
        self.setCentralWidget(self._sv)
        self.addToolBar(qt.Qt.ToolBarArea.RightToolBarArea, toolbar)

        self._shiftWidget.findShiftB.clicked.connect(self._launchFindShift)
        self._shiftWidget.abortShiftB.clicked.connect(self._abortFindShift)
        self._filterByDimensionWidget.axisChanged.connect(self._onAxisChanged)
        self._filterByDimensionWidget.stateDisabled.connect(
            self._onDisablingFiterByDimension
        )

        self._filterByDimensionWidget.hide()

    def getShift(self) -> numpy.ndarray:
        return numpy.array(self._shiftWidget.getShift())

    def setShift(self, shift: numpy.ndarray):
        self._shiftWidget.setShift((shift[0], shift[1]))

    def setDataset(self, dataset: dtypes.Dataset):
        """Saves the dataset and updates the stack with the dataset data."""

        self._input_dataset = dataset.dataset
        self._shiftWidget.correctionB.setEnabled(True)
        self._sv.setKeepDataAspectRatio(True)
        self._sv.setGraphTitle(self._input_dataset.title)
        self._filterByDimensionWidget.setDimensions(self._input_dataset.dims)

        self.refreshPlot()

    def _launchFindShift(self):
        dataset = self._input_dataset
        if dataset is None:
            missing_dataset_msg()
            return

        self._shiftWidget.findShiftB.setDisabled(True)
        self._shiftWidget.abortShiftB.setEnabled(True)

        self._startFindShiftThread(dataset)

    def _abortFindShift(self):
        self.thread_detection.kill()

    def _startFindShiftThread(self, dataset: ImageDataset):
        self.thread_detection = OperationProcess(
            self,
            dataset.find_shift,
            self._axis,
            indices=self.indices,
        )
        self.thread_detection.finished.connect(self._updateShift)
        self.thread_detection.start()

    def _updateShift(self, data: tuple | None):
        self._shiftWidget.findShiftB.setEnabled(True)
        self._shiftWidget.abortShiftB.setDisabled(True)
        self.thread_detection.finished.disconnect(self._updateShift)
        if data is None:
            # Aborted
            return
        self.setShift(numpy.round(data, 5))

    def getCorrectionInputs(self) -> Dict[str, Any]:
        return {
            "shift": self.getShift(),
            "selected_axis": self._axis,
        }

    def setCorrectionInputs(
        self,
        shift: tuple[float, float],
        selected_axis: int | None,
    ):
        """
        Set widget parameters from .ows save

        :param dimension_idx: dimension_idx is the index of the chosen dimension
        :param shift : shift is (shift_x, shift_y) when dimension_idx is None, else this is (shift_x1, shift_y1), ..., (shift_xn, shift_yn) with n = the dimension size
        """
        if (
            (selected_axis is not None and not isinstance(selected_axis, int))
            or not isinstance(shift, tuple)
            or not isinstance(shift[0], (int, float))
        ):
            _logger.warning(
                "Bad saved values for shift. Save file from Darfix < 4.0 ? Saved shift is discarded."
            )
            return

        self.setShift(shift)
        self._axis = selected_axis

    def _clearStack(self):
        self._sv.setStack(None)
        self._shiftWidget.correctionB.setEnabled(False)

    def _onAxisChanged(self, axis: int) -> None:
        # We only handle one fixed dimension
        self._axis = axis
        self.refreshPlot()

    def _onDisablingFiterByDimension(self) -> None:
        self._axis = None
        self.refreshPlot()

    def refreshPlot(self) -> None:
        # TODO is there another way to refresh plot ?
        if self._axis is None:
            self._sv.setStack(self._input_dataset.as_array3d(self.indices))
        else:
            self._sv.setStack(self._input_dataset.z_sum_along_axis(self._axis))
