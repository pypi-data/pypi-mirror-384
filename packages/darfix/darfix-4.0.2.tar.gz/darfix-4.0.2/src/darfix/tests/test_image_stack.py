import numpy
import pytest

from darfix.core.imageStack import FixedDimension
from darfix.core.imageStack import ImageStack


def flatten_scans(data: numpy.ndarray):
    new_shape = (
        data.size // data.shape[-2] // data.shape[-1],
        data.shape[-2],
        data.shape[-1],
    )
    return data.reshape(new_shape)


def legacy_get_data(
    dataset: ImageStack, indices=None, dimension=None, return_indices=False
):
    """
    Legacy very complex dataset function
    (With a few modifications to remove ImageDataset dependencies)
    """
    if dimension is not None and len(dataset._data.shape) > 3:
        # Make sure dimension and value are lists
        if isinstance(dimension[0], int):
            dimension[0] = [dimension[0]]
            dimension[1] = [dimension[1]]
        data = dataset.data

        # Init list of bool indices
        bool_indices = numpy.zeros(dataset.nframes, dtype=bool)
        if indices is None:
            indices = numpy.arange(dataset.nframes)
        bool_indices[indices] = True
        bool_indices = bool_indices.reshape(dataset.scan_shape)
        indx = numpy.arange(dataset.nframes).reshape(dataset.scan_shape)

        # For every axis, get corresponding elements
        for i, dim in enumerate(sorted(dimension[0])):
            # Flip axis to be consistent with the data shape
            axis = len(dataset.scan_shape) - dim - 1
            data = data.take(indices=dimension[1][i], axis=axis)
            bool_indices = bool_indices.take(indices=dimension[1][i], axis=axis)
            indx = indx.take(indices=dimension[1][i], axis=axis)

        data = data[bool_indices]
        indx = indx[bool_indices]
        if return_indices:
            return flatten_scans(data), indx.flatten()
        return flatten_scans(data)

    data = flatten_scans(dataset.data)
    if return_indices:
        if indices is None:
            indices = numpy.arange(dataset.nframes)
        return data[indices], indices
    if indices is None:
        return data
    return data[indices]


@pytest.fixture
def image_stack():
    scans = numpy.arange(2 * 2).repeat(5 * 4 * 3).reshape(5, 4, 3, 2, 2)
    return ImageStack(scans)


def test_properties(image_stack: ImageStack):
    assert image_stack.nframes == 5 * 4 * 3
    assert image_stack.frame_shape == (2, 2)
    assert image_stack.scan_shape == (5, 4, 3)


def test_filter_indices(image_stack: ImageStack):
    numpy.testing.assert_array_equal(image_stack.filter_indices([0, 1, 2]), [0, 1, 2])
    numpy.testing.assert_array_equal(image_stack.filter_indices(None), numpy.arange(60))

    numpy.testing.assert_array_equal(
        image_stack.filter_indices(fixed_dimension=FixedDimension(0, 0)),
        numpy.arange(0, 60, 3),
    )
    numpy.testing.assert_array_equal(
        image_stack.filter_indices(fixed_dimension=FixedDimension(0, 1)),
        numpy.arange(1, 60, 3),
    )
    numpy.testing.assert_array_equal(
        image_stack.filter_indices(fixed_dimension=FixedDimension(2, 1)),
        numpy.arange(12, 24),
    )

    numpy.testing.assert_array_equal(
        image_stack.filter_indices(
            fixed_dimension=FixedDimension(2, 1), indices=numpy.arange(0, 18)
        ),
        numpy.arange(12, 18),
    )


def test_get_filtered_data(image_stack: ImageStack):
    # Should give the same result as old ImageDataset::get_data

    numpy.testing.assert_array_equal(
        image_stack.get_filtered_data([0, 1, 2]),
        legacy_get_data(image_stack, [0, 1, 2]),
    )
    numpy.testing.assert_array_equal(
        image_stack.get_filtered_data(None), legacy_get_data(image_stack, None)
    )

    numpy.testing.assert_array_equal(
        image_stack.get_filtered_data(fixed_dimension=FixedDimension(0, 0)),
        legacy_get_data(image_stack, dimension=[[0], [0]]),
    )
    numpy.testing.assert_array_equal(
        image_stack.get_filtered_data(fixed_dimension=FixedDimension(0, 1)),
        legacy_get_data(image_stack, dimension=[[0], [1]]),
    )
    numpy.testing.assert_array_equal(
        image_stack.get_filtered_data(fixed_dimension=FixedDimension(2, 1)),
        legacy_get_data(image_stack, dimension=[[2], [1]]),
    )

    numpy.testing.assert_array_equal(
        image_stack.get_filtered_data(
            fixed_dimension=FixedDimension(2, 1), indices=numpy.arange(0, 18)
        ),
        legacy_get_data(image_stack, dimension=[[2], [1]], indices=numpy.arange(0, 18)),
    )
