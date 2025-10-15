from __future__ import annotations

import logging
from enum import Enum

import numpy
from ewokscore.missing_data import is_missing_data
from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread

from darfix import dtypes
from darfix.gui.roiSelectionWidget import ROISelectionWidget
from darfix.tasks.roi import RoiSelection

_logger = logging.getLogger(__name__)


class _ROIBehavior(Enum):
    """Define the different behavior we can have regarding ROI"""

    FIT_TO_DATASET = "fit-to-dataset"
    """When a ROI is applied we want to update the ROI to the shape to show the user that the ROI has been applied"""
    PROPOSE_USER_ROI = "propose-ROI-to-user"
    """When a new dataset is set (or when resetting) we want to propose to the user a subset of the frame (one fifth of the current frame shape)"""


class RoiSelectionWidgetOW(OWEwoksWidgetOneThread, ewokstaskclass=RoiSelection):
    name = "roi selection"
    icon = "icons/roi.png"
    want_main_area = True
    want_control_area = False

    _ewoks_inputs_to_hide_from_orange = ("roi_origin", "roi_size")

    def __init__(self):
        super().__init__()

        self._widget = ROISelectionWidget(parent=self)
        self.mainArea.layout().addWidget(self._widget)
        self._widget.sigApply.connect(self._updateActiveDataset)
        self._widget.sigValidate.connect(self._validateResult)
        self._widget.sigReset.connect(self._reset)

        self._update_dataset: dtypes.Dataset = None
        """Dataset updated when the users press 'apply'"""
        self._dataset: dtypes.Dataset = None
        """Original input dataset"""

        self._nextRoiInteractionBehavior: _ROIBehavior = _ROIBehavior.PROPOSE_USER_ROI
        """When a new output is received we want either to:
        * propose a ROI fitting the dataset shape (if a ROI - subset of the dataset - has been applied)
        * propose a ROI on a subset of the dataset (in the case a new dataset has been received)
        """

    def _validateResult(self):
        self._nextRoiInteractionBehavior = _ROIBehavior.PROPOSE_USER_ROI
        self.propagate_downstream()
        self.accept()

    def handleNewSignals(self):
        dataset: dtypes.Dataset = self.get_task_input_value("dataset")

        if is_missing_data(dataset):
            return

        self._dataset = self._update_dataset = dataset

        self._widget.setDataset(dataset)
        self.open()
        self._nextRoiInteractionBehavior = _ROIBehavior.PROPOSE_USER_ROI

        if not self._tryRecoverLastRoi():
            self._resetTaskAndROI(dataset=dataset)

    def _updateActiveDataset(self):

        self._widget.clampRoiToDataset(self._update_dataset.dataset)
        roi = self._widget.getRoi()

        self.set_default_input("roi_origin", roi.getOrigin().tolist())
        self.set_default_input("roi_size", roi.getSize().tolist())
        self._nextRoiInteractionBehavior = _ROIBehavior.FIT_TO_DATASET
        self.execute_ewoks_task_without_propagation()
        self._widget.enableApplyingROI(False)

    def _updateROI(self):
        if self._nextRoiInteractionBehavior is _ROIBehavior.FIT_TO_DATASET:
            # Apply
            self._widget.enableValidation(True)
            self._widget._fitROIToDataset(self._update_dataset.dataset)
        elif self._nextRoiInteractionBehavior is _ROIBehavior.PROPOSE_USER_ROI:
            # Reset
            self._widget.enableValidation(False)
            self._widget._setROIForNewDataset(self._update_dataset.dataset)
        else:
            raise NotImplementedError(
                f"Behavior not defined ({self._nextRoiInteractionBehavior})"
            )

    def task_output_changed(self):
        super().task_output_changed()
        self._update_dataset = self.get_task_output_value("dataset")

        if is_missing_data(self._update_dataset):
            _logger.error("Roi application failed (or cancelled)")
            return

        self._updateROI()

        self._widget.setStack(self._update_dataset.dataset)
        # update the input dataset for next iteration
        self.set_dynamic_input("dataset", self._update_dataset)

    def _reset(self):
        self._update_dataset = self._dataset

        self._nextRoiInteractionBehavior = _ROIBehavior.PROPOSE_USER_ROI
        self._widget.setDataset(self._update_dataset)
        self._resetTaskAndROI(dataset=self._update_dataset)

    def _tryRecoverLastRoi(self) -> bool:
        """Look at saved default input in .ows and try propose the roi on the current dataset."""
        origin = self.get_task_input_value("roi_origin")
        size = self.get_task_input_value("roi_size")

        if (
            is_missing_data(origin)
            or is_missing_data(size)
            or len(origin) != 2
            or len(size) != 2
        ):
            return False

        origin = numpy.array(origin)
        size = numpy.array(size)
        self._widget.setRoi(size=size, origin=origin)
        self._widget.enableValidation(False)
        self._widget.enableApplyingROI(True)
        return True

    def _resetTaskAndROI(self, dataset: dtypes.Dataset):
        """
        Reset the original dataset (last dataset received) and the ROI.

        When receiving a new dataset or resetting it, we need to process the task to
        retrieve the task output dataset when the user presses ok.
        To speed up process in this specific case (ROI match frame shape), the task will simply propagate the original dataset.
        """
        self.set_default_input("roi_origin", (0, 0))
        self.set_default_input("roi_size", dataset.dataset.frame_shape)
        self.set_dynamic_input("dataset", dataset)
        self.execute_ewoks_task_without_propagation()

        self._widget.enableValidation(False)
        self._widget.enableApplyingROI(True)
