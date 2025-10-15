from __future__ import annotations

from typing import Tuple

import numpy

from ..dtypes import Dataset


def apply_shift(
    input_dataset: Dataset,
    shift: Tuple[float, float] | numpy.ndarray,
    selected_axis: int | None = None,
):
    if not isinstance(shift, numpy.ndarray):
        shift = numpy.array(shift)

    dataset = input_dataset.dataset
    indices = input_dataset.indices

    dataset.apply_shift(shift, axis=selected_axis, indices=indices)
