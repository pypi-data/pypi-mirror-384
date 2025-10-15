import math

import numpy

TWO_PI = 2 * numpy.pi
SQRT_2 = math.sqrt(2)


class OperationAborted(Exception):
    """Raised when operation is aborted"""

    def __init__(self) -> None:
        super().__init__("Operation aborted.")


class NoDimensionsError(Exception):
    """Error raised when a method needing Darfix dimensions is called before the dimensions were found."""

    def __init__(self, method_name: str) -> None:
        super().__init__(
            f"{method_name} needs to have defined dimensions. Run `find_dimensions` before `{method_name}`."
        )


class TooManyDimensionsForRockingCurvesError(ValueError):
    def __init__(self) -> None:
        super().__init__(
            "Unsupported number of dimensions. Rocking curves only support 1D, 2D or 3D datasets."
        )


def wrapTo2pi(x):
    """
    Python implementation of Matlab method `wrapTo2pi`.
    Wraps angles in x, in radians, to the interval [0, 2*pi] such that 0 maps
    to 0 and 2*pi maps to 2*pi. In general, positive multiples of 2*pi map to
    2*pi and negative multiples of 2*pi map to 0.
    """
    xwrap = numpy.remainder(x - numpy.pi, TWO_PI)
    mask = numpy.abs(xwrap) > numpy.pi
    xwrap[mask] -= TWO_PI * numpy.sign(xwrap[mask])
    return xwrap + numpy.pi


def compute_hsv(x_data: numpy.ndarray, y_data: numpy.ndarray):
    data = numpy.arctan2(-y_data, -x_data)

    hue = wrapTo2pi(data) / TWO_PI
    saturation = numpy.sqrt(numpy.power(x_data, 2) + numpy.power(y_data, 2)) / SQRT_2
    value = numpy.ones_like(x_data)

    # Display NaN values as black
    value[numpy.isnan(data)] = 0
    hue[numpy.isnan(data)] = 0
    saturation[numpy.isnan(data)] = 0

    return numpy.stack(
        (
            hue,
            saturation,
            value,
        ),
        axis=2,
    )
