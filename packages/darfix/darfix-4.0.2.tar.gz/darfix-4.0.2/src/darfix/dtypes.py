from __future__ import annotations

from typing import Any
from typing import List
from typing import Literal
from typing import Optional
from typing import Tuple
from typing import Union

import numpy

from darfix.core.dataset import ImageDataset

AxisAndValueIndices = Tuple[List[int], List[int]]

AxisType = Union[Literal["dims"], Literal["center"], None]


class Dataset:
    def __init__(
        self,
        dataset: ImageDataset,
        indices: Optional[numpy.ndarray] = None,
        bg_indices: Optional[numpy.ndarray] = None,
        bg_dataset: Optional[ImageDataset] = None,
    ):
        """Darfix dataset with indices and background

        :param dataset: Darfix dataset object that holds the image stack
        :param indices: Image stack indices to be taking into account. Usually set by the 'partition data' task. Defaults to None.
        :param bg_indices: Dark image stack indices to be taking into account. Usually set by the 'partition data' task. Defaults to None.
        :param bg_dataset: Darfix dataset object that holds the dark image stack. Defaults to None.
        """
        self.dataset = dataset
        self.indices = indices
        self.bg_indices = bg_indices
        self.bg_dataset = bg_dataset


class DatasetTypeError(TypeError):
    def __init__(self, wrong_dataset: Any):
        """Error raised when a dataset has not the expected Dataset type"""
        super().__init__(
            f"Dataset is expected to be an instance of {Dataset}. Got {type(wrong_dataset)}."
        )
