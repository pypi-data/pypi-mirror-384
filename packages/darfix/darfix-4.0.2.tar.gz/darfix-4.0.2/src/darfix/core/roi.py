from __future__ import annotations

from typing import Tuple
from typing import Union

import numpy

TwoDVector = Union[numpy.ndarray, Tuple[float, float]]


def apply_2D_ROI(
    img: numpy.ndarray,
    origin: TwoDVector | None = None,
    size: TwoDVector | None = None,
    center: TwoDVector | None = None,
) -> numpy.ndarray:
    """Function that computes a ROI at an image.

    :param array_like img: Image
    :param origin: Origin of the roi
    :param 2d-vector size: [Height, Width] of the roi.
    :param center: Center of the roi
    :raises: AssertionError, ValueError
    """

    assert size is not None, "The size of the roi must be given"

    img = numpy.asanyarray(img)

    if origin is not None:
        assert all(i >= 0 for i in origin) and all(
            j < img.shape[i] for i, j in enumerate(origin)
        ), "Origin must be a valid pixel"
        origin = numpy.array(origin)
        size = numpy.array(size)
        points = numpy.ceil([origin, origin + size]).astype(int)
        points[1] = numpy.minimum(points[1], img.shape)
    elif center is not None:
        assert all(i >= 0 for i in center) and all(
            j < img.shape[i] for i, j in enumerate(center)
        ), "Center must be a valid pixel"
        center = numpy.array(center)
        size = numpy.array(size) * 0.5
        # Compute points and ceil in case of decimal
        points = numpy.ceil([center - size, center + size]).astype(int)
        # Check lower and upper bounds
        points[points < 0] = 0
        points[1] = numpy.minimum(points[1], img.shape)
    else:
        raise ValueError("Origin or center expected")
    return img[points[0, 0] : points[1, 0], points[0, 1] : points[1, 1]]


def apply_3D_ROI(
    data: numpy.ndarray,
    origin: TwoDVector | None = None,
    size: TwoDVector | None = None,
    center: TwoDVector | None = None,
) -> numpy.ndarray:
    """Function that computes the ROI of each image in stack of images.

    :param array_like data: The stack of images
    :param origin: Origin of the roi
    :param 2d-vector size: [Height, Width] of the roi.
    :param center: Center of the roi
    :raises: AssertionError, ValueError
    """
    assert size is not None, "The size of the roi must be given"

    data = numpy.asanyarray(data)

    if origin is not None:
        assert all(i >= 0 for i in origin) and all(
            j < data[0].shape[i] for i, j in enumerate(origin)
        ), "Origin must be a valid pixel"
        origin = numpy.array(origin)
        size = numpy.array(size)
        points = numpy.ceil([origin, origin + size]).astype(int)
        points[1] = numpy.minimum(points[1], data[0].shape)
    elif center is not None:
        assert all(i >= 0 for i in center) and all(
            j < data[0].shape[i] for i, j in enumerate(center)
        ), "Center must be a valid pixel"
        center = numpy.array(center)
        size = numpy.array(size) * 0.5
        # Compute points and ceil in case of decimal
        points = numpy.ceil([center - size, center + size]).astype(int)
        # Check lower and upper bounds
        points[points < 0] = 0
        points[1] = numpy.minimum(points[1], data[0].shape)
    else:
        raise ValueError("Origin or center expected")
    return data[:, points[0, 0] : points[1, 0], points[0, 1] : points[1, 1]]


def clampROI(
    roi_origin: tuple[float, float],
    roi_size: tuple[float, float],
    frame_origin: tuple[float, float],
    frame_size: tuple[int, int],
) -> tuple[tuple[float, float], tuple[int, int]]:
    """
    Clamp given roi to the given frame. Returns origin and size of the clamped roi.

    The 'origin' of both the 'frame' and the 'roi' refers to the locations of the corner with the smallest coordinates.
    """
    roi_origin_x, roi_origin_y = roi_origin
    roi_width, roi_height = roi_size

    frame_origin_x, frame_center_y = frame_origin
    frame_width, frame_height = frame_size

    # Calculate the effective frame boundaries
    frame_min_x = frame_origin_x
    frame_max_x = frame_origin_x + frame_width
    frame_min_y = frame_center_y
    frame_max_y = frame_center_y + frame_height

    # Calculate the effective ROI boundaries
    roi_min_x = roi_origin_x
    roi_max_x = roi_origin_x + roi_width
    roi_min_y = roi_origin_y
    roi_max_y = roi_origin_y + roi_height

    if (frame_min_x > roi_min_x and frame_min_y > roi_min_y) and (
        frame_max_x < roi_max_x and frame_max_y < roi_max_y
    ):
        # if the frame is fully included in the ROI
        # update ROI to match frame shape
        return (frame_origin, frame_size)
    elif (frame_min_x < roi_min_x and frame_min_y < roi_min_y) and (
        frame_max_x > roi_max_x and frame_max_y > roi_max_y
    ):
        # if the roi is fully included in the frame
        return roi_origin, roi_size
    else:
        # in case of intersection
        new_roi_min_x = max(frame_min_x, roi_min_x)
        new_roi_max_x = min(frame_max_x, roi_max_x)
        new_roi_min_y = max(frame_min_y, roi_min_y)
        new_roi_max_y = min(frame_max_y, roi_max_y)

        new_roi_origin = (new_roi_min_x, new_roi_min_y)
        new_roi_size = (
            abs(new_roi_max_x - new_roi_min_x),
            abs(new_roi_max_y - new_roi_min_y),
        )
        return new_roi_origin, new_roi_size
