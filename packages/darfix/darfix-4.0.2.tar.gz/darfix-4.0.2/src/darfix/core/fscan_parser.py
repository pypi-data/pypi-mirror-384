from __future__ import annotations

import logging
from contextlib import contextmanager
from enum import Enum
from typing import Generator

import h5py
from silx.io.utils import h5py_read_dataset

from darfix.core.dataset import ImageDataset
from darfix.core.dimension import Dimension

_logger = logging.getLogger(__file__)

FSCAN_PARAMETERS = "instrument/fscan_parameters/"

FAST_MOTOR_MODE = "fast_motor_mode"

MOTOR_NAME = "motor"
MOTOR_NPOINTS = "npoints"
MOTOR_START_POS = "start_pos"
MOTOR_STEP_SIZE = "step_size"

SCAN_NAME = "scan_name"


class FScanMotorPrefix(Enum):
    PREFIX_2D_FAST = "fast_"
    PREFIX_2D_SLOW = "slow_"
    PREFIX_1D = ""


class OpenFscanError(Exception):
    def __init__(self, details: str):
        super().__init__(details)


@contextmanager
def _open_fscan_parameters(dataset: ImageDataset) -> Generator[h5py.File, None, None]:
    if dataset.metadata_url is None:
        raise OpenFscanError("Dataset has no metadata.")
    with h5py.File(dataset.metadata_url.file_path()) as h5file:
        scan_number = dataset.metadata_url.data_path().lstrip("/").split("/")[0]
        fscan_parameters = h5file.get(scan_number + "/" + FSCAN_PARAMETERS, None)
        if fscan_parameters is None or not isinstance(fscan_parameters, h5py.Group):
            raise OpenFscanError("fscan parameters group not found.")

        yield fscan_parameters


def fscan_get_dimensions(
    dataset: ImageDataset,
) -> tuple[bool, dict[int, Dimension]] | None:
    """
    :return fscan_parameters:  a tuple (is_zigzag, dimensions) or None if no fscan_parameters
    """
    try:
        with _open_fscan_parameters(dataset) as fscan_parameters:

            is_zig_zag = False

            fast_motor_mode = fscan_parameters.get(FAST_MOTOR_MODE, None)
            if fast_motor_mode is not None:
                is_zig_zag = h5py_read_dataset(fast_motor_mode) == "ZIGZAG"
            else:
                is_zig_zag = False
            if h5py_read_dataset(fscan_parameters[SCAN_NAME]) == "fscan":
                # 1D scan
                motor = _get_motor_dimension(
                    fscan_parameters, FScanMotorPrefix.PREFIX_1D
                )
                return is_zig_zag, {0: motor}

            if h5py_read_dataset(fscan_parameters[SCAN_NAME]) == "fscan2d":
                # 2D scan
                fast_motor = _get_motor_dimension(
                    fscan_parameters, FScanMotorPrefix.PREFIX_2D_FAST
                )
                slow_motor = _get_motor_dimension(
                    fscan_parameters, FScanMotorPrefix.PREFIX_2D_SLOW
                )
                return is_zig_zag, {0: fast_motor, 1: slow_motor}

    except OpenFscanError as e:
        _logger.debug(e)

    return None


def _get_motor_dimension(
    parameters: h5py.Group, motor_prefix: FScanMotorPrefix
) -> Dimension:
    """
    Create Dimension object from fscan_parameter for the given motor prefix
    """
    name = h5py_read_dataset(parameters[motor_prefix.value + MOTOR_NAME])
    npoints = h5py_read_dataset(parameters[motor_prefix.value + MOTOR_NPOINTS])
    start_pos = h5py_read_dataset(parameters[motor_prefix.value + MOTOR_START_POS])
    step_size = h5py_read_dataset(parameters[motor_prefix.value + MOTOR_STEP_SIZE])

    return Dimension(
        name,
        npoints,
        start_pos,
        start_pos + step_size * npoints,
    )
