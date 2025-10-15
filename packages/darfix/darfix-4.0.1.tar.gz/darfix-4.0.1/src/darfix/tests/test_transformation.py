import numpy
import pytest

from darfix.core.transformation import Transformation
from darfix.core.utils import NoDimensionsError

from .utils import create_1d_dataset
from .utils import create_dataset_for_RSM


def test_rsm_kind(tmpdir):
    dataset = create_dataset_for_RSM(dir=tmpdir)

    with pytest.raises(NoDimensionsError):
        dataset.compute_transformation(0.1, kind="rsm")
    dataset.find_dimensions()

    assert dataset.transformation is None
    dataset.compute_transformation(0.1, kind="rsm")

    transformation = dataset.transformation

    assert isinstance(transformation, Transformation)
    assert transformation.shape == dataset.frame_shape
    assert numpy.all(numpy.isfinite(transformation.x))
    assert numpy.all(numpy.isfinite(transformation.y))


def test_magnification_kind(tmpdir):
    dataset = create_1d_dataset(
        dir=tmpdir,
        motor1="obx",
        motor2="obpitch",
    )

    with pytest.raises(NoDimensionsError):
        dataset.compute_transformation(0.1, kind="magnification")
    dataset.find_dimensions()

    assert dataset.transformation is None
    dataset.compute_transformation(0.1, kind="magnification")

    transformation = dataset.transformation

    assert isinstance(transformation, Transformation)
    assert transformation.shape == dataset.frame_shape
    assert numpy.all(numpy.isfinite(transformation.x))
    assert numpy.all(numpy.isfinite(transformation.y))


def test_compute_magnification(dataset):
    """Tests fitting data"""

    dataset.find_dimensions()
    dataset.reshape_data()
    dataset.compute_transformation(d=0.1)
    assert dataset.transformation.shape == dataset.frame_shape
