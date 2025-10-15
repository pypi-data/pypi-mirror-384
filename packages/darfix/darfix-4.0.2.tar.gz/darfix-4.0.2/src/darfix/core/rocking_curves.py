from __future__ import annotations

import multiprocessing
from functools import partial
from multiprocessing import Pool
from typing import Generator
from typing import List
from typing import Sequence
from typing import Tuple
from typing import Union

import numpy
import tqdm
from silx.utils.enum import Enum as _Enum

from ..io.utils import create_nxdata_dict
from ..processing.rocking_curves import FitMethod
from ..processing.rocking_curves import fit_1d_rocking_curve
from ..processing.rocking_curves import fit_2d_rocking_curve
from ..processing.rocking_curves import fit_3d_rocking_curve
from .utils import NoDimensionsError
from .utils import TooManyDimensionsForRockingCurvesError

Indices = Union[range, numpy.ndarray]


class Maps_1D(_Enum):
    """Names of the fitting parameters of the 1D fit result. Each result is a map of frame size."""

    AMPLITUDE = "Amplitude"
    FWHM = "FWHM"
    PEAK = "Peak position"
    BACKGROUND = "Background"


class Maps_2D(_Enum):
    """Names of the fitting parameters of the 2D fit result. Each result is a map of frame size."""

    AMPLITUDE = "Amplitude"
    PEAK_X = "Peak position first motor"
    PEAK_Y = "Peak position second motor"
    FWHM_X = "FWHM first motor"
    FWHM_Y = "FWHM second motor"
    BACKGROUND = "Background"
    CORRELATION = "Correlation"


class Maps_3D(_Enum):
    """Names of the fitting parameters of the 3D fit result. Each result is a map of frame size."""

    AMPLITUDE = "Amplitude"
    PEAK_X = "Peak position first motor"
    PEAK_Y = "Peak position second motor"
    PEAK_Z = "Peak position third motor"
    FWHM_X = "FWHM first motor"
    FWHM_Y = "FWHM second motor"
    FWHM_Z = "FWHM third motor"
    BACKGROUND = "Background"
    CORRELATION_XY = "Cross-correlation between first and second motors"
    CORRELATION_XZ = "Cross-correlation between first and third motors"
    CORRELATION_YZ = "Cross-correlation between second and third motors"


MAPS_1D: Tuple[Maps_1D] = Maps_1D.values()
MAPS_2D: Tuple[Maps_2D] = Maps_2D.values()
MAPS_3D: Tuple[Maps_3D] = Maps_3D.values()


def _rocking_curves_per_px(
    data: numpy.ndarray, moments: numpy.ndarray | None = None, indices=None
) -> (
    Generator[Tuple[numpy.ndarray, None], None, None]
    | Generator[Tuple[numpy.ndarray, numpy.ndarray], None, None]
):
    """
    Generator that returns the rocking curve for every pixel

    :param ndarray data: data to analyse
    :param moments: array of same shape as data with the moments values per pixel and image, optional
    :type moments: Union[None, ndarray]
    """
    for i in range(data.shape[1]):
        for j in range(data.shape[2]):
            if indices is None:
                new_data = data[:, i, j]
            else:
                new_data = numpy.zeros(data.shape[0])
                new_data[indices] = data[indices, i, j]
            if moments is not None:
                yield new_data, moments[:, i, j]
            yield new_data, None


def fit_1d_data(
    data: numpy.ndarray,
    moments: numpy.ndarray | None = None,
    values: List[numpy.ndarray] | numpy.ndarray | None = None,
    int_thresh: float = 15.0,
    method: FitMethod | None = None,
) -> tuple[numpy.ndarray, numpy.ndarray]:
    """Fit data in axis 0 of data"""

    rocking_curves_per_px = _rocking_curves_per_px(data, moments)
    cpus = multiprocessing.cpu_count()
    curves, maps = [], []
    with Pool(cpus - 1) as p:
        for curve, pars in tqdm.tqdm(
            p.imap(
                partial(
                    fit_1d_rocking_curve,
                    x_values=values,
                    int_thresh=int_thresh,
                    method=method,
                ),
                rocking_curves_per_px,
            ),
            total=data.shape[1] * data.shape[2],
        ):
            curves.append(list(curve))
            maps.append(list(pars))

    return numpy.array(curves).T.reshape(data.shape), numpy.array(maps).T.reshape(
        (len(MAPS_1D), data.shape[-2], data.shape[-1])
    )


def fit_2d_data(
    data: numpy.ndarray,
    values: List[numpy.ndarray] | numpy.ndarray,
    shape: Tuple[int, int],
    moments: numpy.ndarray | None = None,
    int_thresh: float | None = 15.0,
    indices: Indices | None = None,
    method: FitMethod | None = None,
) -> tuple[numpy.ndarray, numpy.ndarray]:
    """Fit data in axis 0 of data"""
    rocking_curves_per_px = _rocking_curves_per_px(data, moments, indices)
    curves, maps = [], []
    cpus = multiprocessing.cpu_count()
    with Pool(cpus - 1) as p:
        for curve, pars in tqdm.tqdm(
            p.imap(
                partial(
                    fit_2d_rocking_curve,
                    x_values=values,
                    shape=shape,
                    int_thresh=int_thresh,
                    method=method,
                ),
                rocking_curves_per_px,
            ),
            total=data.shape[-2] * data.shape[-1],
        ):
            curves.append(list(curve))
            maps.append(list(pars))

    curves = numpy.array(curves).T
    if indices is not None:
        curves = curves[indices]
        data_shape = data[indices].shape
    else:
        data_shape = data.shape

    return curves.reshape(data_shape), numpy.array(maps).T.reshape(
        (len(MAPS_2D), data.shape[-2], data.shape[-1])
    )


def fit_3d_data(
    data: numpy.ndarray,
    motor_values: Sequence[numpy.ndarray] | numpy.ndarray,
    shape: Tuple[int, int, int],
    moments: numpy.ndarray | None = None,
    int_thresh: float | None = 15.0,
    indices: Indices | None = None,
    method: FitMethod | None = None,
) -> tuple[numpy.ndarray, numpy.ndarray]:
    """Fit the rocking curves using a trivariate gaussian functions

    :param data: Stack of images (Nframes, Npx, Npy)
    :param motor_values: Values of the 3 motor positions. The order is (fast, mid, slow). Shape shoudl be (3, Nframes).
    :param shape: Number of steps in each motor direction. The order is (fast, mid, slow). The product of these number should equal Nframes.
    :param moments: Moments of the data to be used as starting point for the fit.
    :param int_thresh: Minimum intensity threshold. If the summed intensity is below this value, the frame will be skipped. Defaults to 15.0.
    :param indices: Frames for which the fit should be made. Defaults to None (all frames).
    :param method: Fit method. 'lm', 'trf' or 'dogbox'. Defaults to 'trf'.
    :returns: A tuple containing the fitted curves (Nframes, Npx, Npy) and the fit parameters (Nparams, Npx, Npy).
    """
    rocking_curves_per_px = _rocking_curves_per_px(data, moments, indices)
    if isinstance(motor_values, Sequence):
        motor_values = numpy.array(motor_values)
    if not isinstance(motor_values, numpy.ndarray):
        raise TypeError(
            f"motor_values should be a sequence or a numpy array. Got {type(motor_values)}"
        )

    curves, maps = [], []
    for rocking_curve in rocking_curves_per_px:
        curve, fit_params = fit_3d_rocking_curve(
            rocking_curve, motor_values, shape, int_thresh, method
        )
        curves.append(list(curve))
        maps.append(list(fit_params))

    # Arrays have dimensions (Npixels, Ncomponents): transpose to have the pixels as last dimension
    curves = numpy.array(curves).T
    maps = numpy.array(maps).T
    # And reshape to fit the data:
    # curves will be (Nframes, Npx, Npy)
    # maps will be (Nparams, Npx, Npy)
    if indices is not None:
        curves = curves[indices].reshape(data[indices].shape)
    else:
        curves = curves.reshape(data.shape)

    return curves, maps.reshape((len(MAPS_3D), data.shape[-2], data.shape[-1]))


def generate_rocking_curves_nxdict(
    dataset,  # ImageDataset. Cannot type due to circular import
    maps: numpy.ndarray,
    residuals: numpy.ndarray | None,
) -> dict:
    if not dataset.dims.ndim:
        raise NoDimensionsError("generate_rocking_curves_nxdict")
    entry = "entry"

    nx = {
        entry: {"@NX_class": "NXentry"},
        "@NX_class": "NXroot",
        "@default": entry,
    }

    if dataset.transformation:
        axes = [
            dataset.transformation.yregular,
            dataset.transformation.xregular,
        ]
        axes_names = ["y", "x"]
        axes_long_names = [
            dataset.transformation.label,
            dataset.transformation.label,
        ]
    else:
        axes = None
        axes_names = None
        axes_long_names = None

    if dataset.dims.ndim == 1:
        map_names = MAPS_1D
    elif dataset.dims.ndim == 2:
        map_names = MAPS_2D
    else:
        raise TooManyDimensionsForRockingCurvesError()

    for i, map_name in enumerate(map_names):
        signal = maps[i]
        nx[entry][map_name] = create_nxdata_dict(
            signal, map_name, axes, axes_names, axes_long_names
        )
    if residuals is not None:
        nx[entry]["Residuals"] = create_nxdata_dict(
            residuals, "Residuals", axes, axes_names, axes_long_names
        )
    nx[entry]["@default"] = Maps_1D.AMPLITUDE.value

    return nx


def compute_residuals(
    target_dataset,  # ImageDataset. Cannot type due to circular import
    original_dataset,  # ImageDataset. Cannot type due to circular import
    indices: numpy.ndarray | None,
):
    return numpy.sqrt(
        numpy.subtract(target_dataset.zsum(indices), original_dataset.zsum(indices))
        ** 2
    )
