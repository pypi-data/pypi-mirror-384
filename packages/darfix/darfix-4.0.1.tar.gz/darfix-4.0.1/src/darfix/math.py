from typing import Tuple

import numpy
from scipy.stats import multivariate_normal

Vector3D = Tuple[float, float, float]


def sturges_rules(n: int) -> int:
    """https://en.wikipedia.org/wiki/Sturges%27s_rule"""
    return int(numpy.ceil(1 + numpy.log2(n)))


def gaussian(
    x: numpy.ndarray, amplitude: float, x0: float, std_dev: float, background: float
):
    """
    Gaussian function (https://en.wikipedia.org/wiki/Gaussian_function) with background

    :param x: value where to evaluate
    :param amplitude: peak height
    :param x0: peak center
    :param std_dev: standard deviation
    :param background: lowest value of the curve (value of the limits)

    :returns: result of the function on x
    :rtype: float
    """
    return background + amplitude * numpy.exp(
        -numpy.power(x - x0, 2) / (2 * numpy.power(std_dev, 2))
    )


def bivariate_gaussian(
    X: numpy.ndarray,
    x0_0: float,
    x1_0: float,
    sigma_x0: float,
    sigma_x1: float,
    amplitude: float,
    correlation: float = 0,
    background: float = 0,
):
    """
    Bivariate case of the gaussian function with background (https://en.wikipedia.org/wiki/Multivariate_normal_distribution#Bivariate_case)

    If correlation is set to 0 (default), this is simply a 2D gaussian

    :param x: value where to evaluate
    """
    x0, x1 = X

    return background + amplitude * numpy.exp(
        -0.5
        / (1 - correlation**2)
        * (
            ((x0 - x0_0) / sigma_x0) ** 2
            + ((x1 - x1_0) / sigma_x1) ** 2
            - 2 * correlation * (x0 - x0_0) * (x1 - x1_0) / sigma_x0 / sigma_x1
        )
    )


def trivariate_gaussian(
    X: numpy.ndarray,
    x0_0: float,
    x1_0: float,
    x2_0: float,
    sigma_x0: float,
    sigma_x1: float,
    sigma_x2: float,
    c10: float,
    c12: float,
    c20: float,
    amplitude: float,
    background: float = 0,
):
    """
    Trivariate case of the gaussian function with background (https://en.wikipedia.org/wiki/Multivariate_normal_distribution#Density_function)

    :param X: stack of N vectors of shape (3, N)
    :param x0_0: mean along axis 0
    :param x1_0: mean along axis 1
    :param x2_0: mean along axis 2
    :param sigma_x0: standard deviation along axis 0
    :param sigma_x1: standard deviation along axis 1
    :param sigma_x2: standard deviation along axis 2
    :param c10: cross-correlation factor between axis 0 and axis 1
    :param c12: cross-correlation factor between axis 1 and axis 2
    :param c02: cross-correlation factor between axis 0 and axis 2
    :param amplitude:
    :param background:
    """
    assert X.shape[0] == 3

    covariance_matrix = numpy.array(
        [
            [sigma_x0**2, c10 * sigma_x0 * sigma_x1, c20 * sigma_x0 * sigma_x2],
            [c10 * sigma_x0 * sigma_x1, sigma_x1**2, c12 * sigma_x1 * sigma_x2],
            [c20 * sigma_x0 * sigma_x2, c12 * sigma_x1 * sigma_x2, sigma_x2**2],
        ]
    )

    X0 = numpy.array([x0_0, x1_0, x2_0])

    return background + amplitude * multivariate_normal.pdf(
        X.T, X0, covariance_matrix, allow_singular=True
    )
