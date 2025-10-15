from __future__ import annotations

import logging
from typing import Literal
from typing import Tuple

import numpy
from scipy.optimize import curve_fit

import darfix

from ..math import bivariate_gaussian
from ..math import gaussian
from ..math import trivariate_gaussian

FitMethod = Literal["trf", "lm", "dogbox"]

_ZERO_SUM_RELATIVE_TOLERANCE = 1e-3
""" Relative tolerance used to check if the sum of values equals 0. Skips fit if it is the case."""

_BOUNDS_TOLERANCE = 1e-3
""" Absolute tolerance for to set bounds of fit parameters. The bounds will be set to (min - tol, max + tol) whenever possible."""

_logger = logging.getLogger(__file__)


def fit_1d_rocking_curve(
    y_values: Tuple[numpy.ndarray, numpy.ndarray | None],
    x_values: list | numpy.ndarray | None = None,
    num_points: int | None = None,
    int_thresh: int | None = None,
    method: FitMethod | None = None,
) -> Tuple[numpy.ndarray, numpy.ndarray | list]:
    """
    Fit rocking curve.

    :param y_values: the first element is the dependent data and the second element are
        the moments to use as starting values for the fit
    :param values: The independent variable where the data is measured, optional
    :param num_points: Number of points to evaluate the data on, optional
    :param nt_thresh: Intensity threshold. If not None, only the rocking curves with
        higher ptp (range of values) are fitted, others are assumed to be noise and not important
        data. This parameter is used to accelerate the fit. Optional.

    :returns: If curve was fitted, the fitted curve, else item[0]
    """
    if method is None:
        method = "trf"
    y, moments = y_values
    y = numpy.asanyarray(y)
    x = numpy.asanyarray(x_values) if x_values is not None else numpy.arange(len(y))
    ptp_y = numpy.ptp(y)
    if int_thresh is not None and ptp_y < int_thresh:
        return y, [0, x[0], 0, min(y)]
    if moments is not None:
        p0 = [ptp_y, moments[0], moments[1], min(y)]
    else:
        _sum = sum(y)
        if _sum > 0:
            mean = sum(x * y) / sum(y)
            sigma = numpy.sqrt(sum(y * (x - mean) ** 2) / sum(y))
        else:
            mean, sigma = numpy.nan, numpy.nan
        p0 = [ptp_y, mean, sigma, min(y)]
    if numpy.isnan(mean) or numpy.isnan(sigma):
        return y, p0
    if numpy.isclose(p0[2], 0):
        return y, p0
    if num_points is None:
        num_points = len(y)
    epsilon = 1e-2
    bounds = numpy.array(
        [
            [min(ptp_y, min(y)) - epsilon, min(x) - epsilon, 0, -numpy.inf],
            [max(max(y), ptp_y) + epsilon, max(x) + epsilon, numpy.inf, numpy.inf],
        ]
    )

    p0 = numpy.array(p0)
    p0[p0 < bounds[0]] = bounds[0][p0 < bounds[0]]
    p0[p0 > bounds[1]] = bounds[1][p0 > bounds[1]]
    try:
        pars, cov = curve_fit(
            f=gaussian, xdata=x, ydata=y, p0=p0, bounds=bounds, method=method
        )
        y_gauss = gaussian(numpy.linspace(x[0], x[-1], num_points), *pars)
        y_gauss[numpy.isnan(y_gauss)] = 0
        y_gauss[y_gauss < 0] = 0
        pars[2] *= darfix.config.FWHM_VAL
        return y_gauss, pars
    except RuntimeError:
        p0[2] *= darfix.config.FWHM_VAL
        return y, p0
    except ValueError:
        p0[2] *= darfix.config.FWHM_VAL
        return y, p0


def _get_2d_bounds(
    method: FitMethod, x_values: numpy.array, min_y: float, max_y: float
):
    if method not in ("trf", "dogbox"):
        return (-numpy.inf, numpy.inf)

    min_x0, min_x1 = numpy.min(x_values, axis=1)
    max_x0, max_x1 = numpy.max(x_values, axis=1)

    return (
        [
            min_x0 - _BOUNDS_TOLERANCE,
            min_x1 - _BOUNDS_TOLERANCE,
            -numpy.inf,
            -numpy.inf,
            min_y - _BOUNDS_TOLERANCE,
            -1,
            -numpy.inf,
        ],
        [
            max_x0 + _BOUNDS_TOLERANCE,
            max_x1 + _BOUNDS_TOLERANCE,
            numpy.inf,
            numpy.inf,
            max_y + _BOUNDS_TOLERANCE,
            1,
            numpy.inf,
        ],
    )


def fit_2d_rocking_curve(
    y_values_and_moments: Tuple[numpy.ndarray, numpy.ndarray | None],
    x_values: list | numpy.ndarray,
    shape: Tuple[int, int],
    int_thresh: int | None = None,
    method: FitMethod | None = None,
) -> Tuple[numpy.ndarray, numpy.ndarray | list]:
    if method is None:
        method = "trf"
    y, moments = y_values_and_moments
    y = numpy.asanyarray(y)
    ptp_y = numpy.ptp(y)
    x_values = numpy.asanyarray(x_values)
    sum_y = sum(y)
    if numpy.isclose(sum_y, 0, rtol=_ZERO_SUM_RELATIVE_TOLERANCE):
        return y, [numpy.nan, numpy.nan, numpy.nan, numpy.nan, ptp_y, 0, 0]
    x0_0 = sum(x_values[0] * y) / sum_y
    x1_0 = sum(x_values[1] * y) / sum_y
    x0_alpha = numpy.sqrt(sum(y * (x_values[0] - x0_0) ** 2) / sum_y)
    x1_alpha = numpy.sqrt(sum(y * (x_values[1] - x1_0) ** 2) / sum_y)
    if (
        (int_thresh is not None and ptp_y < int_thresh)
        or x0_alpha == 0
        or x1_alpha == 0
    ):
        return y, [x0_0, x1_0, x0_alpha, x1_alpha, ptp_y, 0, 0]

    try:
        pars, cov = curve_fit(
            f=bivariate_gaussian,
            xdata=x_values,
            ydata=y,
            p0=[x0_0, x1_0, x0_alpha, x1_alpha, ptp_y, 0, 0],
            bounds=_get_2d_bounds(
                method, x_values, min_y=min(y.min(), ptp_y), max_y=max(y.max(), ptp_y)
            ),
            method=method,
        )
        # TODO: Shape is flipped for some reason
        x_gauss = x_values.reshape((2, shape[1], shape[0]))
        y_gauss = bivariate_gaussian(x_gauss, *pars)
        pars[2] *= darfix.config.FWHM_VAL
        pars[3] *= darfix.config.FWHM_VAL
        return y_gauss.ravel(), pars
    except RuntimeError:
        return y, [
            x0_0,
            x1_0,
            darfix.config.FWHM_VAL * x0_alpha,
            darfix.config.FWHM_VAL * x1_alpha,
            ptp_y,
            0,
            0,
        ]


def _get_3d_bounds(
    method: FitMethod, x_values: numpy.ndarray, min_y: float, max_y: float
):
    """
    Computes bounds for the curve fit of trivariate gaussian.

    The bounds are for the following parameters (in order):
        - x0_0
        - x1_0
        - x2_0
        - sigma_x0
        - sigma_x1
        - sigma_x2
        - c10
        - c12
        - c20
        - amplitude
        - background
    """
    if method == "lm":
        # `lm` cannot handle bounds: no point in calculating them
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html#scipy.optimize.least_squares
        return (-numpy.inf, numpy.inf)

    mins = numpy.min(x_values, axis=1) - _BOUNDS_TOLERANCE
    maxs = numpy.max(x_values, axis=1) + _BOUNDS_TOLERANCE

    return (
        [
            mins[0],
            mins[1],
            mins[2],
            -numpy.inf,
            -numpy.inf,
            -numpy.inf,
            -1,
            -1,
            -1,
            min_y - _BOUNDS_TOLERANCE,
            -numpy.inf,
        ],
        [
            maxs[0],
            maxs[1],
            maxs[2],
            numpy.inf,
            numpy.inf,
            numpy.inf,
            1,
            1,
            1,
            max_y + _BOUNDS_TOLERANCE,
            numpy.inf,
        ],
    )


def fit_3d_rocking_curve(
    y_values_and_moments: Tuple[numpy.ndarray, numpy.ndarray | None],
    x_values: numpy.ndarray,
    shape: Tuple[int, int, int],
    int_thresh: int | None = None,
    method: FitMethod | None = None,
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    if method is None:
        method = "trf"

    y, moments = y_values_and_moments
    ptp_y = numpy.ptp(y)
    sum_y = sum(y)

    default_params = [
        numpy.nan,
        numpy.nan,
        numpy.nan,
        numpy.nan,
        numpy.nan,
        numpy.nan,
        0,
        0,
        0,
        ptp_y,
        0,
    ]
    if numpy.isclose(sum_y, 0, rtol=_ZERO_SUM_RELATIVE_TOLERANCE):
        return y, default_params

    X0 = numpy.sum(x_values * y, axis=1) / sum_y
    X_sigma = numpy.sqrt(
        numpy.sum(y * (x_values - X0[:, numpy.newaxis]) ** 2, axis=1) / sum_y
    )

    default_params = [*X0, *(X_sigma * darfix.config.FWHM_VAL), 0, 0, 0, ptp_y, 0]
    if (int_thresh is not None and ptp_y < int_thresh) or numpy.any(X0 == 0):
        return y, default_params

    try:
        fit_params, cov = curve_fit(
            f=trivariate_gaussian,
            xdata=x_values,
            ydata=y,
            p0=[*X0, *X_sigma, 0, 0, 0, ptp_y, 0],
            method=method,
            bounds=_get_3d_bounds(
                method, x_values, min_y=min(y.min(), ptp_y), max_y=max(y.max(), ptp_y)
            ),
        )
    except (RuntimeError, ValueError) as e:
        _logger.warning(
            f"Encountered the following error while fitting rocking curves: '{e}'"
        )
        return y, default_params
    else:
        x_gauss = x_values.reshape((3, shape[2], shape[1], shape[0]))
        y_gauss = trivariate_gaussian(x_gauss, *fit_params)
        fit_params[3] *= darfix.config.FWHM_VAL
        fit_params[4] *= darfix.config.FWHM_VAL
        fit_params[5] *= darfix.config.FWHM_VAL
        return y_gauss.ravel(), fit_params
