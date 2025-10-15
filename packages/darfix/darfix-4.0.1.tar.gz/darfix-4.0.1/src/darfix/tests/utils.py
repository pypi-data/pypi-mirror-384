from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

import h5py
import numpy
from ewoksutils.import_utils import qualname
from silx.io.dictdump import dicttoh5
from silx.io.dictdump import dicttonx
from silx.io.url import DataUrl
from silx.resources import ExternalResources

from darfix.core.dataset import ImageDataset

utilstest = ExternalResources(
    project="darfix",
    url_base="http://www.edna-site.org/pub/darfix/testimages",
    env_key="DATA_KEY",
    timeout=60,
)


def createHDF5Dataset(
    data: numpy.ndarray, metadata_dict: dict = None, output_file=None
):
    if metadata_dict is None:
        metadata_dict = {}
    if output_file is None:
        output_file = os.path.join(str(tempfile.mkdtemp()), "darfix_dataset.hdf5")
    dicttoh5(metadata_dict, output_file, h5path="1.1/instrument/positioners")
    with h5py.File(output_file, mode="a") as h5f:
        h5f["1.1/instrument/detector/data"] = data
    dataset = ImageDataset(
        _dir=os.path.dirname(output_file),
        detector_url=DataUrl(
            file_path=output_file,
            data_path="1.1/instrument/detector/data",
            scheme="silx",
        ),
        metadata_url=DataUrl(
            file_path=output_file,
            data_path="1.1/instrument/positioners",
            scheme="silx",
        ),
    )
    return dataset


def createHDF5Dataset1D(data: numpy.ndarray, output_file=None) -> ImageDataset:
    """
    Creates an ImageDataset with `data` inside and a single moving motor in the associated metadata (1D)

    :param data: 3D numpy array (N_motor_steps, N_pixels_x, N_pixels_y)
    :param output_file: Name of the output HDF5 file where the data will be saved. If None (default), the file will be saved in a temporary folder
    """
    assert data.ndim == 3

    N_frames = data.shape[0]
    metadata_dict = {"motor1": numpy.arange(N_frames)}

    return createHDF5Dataset(data, metadata_dict, output_file)


def createHDF5Dataset2D(data: numpy.ndarray, output_file=None) -> ImageDataset:
    """
    Creates an ImageDataset with `data` inside and a two moving motors in the associated metadata (2D)

    :param data: 4D dataset (N_motor1_steps, N_motor2_steps, N_pixels_x, N_pixels_y)
    :param output_file: Name of the output HDF5 file where the data will be saved. If None (default), the file will be saved in a temporary folder
    """
    assert data.ndim == 4

    N_motor1 = data.shape[0]
    N_motor2 = data.shape[1]
    N_frames = N_motor1 * N_motor2
    motor_1 = numpy.empty((N_motor1, N_motor2))
    motor_2 = numpy.empty((N_motor1, N_motor2))
    for i in range(N_motor1):
        motor_1[i] = numpy.arange(N_motor2)
    for j in range(N_motor2):
        motor_2[:, j] = numpy.arange(N_motor1)
    metadata_dict = {"motor1": motor_1.flatten(), "motor2": motor_2.flatten()}

    data = data.reshape((N_frames, *data.shape[2:]))

    return createHDF5Dataset(data, metadata_dict, output_file)


def createHDF5Dataset3D(data: numpy.ndarray, output_file=None) -> ImageDataset:
    """
    Creates an ImageDataset with `data` inside and a three moving motors in the associated metadata (3D)

    :param data: 5D dataset (N_motor1_steps, N_motor2_steps, N_motor3_steps, N_pixels_x, N_pixels_y)
    :param output_file: Name of the output HDF5 file where the data will be saved. If None (default), the file will be saved in a temporary folder
    """
    assert data.ndim == 5

    N_motor1, N_motor2, N_motor3 = data.shape[:3]
    N_frames = N_motor1 * N_motor2 * N_motor3
    motor_1 = numpy.empty((N_motor1, N_motor2, N_motor3))
    motor_2 = numpy.empty((N_motor1, N_motor2, N_motor3))
    motor_3 = numpy.empty((N_motor1, N_motor2, N_motor3))

    motor_1[:, :, :] = numpy.arange(N_motor1).reshape(N_motor1, 1, 1)
    motor_2[:, :, :] = numpy.arange(N_motor2).reshape(1, N_motor2, 1)
    motor_3[:, :, :] = numpy.arange(N_motor3).reshape(1, 1, N_motor3)
    metadata_dict = {
        "motor1": motor_1.flatten(),
        "motor2": motor_2.flatten(),
        "motor_3": motor_3.flatten(),
    }

    data = data.reshape((N_frames, *data.shape[-2:]))

    return createHDF5Dataset(data, metadata_dict, output_file)


def createRandomHDF5Dataset(
    dims,
    nb_data_frames=20,
    output_file=None,
    num_dims=3,
    metadata=False,
):
    """Simple creation of a dataset in output_file with the requested number of data
    files and dark files.

    :param tuple of int dims: dimensions of the files.
    :param int nb_data_frames: Number of data files to create.
    :param str or None output_file: output HDF5 file
    :param int num_dims: number of dimensions of the dataset

    :return :class:`Dataset`: generated instance of :class:`Dataset`
    """
    if not isinstance(dims, tuple) and len(dims) == 2:
        raise TypeError("dims should be a tuple of two elements")
    if not isinstance(nb_data_frames, int):
        raise TypeError(
            f"nb_data_frames ({nb_data_frames}) should be an int. Get {type(nb_data_frames)} instead"
        )
    if not isinstance(output_file, (type(None), str)):
        raise TypeError(
            f"output_file shuld be none or a string. Get {type(output_file)} instead"
        )

    if output_file is None:
        output_file = os.path.join(str(tempfile.mkdtemp()), "darfix_dataset.hdf5")

    metadata_dict = {}
    if metadata:
        metadata_dict["obx"] = [numpy.random.rand(1)[0]] * nb_data_frames
        metadata_dict["mainx"] = [numpy.random.rand(1)[0]] * nb_data_frames
        metadata_dict["ffz"] = [numpy.random.rand(1)[0]] * nb_data_frames
        metadata_dict["y"] = [numpy.random.rand(1)[0]] * nb_data_frames

        # comes from createRandomEDFDataset (legacy and remove in 4.0). Don't know why those
        # values are making sense...
        a = sorted(numpy.random.rand(2))
        b = [numpy.random.rand()] * numpy.array([1, 1.2, 1.4, 1.6, 1.8])
        c = sorted(numpy.random.rand(2))
        metadata_dict["m"] = [b[i % 5] for i in range(nb_data_frames)]
        if num_dims > 1:
            metadata_dict["z"] = [
                a[int((i > 4 and i < 10) or i > 14)] for i in range(nb_data_frames)
            ]
        metadata_dict["obpitch"] = [c[int(i > 9)] for i in range(nb_data_frames)]

    data = numpy.random.random((nb_data_frames, *dims))
    dicttoh5(metadata_dict, output_file, h5path="1.1/instrument/positioners")
    with h5py.File(output_file, mode="a") as h5f:
        h5f["1.1/instrument/detector/data"] = data
    assert os.path.exists(output_file)

    dataset = ImageDataset(
        _dir=os.path.dirname(output_file),
        detector_url=DataUrl(
            file_path=output_file,
            data_path="1.1/instrument/detector/data",
            scheme="silx",
        ),
        metadata_url=DataUrl(
            file_path=output_file,
            data_path="1.1/instrument/positioners",
            scheme="silx",
        ),
    )
    return dataset


def createDataset(
    data: numpy.ndarray, metadata_dict: dict = None, _dir: str | None = None
) -> ImageDataset:
    assert len(data) > 0
    if _dir is None:
        _dir = tempfile.mkdtemp()

    dir = Path(_dir)
    output_file = dir / "darfix_dataset.h5"
    return createHDF5Dataset(data, metadata_dict, output_file)


def create_scans(
    file_path: str,
    n_scan: int = 3,
    detector_path=r"{scan}/measurement/my_detector",
    metadata_path=r"{scan}/instrument/positioners",
):
    """
    create 'n_scan' scans with a detector like dataset and a 'positioners' groups containing motor like datasets

    warning: one of the dataset (delta) has an incoherent number of points (2 instead of 4). This is done on purpose
    to check behavior with this use case.
    """
    raw_detector_dataset = numpy.linspace(0, 5, 100 * 100 * 4).reshape(4, 100, 100)
    positioners_metadata = {
        "alpha": 1.0,
        "beta": numpy.arange(4, dtype=numpy.float32),
        "gamma": numpy.linspace(68, 70, 4, dtype=numpy.uint8),
        "delta": numpy.arange(2, dtype=numpy.int16),
    }

    for i in range(1, n_scan + 1):
        with h5py.File(file_path, mode="a") as h5f:
            h5f[detector_path.format(scan=f"{i}.1")] = raw_detector_dataset

        dicttonx(
            positioners_metadata,
            h5file=file_path,
            h5path=metadata_path.format(scan=f"{i}.1"),
            mode="a",
        )


def generate_ewoks_task_inputs(task_class, **kwargs) -> List[Dict[str, Any]]:
    task_identifier = qualname(task_class)

    return [
        {"task_identifier": task_identifier, "name": name, "value": value}
        for name, value in kwargs.items()
    ]


N_FRAMES_DIM0 = 10


def create_1d_dataset(dir, motor1, motor2):
    n_frames = N_FRAMES_DIM0
    dims = (n_frames, 100, 100)
    data = numpy.zeros(dims, dtype=numpy.float64)

    for i in range(n_frames):
        data[i] = i
    metadata_dict = {
        "mainx": numpy.ones(N_FRAMES_DIM0) * 0.5,
        motor1: numpy.ones(N_FRAMES_DIM0) * 0.2,
        motor2: numpy.arange(N_FRAMES_DIM0),
    }

    return createDataset(data, metadata_dict, dir)


def create_dataset_for_RSM(dir):
    """Create a dataset with suitable motor names to test RSM tasks"""
    return create_1d_dataset(dir, motor1="ffz", motor2="diffry")


def create_2_motors_metadata(
    slow_npoints: int, fast_npoints: int
) -> dict[str, numpy.ndarray]:
    """
    Create random metadata for 2 motors slow anf fast with
    """
    return {
        "slow": numpy.repeat(numpy.random.rand(slow_npoints), fast_npoints),
        "fast": numpy.tile(numpy.random.rand(fast_npoints), slow_npoints),
    }


def create_3_motors_metadata(
    slow_name: str,
    fast_name: str,
    very_fast_name: str,
    slow_npoints: int,
    fast_npoints: int,
    very_fast_npoints: int,
) -> dict[str, numpy.ndarray]:
    """
    Create random metadata for 2 motors slow anf fast with
    """
    return {
        slow_name: numpy.repeat(
            numpy.random.rand(slow_npoints), very_fast_npoints * fast_npoints
        ),
        fast_name: numpy.tile(
            numpy.repeat(numpy.random.rand(fast_npoints), slow_npoints),
            very_fast_npoints,
        ),
        very_fast_name: numpy.tile(
            numpy.random.rand(very_fast_npoints), slow_npoints * fast_npoints
        ),
        "mainx": 1,
        "obx": 1,
    }


def _3motors_dataset_args():
    """ "
    Creating random dataset with specific metadata.
    """
    dims = (20, 100, 100)
    data = numpy.zeros(dims)
    background = numpy.random.random(dims) * 100
    idxs = [0, 2, 4]
    data[idxs] += background[idxs]
    return data, create_3_motors_metadata("obpitch", "z", "m", 2, 2, 5)


def create_3motors_dataset(dir):
    """Create a dataset with 3 motors"""
    return createDataset(
        *_3motors_dataset_args(),
        _dir=str(dir) if dir else None,
    )
