import os

import h5py
import numpy
import pytest
from silx.io.url import DataUrl

import darfix.resources.tests
from darfix.core.dataset import ImageDataset
from darfix.core.dimension import AcquisitionDims
from darfix.core.dimension import Dimension
from darfix.dtypes import Dataset
from darfix.tasks.dimensiondefinition import get_dimensions_error
from darfix.tests.utils import createHDF5Dataset


def test_find_dimensions(dataset):
    """Tests the correct finding of the dimensions"""

    dataset.find_dimensions()
    assert dataset.dims.ndim == 3
    assert dataset.dims.get(0).name == "m"
    assert dataset.dims.get(1).name == "z"
    assert dataset.dims.get(2).name == "obpitch"


def test_find_dimension_silicon_111_reflection(tmp_path, resource_files):
    """
    Test 'find_dimension' with a bunch of motor position over a real use cases that used to bring troubles.
    """
    silicon_111_reflection_file = resource_files(darfix.resources.tests).joinpath(
        os.path.join("dimensions_definition", "silicon_111_reflection.h5")
    )

    raw_motor_values = {}
    with h5py.File(silicon_111_reflection_file, mode="r") as h5f:
        raw_motor_values["chi"] = h5f["positioners/chi"][()]
        raw_motor_values["mu"] = h5f["positioners/mu"][()]

    data_folder = tmp_path / "test_fitting"
    data_folder.mkdir()
    data_file_url = DataUrl(
        file_path=os.path.join(str(data_folder), "data.h5"),
        data_path="data",
        scheme="silx",
    )
    number_of_points = 1891
    with h5py.File(data_file_url.file_path(), mode="w") as h5f:
        h5f["data"] = numpy.random.random(number_of_points).reshape(
            number_of_points, 1, 1
        )

    dataset = Dataset(
        dataset=ImageDataset(
            detector_url=data_file_url.path(),
            metadata_url=DataUrl(
                file_path=str(silicon_111_reflection_file),
                data_path="positioners",
                scheme="silx",
            ).path(),
            _dir=None,
        )
    )
    image_dataset = dataset.dataset

    # with a tolerance of 10e-9 we won't find 1081 steps over 2 dimensions
    assert len(image_dataset.dims) == 0
    image_dataset.find_dimensions(tolerance=1e-9)
    assert len(image_dataset.dims) == 2
    assert (
        numpy.prod([val.size for val in image_dataset.dims.values()]) > number_of_points
    )

    image_dataset.find_dimensions(tolerance=1e-5)
    assert (
        numpy.prod([val.size for val in image_dataset.dims.values()])
        == number_of_points
    )
    for dim in image_dataset.dims.values():
        numpy.testing.assert_almost_equal(
            dim.start, min(raw_motor_values[dim.name]), decimal=3
        )
        numpy.testing.assert_almost_equal(
            dim.stop, max(raw_motor_values[dim.name]), decimal=3
        )


def test_find_dimension_NiTi_1PD_002_g411_420MPa_mosalayers_2x(
    tmp_path, resource_files
):
    """
    Test 'find_dimension' with a bunch of motor position over a real use cases that used to bring troubles.
    """
    dataset_file = resource_files(darfix.resources.tests).joinpath(
        os.path.join(
            "dimensions_definition", "NiTi_1PD_002_g411_420MPa_mosalayers_2x.h5"
        )
    )

    raw_motor_values = {}
    with h5py.File(dataset_file, mode="r") as h5f:
        raw_motor_values["chi"] = h5f["positioners/chi"][()]
        raw_motor_values["diffry"] = h5f["positioners/diffry"][()]
        raw_motor_values["difftz"] = h5f["positioners/difftz"][()]

    data_folder = tmp_path / "test_fitting"
    data_folder.mkdir()
    data_file_url = DataUrl(
        file_path=os.path.join(str(data_folder), "data.h5"),
        data_path="data",
        scheme="silx",
    )
    number_of_points = 31500
    with h5py.File(data_file_url.file_path(), mode="w") as h5f:
        h5f["data"] = numpy.random.random(number_of_points).reshape(
            number_of_points, 1, 1
        )

    dataset = Dataset(
        dataset=ImageDataset(
            detector_url=data_file_url.path(),
            metadata_url=DataUrl(
                file_path=str(dataset_file),
                data_path="positioners",
                scheme="silx",
            ).path(),
            _dir=None,
        )
    )
    image_dataset = dataset.dataset

    def check_dimensions_bounds(dims: dict):
        """Make sure find_dimension is correctly fitting motor bounds"""
        for dim in dims.values():
            numpy.testing.assert_almost_equal(
                dim.start, raw_motor_values[dim.name][0], decimal=3
            )
            numpy.testing.assert_almost_equal(
                dim.stop, raw_motor_values[dim.name][-1], decimal=3
            )

    # with a tolerance of 10e-9 we won't find 1081 steps over 2 dimensions
    assert len(image_dataset.dims) == 0
    image_dataset.find_dimensions(tolerance=1e-5)
    assert len(image_dataset.dims) == 3
    check_dimensions_bounds(dims=image_dataset.dims)
    assert (
        numpy.prod([val.size for val in image_dataset.dims.values()]) > number_of_points
    )

    image_dataset.find_dimensions(tolerance=1e-4)
    assert len(image_dataset.dims) == 3
    check_dimensions_bounds(dims=image_dataset.dims)
    assert (
        numpy.prod([val.size for val in image_dataset.dims.values()])
        == number_of_points
    )


def test_are_dimensions_ok():
    data = numpy.ones(1).repeat(20).reshape(20, 1, 1)
    metadata_dict = {
        "dim1": numpy.arange(20),
        "dim2": numpy.arange(20),
        "dim3": numpy.arange(20),
    }
    dataset = createHDF5Dataset(data, metadata_dict)
    dims = AcquisitionDims()

    # len == 0
    assert "None dimension are defined." == get_dimensions_error(dataset, dims)

    dims = [
        Dimension("dim1", 5, 0, 19),
        Dimension("dim2", 2, 0, 19),
        Dimension("bad_name", 2, 0, 19),
    ]

    # bad name
    assert "bad_name" in get_dimensions_error(dataset, dims)

    dims = [
        Dimension("dim1", 5, 0, 19),
        Dimension("dim2", 2, 0, 19),
        Dimension("dim3", 2, 0, 21),
    ]

    # bad stop
    assert "21" in get_dimensions_error(dataset, dims)

    dims = [
        Dimension("dim1", 5, 0, 19),
        Dimension("dim2", 2, 0, 19),
        Dimension("dim3", 2, -2, 19),
    ]

    # bad start
    assert "-2" in get_dimensions_error(dataset, dims)

    dims = [
        Dimension("dim1", 5, 0, 19),
        Dimension("dim2", 2, 0, 19),
        Dimension("dim3", 1, 0, 19),
    ]

    # bad size
    assert "20" in get_dimensions_error(dataset, dims)

    dims = [
        Dimension("dim1", 5, 0, 19),
        Dimension("dim2", 2, 0, 19),
        Dimension("dim3", 2, 0, 19),
    ]

    # good
    assert get_dimensions_error(dataset, dims) is None


@pytest.mark.parametrize(
    "metadata_values, expected_start, expected_stop, expected_size, expected_step",
    [
        (numpy.array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]), 10, 1, 10, -1),
        (numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), 1, 10, 10, 1),
        (numpy.array([1, 5, 9]), 1, 9, 3, 4),
        (numpy.array([1, 1, 2, 2.01, 3, 3, 4, 3.98, 5, 5]), 1, 5, 5, 1),
        (numpy.array([5, 5, 4, 3.98, 3, 3, 2, 2.01, 1, 1]), 5, 1, 5, -1),
        (numpy.array([2, 2]), 2, 2, 1, 0),
    ],
)
def test_dim_linspace(
    metadata_values: numpy.ndarray,
    expected_start: float,
    expected_stop: float,
    expected_size: int,
    expected_step: float,
):
    dim = Dimension("dim")
    dim.guess_parameters(metadata_values, tolerance=0.01)

    # Check start, stop, and length

    numpy.testing.assert_allclose(
        dim.compute_unique_values(),
        metadata_values[:: len(metadata_values) // expected_size],
        atol=0.01,
    )
    assert numpy.isclose(expected_start, dim.start)
    assert numpy.isclose(expected_stop, dim.stop)
    assert expected_size == dim.size
    assert expected_step == dim.step
