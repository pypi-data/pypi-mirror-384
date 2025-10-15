from __future__ import annotations

import logging

import numpy
from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict

from darfix.core.dataset import ImageDataset
from darfix.dtypes import Dataset

logger = logging.getLogger(__file__)


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: Dataset
    """Input dataset containing a stack of images."""
    roi_origin: numpy.ndarray | list[float] | MissingData = MISSING_DATA
    """Origin of the ROI to apply. If not provided, dataset will be unchanged."""
    roi_size: numpy.ndarray | list[float] | MissingData = MISSING_DATA
    """Size of the ROI to apply. If not provided, dataset will be unchanged."""


class RoiSelection(
    Task,
    input_model=Inputs,
    output_names=["dataset"],
):
    """Apply a Region of Interest (ROI) selection on a Darfix dataset."""

    def run(self):
        input_dataset: Dataset = self.inputs.dataset
        dataset: ImageDataset = input_dataset.dataset
        bg_dataset: ImageDataset | None = input_dataset.bg_dataset

        origin: numpy.ndarray = numpy.flip(self.get_input_value("roi_origin", []))
        size: numpy.ndarray = numpy.flip(self.get_input_value("roi_size", []))

        frame_shape: numpy.ndarray = numpy.flip(dataset.frame_shape)

        if len(origin) == 0 or len(size) == 0:
            # ROI undefined
            logger.warning(
                f"Cannot apply a ROI if origin ({origin}) or size ({size}) is empty. Dataset is unchanged."
            )
        elif tuple(origin) == (0, 0) and tuple(size) == tuple(frame_shape):
            logger.info("ROI is covering the full frame. Dataset is unchanged.")
            # ROI covering the frame shape
            pass
        else:
            dataset = dataset.apply_roi(origin=origin, size=size)
            if bg_dataset:
                bg_dataset = bg_dataset.apply_roi(origin=origin, size=size)

        self.outputs.dataset = Dataset(
            dataset=dataset,
            indices=input_dataset.indices,
            bg_indices=input_dataset.bg_indices,
            bg_dataset=bg_dataset,
        )
