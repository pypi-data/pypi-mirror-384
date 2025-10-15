from __future__ import annotations

from typing import Sequence

from ewokscore import Task
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict

from darfix.core.shiftcorrection import apply_shift
from darfix.dtypes import Dataset


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: Dataset
    """ Input dataset containing a stack of images """
    shift: Sequence[float] | Sequence[Sequence[float]] | None = None
    """Shift to apply to the images. If not provided, dataset will be unchanged."""
    selected_axis: int | None = None
    """Selected dimension axis. If not None. We considere a linear shift along this dimension.  Darfix convention is : dimension with axis 0 is the fast motor."""


class ShiftCorrection(
    Task,
    input_model=Inputs,
    output_names=["dataset"],
):
    def run(self):
        inputs = Inputs(**self.get_input_values())

        if inputs.shift is None:
            self.outputs.dataset = inputs.dataset
            return

        apply_shift(inputs.dataset, inputs.shift, inputs.selected_axis)

        self.outputs.dataset = inputs.dataset
