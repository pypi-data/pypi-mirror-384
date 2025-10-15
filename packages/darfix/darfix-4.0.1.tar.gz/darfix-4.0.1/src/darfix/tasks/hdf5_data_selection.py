from __future__ import annotations

import logging
import os.path

from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict
from pydantic import Field
from silx.io.url import DataUrl

from .. import dtypes
from ..core.data_selection import load_process_data

_logger = logging.getLogger(__file__)


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    raw_input_file: str = Field(
        examples=["/path/to/awesome/file.h5"], description="Path to the raw input file."
    )
    raw_detector_data_path: str = Field(
        examples=["/1.1/measurement/pco_ff"],
        description="Path to the raw detector data in the input file.",
    )
    raw_metadata_path: str | MissingData = Field(
        examples=["/1.1/instrument/positioners"],
        description="Path to the raw metadata in the input file.",
    )
    dark_input_file: str | MissingData = Field(
        default=MISSING_DATA,
        examples=["/path/to/dark/file.h5"],
        description="Path to the dark input file. Default is None.",
    )
    dark_detector_data_path: str | MissingData = Field(
        default=MISSING_DATA,
        examples=["/1.1/measurement/pco_ff"],
        description="Path to the dark detector data in the input file. Default is None.",
    )
    workflow_title: str | MissingData = MISSING_DATA
    """Title of the dataset for display purpose. Empty if not provided."""
    treated_data_dir: str | MissingData = MISSING_DATA
    """Processed output directory. If not provided, will try to find PROCESSED_DATA directory."""


class HDF5DataSelection(
    Task,
    input_model=Inputs,
    output_names=["dataset"],
):
    """Loads data and positioner metadata from a hdf5 file to create a Darfix dataset."""

    def run(self):
        raw_data_url = DataUrl(
            file_path=self.inputs.raw_input_file,
            data_path=self.inputs.raw_detector_data_path,
            scheme="silx",
        )

        raw_metadata_path = self.get_input_value("raw_metadata_path", None)
        if not raw_metadata_path:
            metadata_url = None
        else:
            metadata_url = DataUrl(
                file_path=self.inputs.raw_input_file,
                data_path=raw_metadata_path,
                scheme="silx",
            )

        dark_input_file = self.get_input_value("dark_input_file", None)
        dark_detector_data_path = self.get_input_value("dark_detector_data_path", None)
        if dark_input_file is None and dark_detector_data_path is not None:
            raise ValueError(
                "data path provided for background but no file path given."
            )

        if dark_input_file and dark_detector_data_path:
            bg_data_url = DataUrl(
                file_path=dark_input_file,
                data_path=dark_detector_data_path,
                scheme="silx",
            )
        else:
            bg_data_url = None

        treated_data_dir = self.get_input_value("treated_data_dir", None)
        # Move output folder to 'PROCESSED_DATA' instead of 'RAW_DATA' when possible
        # but ONLY if it was not set by the user
        if treated_data_dir is None and "RAW_DATA" in raw_data_url.file_path():
            treated_data_dir = os.path.dirname(raw_data_url.file_path()).replace(
                "RAW_DATA", "PROCESSED_DATA"
            )
            _logger.warning(f"Treated data will be saved in {treated_data_dir}")

        dataset, indices, bg_indices, bg_dataset = load_process_data(
            detector_url=raw_data_url.path(),
            root_dir=treated_data_dir,
            dark_detector_url=bg_data_url,
            title=self.get_input_value("workflow_title", ""),
            metadata_url=metadata_url,
        )

        self.outputs.dataset = dtypes.Dataset(
            dataset=dataset,
            indices=indices,
            bg_indices=bg_indices,
            bg_dataset=bg_dataset,
        )
