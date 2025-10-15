import numpy
import pytest

from darfix.core import roi


@pytest.fixture()
def data():
    return numpy.array(
        [
            [
                [1, 2, 3, 4, 5],
                [2, 2, 3, 4, 5],
                [3, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
            [
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 3],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
            [
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [8, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
        ]
    )


def test_ROI_0(data):

    expected = numpy.array([[2, 3, 4], [2, 3, 4], [2, 3, 4]])

    data = roi.apply_2D_ROI(data[0], size=(3, 3), center=numpy.array(data[0].shape) / 2)
    numpy.testing.assert_equal(data, expected)


def test_ROI_1(data):

    expected = numpy.array([[1, 2], [2, 2]])

    data = roi.apply_2D_ROI(data[0], size=(3, 3), center=(0, 0))
    numpy.testing.assert_equal(data, expected)


def test_ROI_2(data):

    expected = numpy.array([[2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5]])

    data = roi.apply_2D_ROI(data[0], size=(4, 4), center=(2, 3))
    numpy.testing.assert_equal(data, expected)


def test_ROI_3D_0(data):

    expected = numpy.array([[[1, 2], [2, 2]], [[1, 2], [1, 2]], [[1, 2], [1, 2]]])

    data = roi.apply_3D_ROI(data, size=(2, 2), origin=(0, 0))
    numpy.testing.assert_equal(data, expected)


def test_ROI_3D_1(data):

    expected = numpy.array([[[1]], [[1]], [[1]]])

    data = roi.apply_3D_ROI(data, size=(2, 2), center=(0, 0))
    numpy.testing.assert_equal(data, expected)


def test_ROI_3D_2(data):

    expected = numpy.array(
        [
            [[2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5]],
            [[2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 3], [2, 3, 4, 5]],
            [[2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5], [2, 3, 4, 5]],
        ]
    )

    data = roi.apply_3D_ROI(data, size=(4, 4), center=(2, 3))
    numpy.testing.assert_equal(data, expected)
