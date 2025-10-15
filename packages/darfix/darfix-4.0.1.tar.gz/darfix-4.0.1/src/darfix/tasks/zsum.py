from __future__ import annotations

import numpy
from ewokscore import Task
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict

from darfix import dtypes


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: dtypes.Dataset
    """Input dataset containing a stack of images."""
    selected_axis: int | None = None
    """Selected axis in dataset.dataset.data. The zsum is computed for each value of this axis."""


class ZSum(
    Task,
    input_model=Inputs,
    output_names=["zsum"],
):
    """Sum all images of the dataset or images at specified indices along a given dimension."""

    def run(self):
        inputs = Inputs(**self.get_input_values())
        dataset = inputs.dataset.dataset

        if inputs.selected_axis is None:
            # AS 3D array
            self.outputs.zsum = dataset.zsum()[numpy.newaxis, :, :]
        else:
            self.outputs.zsum = dataset.z_sum_along_axis(inputs.selected_axis)
