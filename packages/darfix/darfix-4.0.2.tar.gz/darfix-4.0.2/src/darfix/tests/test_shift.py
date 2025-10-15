import numpy
import pytest

from darfix.core.imageRegistration import apply_opencv_shift
from darfix.tests.utils import createHDF5Dataset2D


@pytest.fixture
def two_motors_dataset():
    # 2d daset like in shift correction example, A square shifted by (3,2) along the axis 1
    data = numpy.zeros(150000).reshape((10, 5, 50, 60))
    for i in range(10):
        data[i, :, 3 * i + 10 : 3 * i + 20, 2 * i + 10 : 2 * i + 20] = 1
    return createHDF5Dataset2D(data)


def test_find_shift(two_motors_dataset):
    """Tests the shift detection with dimensions and indices"""
    dataset = two_motors_dataset

    dataset.find_dimensions()
    dataset.reshape_data()

    # Axis 0 : dim size is 5
    assert dataset.dims[0].size == 5
    # Axis 1 : dim size is 10
    assert dataset.dims[1].size == 10

    shift = dataset.find_shift(selected_axis=0)

    # dimension shift is 3, 2 for axis 0
    numpy.testing.assert_allclose(shift, (-3, -2))

    # dimension shift is 0, 0 for axis 1

    shift = dataset.find_shift(selected_axis=1)

    numpy.testing.assert_allclose(shift, (0, 0))


def test_apply_shift(two_motors_dataset):
    """Tests the shift correction with dimensions and indices"""
    dataset = two_motors_dataset

    dataset.find_dimensions()
    dataset.reshape_data()

    # Axis 0 : dim size is 5
    assert dataset.dims[0].size == 5
    # Axis 1 : dim size is 10
    assert dataset.dims[1].size == 10

    input_img = dataset.as_array3d(4).copy()
    # Check fit is well applied at index 4
    result_idx4 = apply_opencv_shift(input_img, shift=(0.5 * 4, 0.5 * 4))

    dataset.apply_shift(shift=(0.5, 0.5), axis=1, shift_approach="fft")

    numpy.testing.assert_raises(
        AssertionError,
        numpy.testing.assert_array_equal,
        input_img,
        dataset.as_array3d(4),
    )
    numpy.testing.assert_allclose(result_idx4, dataset.as_array3d(4))


def test_find_shift_along_dimension(two_motors_dataset):
    """Tests the shift detection along a dimension"""
    dataset = two_motors_dataset

    dataset.find_dimensions()
    dataset.reshape_data()

    shift = dataset.find_shift(selected_axis=1)
    assert len(shift) == 2
    shift = dataset.find_shift(selected_axis=0)
    assert len(shift) == 2


def test_apply_shift_along_dimension(two_motors_dataset):
    """Tests the shift correction with dimensions and indices"""
    dataset = two_motors_dataset

    dataset.find_dimensions()
    dataset.reshape_data()

    # Axis 0 : dim size is 5
    assert dataset.dims[0].size == 5
    # Axis 1 : dim size is 10
    assert dataset.dims[1].size == 10

    first_img = dataset.as_array3d()[0].copy()

    last_img = dataset.as_array3d()[-1].copy()

    dataset.apply_shift(shift=numpy.array([-3, -2]), axis=0)

    # Test if shift correction is successfull
    numpy.testing.assert_array_almost_equal(first_img, dataset.as_array3d()[0])
    numpy.testing.assert_array_almost_equal(first_img, dataset.as_array3d()[24])
    numpy.testing.assert_array_almost_equal(first_img, dataset.as_array3d()[37])
    numpy.testing.assert_array_almost_equal(first_img, dataset.as_array3d()[49])
    numpy.testing.assert_raises(
        AssertionError,
        numpy.testing.assert_array_equal,
        last_img,
        dataset.as_array3d()[-1],
    )
