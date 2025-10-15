from __future__ import annotations

import os.path
from pathlib import Path
from typing import Literal

from ewokscore import Task
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict
from silx.io.dictdump import dicttonx

from ..core.rocking_curves import compute_residuals
from ..core.rocking_curves import generate_rocking_curves_nxdict
from ..dtypes import Dataset


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: Dataset
    """ Input dataset containing a stack of images """
    int_thresh: float | None = None
    """If provided, only the rocking curves with higher ptp (peak to peak) value > int_thresh are fitted, others are assumed to be noise and will be discarded"""
    method: Literal["trf", "lm", "dogbox"] = "trf"
    """Method to use for the rocking curves fit"""
    output_filename: str | Path | None = None
    """Output filename to save the rocking curves results. Results are not saved if not provided"""


class RockingCurves(Task, input_model=Inputs, output_names=["dataset", "maps"]):
    """Analyze the rocking curve of each pixel of each image of the darfix dataset by fitting to a peak shape, e.g. a Gaussian.

    Related article : https://pmc.ncbi.nlm.nih.gov/articles/PMC10161887/#sec3.3.1
    """

    def run(self):
        inputs = Inputs(**self.get_input_values())

        output_filename = inputs.output_filename
        if output_filename and os.path.isfile(output_filename):
            raise FileExistsError(
                f"""Cannot launch rocking curves fit: saving destination {output_filename} already exists.
                Change the `output_filename` input or set it to None to disable saving."""
            )

        dataset = inputs.dataset.dataset
        indices = inputs.dataset.indices
        new_image_dataset, maps = dataset.apply_fit(
            indices=indices, int_thresh=inputs.int_thresh, method=inputs.method
        )

        if output_filename is not None:
            nxdict = generate_rocking_curves_nxdict(
                new_image_dataset,
                maps,
                residuals=compute_residuals(new_image_dataset, dataset, indices),
            )
            dicttonx(nxdict, output_filename)

        self.outputs.dataset = Dataset(
            dataset=new_image_dataset,
            indices=indices,
            bg_indices=inputs.dataset.bg_indices,
            bg_dataset=inputs.dataset.bg_dataset,
        )
        self.outputs.maps = maps
