from __future__ import annotations

from typing import Any

import numpy
from attr import dataclass
from matplotlib.colors import hsv_to_rgb
from silx.math.combo import min_max
from silx.utils.enum import Enum

from darfix.io.utils import create_nxdata_dict
from darfix.math import sturges_rules

from ..dtypes import AxisType
from .dataset import ImageDataset
from .utils import compute_hsv


class MomentType(Enum):
    COM = "Center of mass"
    FWHM = "FWHM"
    SKEWNESS = "Skewness"
    KURTOSIS = "Kurtosis"


class OrientationDistData:
    KEY_SCALE = 1000

    def __init__(
        self,
        dataset: ImageDataset,
        x_dimension: int,
        y_dimension: int,
    ) -> None:

        # automatic bins
        x_bins = sturges_rules(
            dataset.dims.get(x_dimension).size * numpy.prod(dataset.frame_shape)
        )
        y_bins = sturges_rules(
            dataset.dims.get(y_dimension).size * numpy.prod(dataset.frame_shape)
        )

        self.data, self.x_range, self.y_range = (
            compute_orientation_distribution_histogram(
                dataset, x_dimension, y_dimension, x_bins, y_bins
            )
        )

        self.x_bins = x_bins
        self.y_bins = y_bins
        self.x_label = dataset.dims.get(x_dimension).name
        self.y_label = dataset.dims.get(y_dimension).name

        x_data = numpy.linspace(-1, 1, self.KEY_SCALE)
        y_data = numpy.linspace(-1, 1, self.KEY_SCALE)
        x_mesh, y_mesh = numpy.meshgrid(x_data, y_data)
        self.rgb_key = hsv_to_rgb(compute_hsv(x_mesh, y_mesh))

    def origin(
        self,
        origin: AxisType,
    ) -> tuple[float, float]:
        if origin == "dims":
            return (self.x_range[0], self.y_range[0])
        elif origin == "center":
            return (
                -numpy.ptp(self.x_range) / 2,
                -numpy.ptp(self.y_range) / 2,
            )
        else:
            return (0, 0)

    def data_plot_scale(self) -> tuple[float, float]:
        return (
            numpy.ptp(self.x_range) / self.x_bins,
            numpy.ptp(self.y_range) / self.y_bins,
        )

    def rgb_key_plot_scale(self) -> tuple[float, float]:
        return (
            numpy.ptp(self.x_range) / self.KEY_SCALE,
            numpy.ptp(self.y_range) / self.KEY_SCALE,
        )

    def to_motor_coordinates(
        self,
        points_x: numpy.ndarray,
        points_y: numpy.ndarray,
        origin: AxisType,
    ) -> tuple[numpy.ndarray, numpy.ndarray]:
        """
        Given points_x, points_y in the 2D space of self.data, returns motor coordinates x, y
        """
        x_origin, y_origin = self.origin(origin)
        return (
            points_x * numpy.ptp(self.x_range) / (self.x_bins - 1) + x_origin,
            points_y * numpy.ptp(self.y_range) / (self.y_bins - 1) + y_origin,
        )


@dataclass
class OrientationDistImage:
    xlabel: str
    ylabel: str
    scale: tuple[float, float]
    origin: tuple[float, float]
    data: numpy.ndarray
    as_rgb: numpy.ndarray
    contours: dict


class MultiDimMomentType(Enum):
    """Moments that are only computed for datasets with multiple dimensions"""

    ORIENTATION_DIST = "Orientation distribution"
    MOSAICITY = "Mosaicity"


def get_axes(transformation: numpy.ndarray | None) -> tuple[
    tuple[numpy.ndarray, numpy.ndarray] | None,
    tuple[str, str] | None,
    tuple[str, str] | None,
]:
    if not transformation:
        return None, None, None

    axes = (transformation.yregular, transformation.xregular)
    axes_names = ("y", "x")
    axes_long_names = (transformation.label, transformation.label)

    return axes, axes_names, axes_long_names


def compute_normalized_component(component: numpy.ndarray):

    min_max_result = min_max(component)
    min_component = min_max_result.minimum
    max_component = min_max_result.maximum

    return 2 * (component - min_component) / (max_component - min_component) - 1


def compute_mosaicity(
    moments: dict[int, numpy.ndarray], x_dimension: int, y_dimension: int
):
    norm_center_of_mass_x = compute_normalized_component(moments[x_dimension][0])
    norm_center_of_mass_y = compute_normalized_component(moments[y_dimension][0])

    return hsv_to_rgb(compute_hsv(norm_center_of_mass_x, norm_center_of_mass_y))


def create_moment_nxdata_groups(
    parent: dict[str, Any],
    moment_data: numpy.ndarray,
    axes,
    axes_names,
    axes_long_names,
):

    for i, map_type in enumerate(MomentType.values()):
        parent[map_type] = create_nxdata_dict(
            moment_data[i],
            map_type,
            axes,
            axes_names,
            axes_long_names,
        )


def generate_grain_maps_nxdict(
    dataset: ImageDataset,
    mosaicity: numpy.ndarray | None,
    orientation_dist_image: OrientationDistImage | None,
) -> dict:
    moments = dataset.moments_dims
    axes, axes_names, axes_long_names = get_axes(dataset.transformation)

    nx = {
        "entry": {"@NX_class": "NXentry"},
        "@NX_class": "NXroot",
        "@default": "entry",
    }

    if mosaicity is not None:
        nx["entry"][MultiDimMomentType.MOSAICITY.value] = create_nxdata_dict(
            mosaicity,
            MultiDimMomentType.MOSAICITY.value,
            axes,
            axes_names,
            axes_long_names,
            rgba=True,
        )
        nx["entry"]["@default"] = MultiDimMomentType.MOSAICITY.value
    else:
        nx["entry"]["@default"] = MomentType.COM.value

    if orientation_dist_image is not None:
        nx["entry"][MultiDimMomentType.ORIENTATION_DIST.value] = {
            "key": {
                "image": orientation_dist_image.as_rgb,
                "data": orientation_dist_image.data,
                "origin": orientation_dist_image.origin,
                "scale": orientation_dist_image.scale,
                "xlabel": orientation_dist_image.xlabel,
                "ylabel": orientation_dist_image.ylabel,
                "image@interpretation": "rgba-image",
                "image@CLASS": "IMAGE",
            },
            "curves": orientation_dist_image.contours,
        }

    if dataset.dims.ndim <= 1:
        create_moment_nxdata_groups(
            nx["entry"],
            moments[0],
            axes,
            axes_names,
            axes_long_names,
        )
    else:
        for axis, dim in dataset.dims.items():
            nx["entry"][dim.name] = {"@NX_class": "NXcollection"}
            create_moment_nxdata_groups(
                nx["entry"][dim.name],
                moments[axis],
                axes,
                axes_names,
                axes_long_names,
            )

    return nx


def compute_orientation_distribution_histogram(
    dataset: ImageDataset,
    x_dimension: int,
    y_dimension: int,
    x_bins: int,
    y_bins: int,
) -> tuple[numpy.ndarray, tuple[float, float], tuple[float, float]]:
    """
    Computes the orientation distribution hostogram.

    Requires apply_moments to be called before.

    :returns: 2d histogram, x range, y range.

    """

    if len(dataset.moments_dims) == 0:
        raise ValueError("Moments should be computed before to use this function.")

    com_x = dataset.moments_dims[x_dimension][0].ravel()
    com_y = dataset.moments_dims[y_dimension][0].ravel()

    range_x = [numpy.nanmin(com_x), numpy.nanmax(com_x)]
    range_y = [numpy.nanmin(com_y), numpy.nanmax(com_y)]

    # Histogram in 2D
    orientation_distribution, _, _ = numpy.histogram2d(
        com_y,
        com_x,  # note: y first is in purpose : see numpy.histogram2d documentation
        weights=dataset.zsum().ravel(),  # We need to take into account pixel intensity
        bins=[y_bins, x_bins],
        range=[range_y, range_x],
    )

    return orientation_distribution, range_x, range_y
