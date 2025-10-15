from __future__ import annotations

from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict

from darfix import dtypes


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: dtypes.Dataset
    """ Input dataset containing a stack of images """
    bins: int | MissingData = MISSING_DATA
    """ Number of bins to use for partitioning the data. Default is the number of frames in the dataset."""
    filter_bottom_bin_idx: int | MissingData = MISSING_DATA
    """ index of the bins to retrieve bottom threshold filter value. If not defined, no filtering is applied."""
    filter_top_bin_idx: int | MissingData = MISSING_DATA
    """ index of the bins to retrieve top threshold filter value. If not defined, no filtering is applied."""


class DataPartition(
    Task,
    input_model=Inputs,
    output_names=["dataset"],
):
    """
    Filter frames with low intensity.
    """

    def run(self):
        dataset = self.inputs.dataset
        if not isinstance(dataset, dtypes.Dataset):
            raise TypeError(
                f"dataset is expected to be an instance of {dtypes.Dataset}. Got {type(dataset)}"
            )

        darfix_dataset = dataset.dataset

        indices, bg_indices = darfix_dataset.partition_by_intensity(
            bins=self.get_input_value("bins", None),
            bottom_bin=self.get_input_value("filter_bottom_bin_idx", None),
            top_bin=self.get_input_value("filter_top_bin_idx", None),
        )
        self.outputs.dataset = dtypes.Dataset(
            dataset=darfix_dataset,
            indices=indices,
            bg_indices=bg_indices,
            bg_dataset=dataset.bg_dataset,
        )
