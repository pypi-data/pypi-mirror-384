import pytest

from darfix.core.utils import NoDimensionsError


def test_apply_moments(dataset):

    with pytest.raises(NoDimensionsError):
        dataset.apply_moments(indices=[1, 2, 3, 4])

    dataset.find_dimensions()
    dataset.reshape_data()
    moments = dataset.apply_moments(indices=[1, 2, 3, 4])
    assert moments[0][0].shape == dataset.frame_shape
    assert moments[1][3].shape == dataset.frame_shape
