from __future__ import annotations

from typing import Literal

from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict

from ..dtypes import Dataset
from ..pixel_sizes import PixelSize


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: Dataset
    """Input dataset containing a stack of images."""
    kind: Literal["rsm", "magnification"] | bool | MissingData = MISSING_DATA
    "Kind of transformation to apply. RSM only applicable for 1D datasets. 'magnification' is used if kind is not provided.",
    orientation: int | MissingData = MISSING_DATA
    """Used only with kind='magnification'."""
    magnification: float | MissingData = MISSING_DATA
    """To be used only with kind='magnification'. Magnification factor to apply to the dataset."""
    pixelSize: Literal["Basler", "PcoEdge_2x", "PcoEdge_10x"] | MissingData = (
        MISSING_DATA
    )
    """To be used only with kind='rsm', distance in micrometers of each pixel."""
    rotate: bool | MissingData = MISSING_DATA
    """To be used only with kind='rsm', if True the images with transformation are rotated 90 degrees."""


class TransformationMatrixComputation(
    Task,
    input_model=Inputs,
    output_names=["dataset"],
):
    """Computes transformation matrix and attach it to the dataset"""

    def run(self):
        input_dataset: Dataset = self.inputs.dataset
        if not isinstance(input_dataset, Dataset):
            raise TypeError(
                f"Dataset is expected to be an instance of {Dataset}. Got {type(input_dataset)} instead."
            )
        dataset = input_dataset.dataset

        if not dataset.dims.ndim:
            return input_dataset

        kind = self.get_input_value("kind", None)

        # Dirty workaround to handle both bool and str for kind because of legacy 2.X
        if isinstance(kind, bool):
            kind = "rsm" if kind else "magnification"

        if kind == "rsm":
            assert dataset.dims.ndim == 1, "Kind RSM can only be used for 1D datasets."

            pixelSize: str = self.get_input_value("pixelSize", None)
            rotate: bool = self.get_input_value("rotate", None)

            dataset.compute_transformation(
                PixelSize[pixelSize].value, kind=kind, rotate=rotate
            )
        else:
            magnification: float = self.get_input_value("magnification", None)
            orientation: int = self.get_input_value("orientation", None)

            if orientation == -1 or orientation is None:
                dataset.compute_transformation(magnification, kind=kind)
            else:
                dataset.compute_transformation(
                    magnification, topography_orientation=orientation
                )

        self.outputs.dataset = Dataset(
            dataset=dataset,
            indices=input_dataset.indices,
            bg_indices=input_dataset.bg_indices,
            bg_dataset=input_dataset.bg_dataset,
        )
