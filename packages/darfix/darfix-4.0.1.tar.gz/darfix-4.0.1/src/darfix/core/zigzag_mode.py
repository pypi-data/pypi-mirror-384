from __future__ import annotations

import numpy
import tqdm

from darfix.core.dataset import ImageDataset
from darfix.core.dimension import AcquisitionDims
from darfix.core.dimension import Dimension


def reorder_frames_of_zigzag_scan(
    dims: AcquisitionDims,
    dataset: ImageDataset,
) -> None:
    """
    Modify data to reorder frames

    Prequisites : user already check that ZIGZAG mode is used for acquisition.
    """

    if dims.ndim <= 1:
        raise NotImplementedError("Zigzag mode is not available for 1D dataset")

    indices = numpy.arange(dataset.nframes)

    # Take first dim -> fast motor
    fast_motor = tuple(dims.values())[0]

    assert isinstance(fast_motor, Dimension)

    # Reorder indices : In ZIGZAG mode fast motor is moving from start to stop then from stop to start value N times, with N corresponding to data.nframes // fast_motor.size.
    # When motor is moving backward, we reverse the indices of data to have the same order of frames as in normal acquisition mode.

    fast_motor_continuous_movement_count = dataset.nframes // fast_motor.size

    indices = indices.reshape(fast_motor_continuous_movement_count, fast_motor.size)
    indices[1::2] = indices[1::2, ::-1]
    indices = indices.flatten()

    for key in dataset.metadata_dict.keys():
        dataset.metadata_dict[key] = dataset.metadata_dict[key][indices]

    # quite the same but i use a loop and tqdm for better user experience
    for i, chunk in tqdm.tqdm(
        enumerate(
            numpy.split(dataset.as_array3d(), fast_motor_continuous_movement_count)
        ),
        "reorder frames for zigzag scan...",
        fast_motor_continuous_movement_count,
    ):
        if i % 2 == 0:
            continue
        chunk[:] = chunk[::-1]
