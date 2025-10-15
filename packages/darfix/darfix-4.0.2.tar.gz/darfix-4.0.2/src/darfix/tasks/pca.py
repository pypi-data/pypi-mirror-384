from __future__ import annotations

from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.missing_data import is_missing_data
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict

from darfix.dtypes import Dataset


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: Dataset
    """ Input dataset containing a stack of images """
    num_components: int | MissingData = MISSING_DATA
    """Number of principal components to compute."""


class PCA(
    Task,
    input_model=Inputs,
    output_names=["vals", "dataset"],
):
    """Compute Principal Component Analysis on a Darfix dataset.

    More about PCA : https://en.wikipedia.org/wiki/Principal_component_analysis"""

    def run(self):
        dataset = self.inputs.dataset
        if not isinstance(dataset, Dataset):
            raise TypeError(
                f"dataset is expected to be an instance of {Dataset}. Got {type(dataset)} instead"
            )
        num_components = self.get_input_value("num_components")

        pca_kwargs = {"return_vals": True, "indices": dataset.indices}
        if not is_missing_data(num_components):
            pca_kwargs["num_components"] = num_components

        vals = dataset.dataset.pca(**pca_kwargs)

        self.outputs.vals = vals
        self.outputs.dataset = Dataset(
            dataset=dataset.dataset,
            indices=dataset.indices,
            bg_dataset=dataset.bg_dataset,
            bg_indices=dataset.bg_indices,
        )
