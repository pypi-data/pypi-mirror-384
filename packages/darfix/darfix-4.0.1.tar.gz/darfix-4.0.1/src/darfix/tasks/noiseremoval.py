from __future__ import annotations

import logging
import threading
from typing import Any

from ewokscore import TaskWithProgress
from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import MissingData
from ewokscore.model import BaseInputModel
from pydantic import ConfigDict
from pydantic import Field

from darfix.core.state_of_operation import Operation
from darfix.dtypes import Dataset

from ..core.noiseremoval import NoiseRemovalOperation
from ..core.noiseremoval import apply_noise_removal_operations
from ..core.noiseremoval import create_background_substraction_operation

_logger = logging.getLogger(__name__)


class Inputs(BaseInputModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    dataset: Dataset
    """ Input dataset containing a stack of images """
    operations: list[dict[str, Any]] | MissingData = Field(
        default=MISSING_DATA,
        examples=[
            [
                {"type": "THRESHOLD", "parameters": {"bottom": 10.0, "top": 1000.0}},
                {"type": "HP", "parameters": {"kernel_size": 3}},
            ]
        ],
        description="""List of noise removal operations to apply to the dataset. Empty list if not provided."

        Available operations :

        - 'Operation.THRESHOLD': Threshold operation. Parameters: 'bottom' (float) and 'top' (float). Keep value only if it is between bottom and top.
        - 'Operation.HP': Hot Pixel removal using median filter operation. Parameters: 'kernel_size' (int).
        - 'Operation.BS': Background subtraction operation. Parameters: 'method' ("mean" | "median") and 'background_type' ("Data" | "Unused data (after partition)" | "Dark data").
        - 'Operation.MASK': Mask removal operation. Parameters: 'mask' (numpy.ndarray 2D containing 0 and 1 where 0 indicates the pixels to be removed).
        """,
    )


class NoiseRemoval(
    TaskWithProgress,
    input_model=Inputs,
    output_names=["dataset"],
):
    """Apply a list of noise removal operations on a Darfix dataset."""

    def run(self):

        self.cancelEvent = threading.Event()

        input_dataset: Dataset = self.get_input_value("dataset")

        operations = []

        for operation in self.get_input_value("operations", []):
            operation = NoiseRemovalOperation(operation)
            if operation["type"] is Operation.BS:
                _logger.info("Computing background...")
                background_substraction_operation = (
                    create_background_substraction_operation(
                        input_dataset, **operation["parameters"]
                    )
                )
                operations.append(background_substraction_operation)
            else:
                operations.append(operation)

        apply_noise_removal_operations(
            input_dataset.dataset.as_array3d(input_dataset.indices),
            operations,
            self._is_cancelled,
            self._set_progress,
        )

        self.outputs.dataset = input_dataset

    def cancel(self) -> None:
        self.cancelEvent.set()

    def _is_cancelled(self) -> bool:
        return self.cancelEvent.is_set()

    def _set_progress(self, progress: int):
        self.progress = progress
