from __future__ import annotations

import logging
from typing import Any
from typing import Iterable

import numpy
from ewokscore import Task
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict
from pydantic import Field

from darfix import dtypes
from darfix.core.dataset import ImageDataset
from darfix.core.dimension import AcquisitionDims
from darfix.core.dimension import Dimension
from darfix.core.dimension import find_dimensions_from_metadata
from darfix.core.fscan_parser import fscan_get_dimensions
from darfix.core.zigzag_mode import reorder_frames_of_zigzag_scan

_logger = logging.getLogger(__file__)

REL_TOLERANCE_FOR_MIN_MAX_VALIDATION = 1e-1  # 10%


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: dtypes.Dataset
    """ Input dataset containing a stack of images """
    dims: dict[int, Any] | MissingData = Field(
        default=MISSING_DATA,
        examples=[
            {
                0: {"name": "diffrx", "size": 5, "range": [0.0, 5.0, 1.0]},
                1: {"name": "diffry", "size": 10, "range": [0.0, 10.0, 1.0]},
            }
        ],
        description="Dimensions to use for the dataset. If not provided, the task will try to find dimensions from metadata.",
    )
    tolerance: float | MissingData = MISSING_DATA
    """Tolerance to use for finding dimensions from metadata. Default is 1e-9."""
    is_zigzag: bool | MissingData = MISSING_DATA
    """Set to True if the scan was a zigzag scan (slow motor moving back and forth). Defaults to False."""


class DimensionDefinition(
    Task,
    input_model=Inputs,
    output_names=["dataset"],
):
    """
    Fit dimension of given dataset.
    If dims are provided then will use them. else will call 'find_dimensions' with the provided tolerance or the default one.
    """

    DEFAULT_TOLERANCE = 1e-9

    def run(self):
        if not isinstance(self.inputs.dataset, dtypes.Dataset):
            raise TypeError(
                f"'dataset' input should be an instance of {dtypes.Dataset}. Got {type(self.inputs.dataset)}"
            )

        dataset = self.inputs.dataset.dataset
        if not isinstance(dataset, dtypes.ImageDataset):
            raise TypeError(
                f"self.inputs.dataset is expected to be an instance of {dtypes.ImageDataset}. Get {type(dataset)}"
            )

        fscan_parameters = fscan_get_dimensions(dataset)

        dims = self._handle_dims(
            fscan_parameters[1] if fscan_parameters else None,
            dataset.metadata_dict,
            user_input=self._get_dimensions_from_default_inputs(),
        )
        is_zigzag = self._handle_is_zigzag(
            fscan_parameters[0] if fscan_parameters else None,
            user_input=self.get_input_value("is_zigzag", None),
        )

        assert_dimensions_ok(dataset, dims.values())

        if is_zigzag:
            reorder_frames_of_zigzag_scan(dims, dataset)

        # Reshape the dataset with the new dimensions

        dataset.dims = dims
        dataset.reshape_data()
        self.outputs.dataset = dtypes.Dataset(
            dataset=dataset,
            indices=self.inputs.dataset.indices,
            bg_indices=self.inputs.dataset.bg_indices,
            bg_dataset=self.inputs.dataset.bg_dataset,
        )

    def _get_dimensions_from_default_inputs(self) -> AcquisitionDims | None:

        raw_dims = self.get_input_value("dims", None)

        if raw_dims is None:
            return None

        try:
            return AcquisitionDims.from_dict(raw_dims)
        except ValueError as e:
            # TODO: Should we really silence the error here?
            _logger.error(f"Encountered {e} when parsing default raw_dims: {raw_dims}")
            return None

    def _handle_is_zigzag(self, fscan_input: bool | None, user_input: bool | None):
        if user_input:
            _logger.debug("is_zigzag set by user")
            return user_input

        if fscan_input:
            _logger.debug("is_zigzag set by fscan")
            return fscan_input

        _logger.debug("Using default value (False) for is_zigzag")
        return False

    def _handle_dims(
        self,
        fscan_dims: dict[int, Dimension] | None,
        metadata_dict: dict,
        user_input: AcquisitionDims | None,
    ) -> AcquisitionDims:
        if user_input is not None:
            _logger.debug("dims set by user")
            return user_input

        if fscan_dims is not None:
            _logger.debug("dims set by fscan")
            return AcquisitionDims.from_dict(fscan_dims)

        _logger.debug("dims computed from metadata")
        return self._compute_dimensions_from_metadata(metadata_dict)

    def _compute_dimensions_from_metadata(
        self, metadata_dict: dict[str, numpy.ndarray]
    ) -> AcquisitionDims:

        tolerance = self.get_input_value("tolerance", self.DEFAULT_TOLERANCE)

        return find_dimensions_from_metadata(
            metadata_dict,
            tolerance,
        )


def assert_dimensions_ok(dataset: ImageDataset, dims: Iterable[Dimension]) -> None:

    error_msg = get_dimensions_error(dataset, dims)
    if error_msg:
        raise RuntimeError(error_msg)


def get_dimensions_error(
    dataset: ImageDataset, dims: Iterable[Dimension]
) -> str | None:

    shape = []

    # Check name, min and max
    for dimension in dims:

        shape.append(dimension.size)

        if dimension.name not in dataset.metadata_dict:
            return f"Dimension with name '{dimension.name}' is not in the metadata."
        metadata_min = numpy.min(dataset.metadata_dict[dimension.name])
        metadata_max = numpy.max(dataset.metadata_dict[dimension.name])
        rel_tol = (metadata_max - metadata_min) * REL_TOLERANCE_FOR_MIN_MAX_VALIDATION
        metadata_min -= rel_tol
        metadata_max += rel_tol

        if dimension.start > metadata_max or dimension.start < metadata_min:
            return f"Dimension with name '{dimension.name}' start value = {dimension.start} but this is outside the dimension range [{metadata_min} → {metadata_max}]."

        if dimension.stop > metadata_max or dimension.stop < metadata_min:
            return f"Dimension with name '{dimension.name}' stop value = {dimension.stop} but this is outside the dimension range [{metadata_min} → {metadata_max}]."

    if len(shape) == 0:
        return "None dimension are defined."

    dims_size = numpy.prod(shape)

    # Check size
    if dims_size != dataset.nframes:
        product_string = " x ".join([str(size) for size in shape])

        return f"Dimensions do not match number of frames → {product_string} ≠ {dataset.nframes}."

    return None
