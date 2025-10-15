import numpy
import pytest

from darfix.processing import imageOperations


@pytest.fixture
def data():
    return numpy.array(
        [
            [1, 1, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 6, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
        ],
        dtype=numpy.uint16,
    )


@pytest.fixture
def dark():
    return numpy.array(
        [
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
        ],
        dtype=numpy.uint16,
    )


def test_background_subtraction(data, dark):
    """Tests background subtraction function"""
    expected = numpy.array(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 3, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=numpy.uint16,
    )

    imageOperations.background_subtraction(data, dark)
    numpy.testing.assert_array_equal(expected, data)


def test_hot_pixel_removal(data):
    """Tests the hot pixel removal in stack of arrays"""
    expected = numpy.array(
        [
            [1, 1, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
        ],
        dtype=numpy.uint16,
    )

    imageOperations.hot_pixel_removal(data)
    numpy.testing.assert_array_equal(expected, data)


def test_threshold_removal(data):
    """Tests the threshold of the data"""

    expected = numpy.array(
        [
            [0, 0, 3, 4, 0],
            [0, 2, 3, 4, 0],
            [0, 2, 0, 4, 0],
            [0, 2, 3, 4, 0],
            [0, 2, 3, 4, 0],
        ],
        dtype=numpy.uint16,
    )

    imageOperations.threshold_removal(data, 2, 4)

    numpy.testing.assert_array_equal(expected, data)
