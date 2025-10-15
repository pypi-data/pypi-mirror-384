from __future__ import annotations

from typing import Literal

from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict

from ..dtypes import Dataset
from ..math import Vector3D
from ..pixel_sizes import PixelSize


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: Dataset
    """Input dataset containing a stack of images."""
    Q: Vector3D
    """Scattering vector in oriented pseudocubic coordinates."""
    a: float
    """Pseudocubic lattice parameter."""
    map_range: float
    """Range (in all 3 directions) of the histogram. Center-to-edge distance."""
    detector: str
    """Detector type for the RSM computation."""
    units: Literal["poulsen", "gorfman"] | MissingData = MISSING_DATA
    """Either 'poulsen' [10.1107/S1600576717011037] or 'gorfman' [https://arxiv.org/pdf/2110.14311.pdf]. 'poulsen' if not provided"""
    n: Vector3D | MissingData = MISSING_DATA
    """Surface normal of the sample in oriented pseudocubic hkl"""
    map_shape: Vector3D | MissingData = MISSING_DATA
    """Number of bins in each direction."""
    energy: float | MissingData = MISSING_DATA


class RSMHistogram(
    Task,
    input_model=Inputs,
    output_names=["hist_values", "hist_edges"],
):
    """Computes Reciprocal Space Map histogram."""

    def run(self):
        input_dataset = self.inputs.dataset
        if not isinstance(input_dataset, Dataset):
            raise TypeError(
                f"dataset is expected to be an instance of Dataset. Got {type(input_dataset)}."
            )
        dataset = input_dataset.dataset

        units: str | None = self.get_input_value("units", None)
        n: Vector3D | None = self.get_input_value("n", None)
        map_shape: Vector3D | None = self.get_input_value("map_shape", None)
        energy: float | None = self.get_input_value("energy", None)

        values, edges = dataset.compute_rsm(
            Q=self.inputs.Q,
            a=self.inputs.a,
            map_range=self.inputs.map_range,
            pixel_size=PixelSize[self.inputs.detector].value,
            units=units.lower() if units else None,
            n=n,
            map_shape=map_shape,
            energy=energy,
        )

        self.outputs.hist_values = values
        self.outputs.hist_edges = edges
