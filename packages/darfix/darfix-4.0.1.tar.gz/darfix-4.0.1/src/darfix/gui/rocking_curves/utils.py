from __future__ import annotations

import numpy
from silx.image.marchingsquares import find_contours


def compute_contours(image: numpy.ndarray) -> list[numpy.ndarray]:
    polygons = []
    for i in numpy.linspace(numpy.min(image), numpy.max(image), 10):
        polygons.extend(find_contours(image, i))

    return polygons
