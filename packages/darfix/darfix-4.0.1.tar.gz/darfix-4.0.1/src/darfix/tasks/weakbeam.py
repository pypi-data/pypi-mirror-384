from __future__ import annotations

import os
import string

import h5py
import numpy
from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict

from darfix import dtypes


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: dtypes.Dataset
    """Input dataset containing a stack of images."""
    nvalue: float | MissingData = MISSING_DATA
    """Increase or decrease the top threshold by this fixed value."""
    indices: list[int] | MissingData = MISSING_DATA
    """Indices of the images to process. If not provided, all images will be processed."""
    title: str | MissingData = MISSING_DATA
    """Title for the output file. If not provided, title is empty."""


class WeakBeam(
    Task,
    input_model=Inputs,
    output_names=["dataset"],
):
    """
    Obtain dataset with filtered weak beam and recover its Center of Mass.
    Save file with this COM for further processing.
    """

    def run(self):
        dataset = self.inputs.dataset
        indices = self.get_input_value("indices", None)
        if isinstance(dataset, dtypes.Dataset):
            dataset = dataset.dataset
        if not isinstance(dataset, dtypes.ImageDataset):
            raise TypeError("dataset is expected to be an instance")

        nvalue = self.inputs.nvalue
        wb_dataset = dataset.recover_weak_beam(nvalue, indices=indices)
        com = wb_dataset.apply_moments(indices=indices)[0][0]
        os.makedirs(dataset.dir, exist_ok=True)
        filename = os.path.join(dataset.dir, "weakbeam_{}.hdf5".format(nvalue))

        title = self.get_input_value("title", "")
        # title can be set to None, MISSING_DATA or an empty string. So safer to use the following line
        title = title or self.get_random_title()
        with h5py.File(filename, "a") as _file:
            _file[title] = com

        self.outputs.dataset = dtypes.Dataset(
            dataset=dataset,
            indices=indices,
            bg_indices=self.inputs.dataset.bg_indices,
            bg_dataset=self.inputs.dataset.bg_dataset,
        )

    @staticmethod
    def get_random_title() -> str:
        letters = string.ascii_lowercase
        return "".join(numpy.random.choice(list(letters)) for i in range(6))
