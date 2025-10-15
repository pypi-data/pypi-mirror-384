from __future__ import annotations

import numpy
from silx.gui.plot import Plot2D
from silx.utils.enum import Enum as _Enum

from ...core.grainplot import MomentType
from ...core.grainplot import MultiDimMomentType
from ...core.transformation import Transformation


class MapType(_Enum):
    """
    Different maps to show
    """

    COM = MomentType.COM.value
    FWHM = MomentType.FWHM.value
    SKEWNESS = MomentType.SKEWNESS.value
    KURTOSIS = MomentType.KURTOSIS.value
    MOSAICITY = MultiDimMomentType.MOSAICITY.value


def add_image_with_transformation(
    plot: Plot2D, image: numpy.ndarray, transformation: Transformation | None = None
):
    if transformation is None:
        plot.addImage(image, xlabel="pixels", ylabel="pixels")
        return

    if transformation.rotate:
        image = numpy.rot90(image, 3)
    plot.addImage(
        image,
        origin=transformation.origin,
        scale=transformation.scale,
        xlabel=transformation.label,
        ylabel=transformation.label,
    )
