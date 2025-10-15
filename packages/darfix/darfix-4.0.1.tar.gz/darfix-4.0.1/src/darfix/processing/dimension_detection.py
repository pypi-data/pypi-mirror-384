import math
from typing import List
from typing import Sequence
from typing import Tuple


def find_linspace_parameters(
    values: Sequence[float], tolerance: float
) -> Tuple[int, float, float]:
    """
    Sets the unique values of the dimension. If the size of the dimension is fixed,
    it automatically sets the first size values, else it finds the unique values.

    :param array_like values: list of values.

    :param tolerance: Tolerance to find the unique values

    :returns linspace parameters: A tuple with dimension size, start and stop

    """
    unique_values = _find_unique_values(values, tolerance)

    return len(unique_values), values[0], values[-1]


def _find_unique_values(values: Sequence[float], tolerance: float) -> List[float]:
    """
    Function that compares the values passed as parameter and returns only the unique
    ones given the dimension's tolerance.

    :param array_like values: list of values to compare.

    :param tolerance: Tolerance to find the unique values

    :returns : An array with uniques values with right dimension size
    """
    unique_values = []

    for val in values:
        if not unique_values:
            unique_values.append(val)
        else:
            unique = True
            for unique_value in unique_values:
                if math.isclose(unique_value, val, rel_tol=tolerance):
                    unique = False
                    break
            if unique:
                unique_values.append(val)
    return unique_values
