from typing import Sequence
from typing import Tuple
from typing import Union

import numpy


def unique(
    ar: Sequence, return_index: bool = False, **kw
) -> Union[Tuple[numpy.ndarray], numpy.ndarray]:
    """Returns the unique elements of an array while preserving their order.

    The signature of this function is the same as `numpy.unique`.
    """
    unique_values, unique_indices, *other_indices = numpy.unique(
        ar, return_index=True, **kw
    )

    idx = numpy.argsort(unique_indices)

    unique_values = unique_values[idx]
    if not return_index and not other_indices:
        return unique_values
    unique_indices = unique_indices[idx]
    if not other_indices:
        return unique_values, unique_indices
    other_indices = tuple(values[idx] for values in other_indices)
    if not return_index:
        return (unique_values,) + other_indices
    return (unique_values, unique_indices) + other_indices
