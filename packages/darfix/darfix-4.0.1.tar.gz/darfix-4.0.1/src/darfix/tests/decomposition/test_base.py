import numpy
import pytest

from darfix.decomposition.base import Base


@pytest.fixture
def images():
    return numpy.random.random((100, 1000))


def test_data(images):
    base = Base(images)
    numpy.testing.assert_equal(images, base.data)


def test_indices(images):
    base = Base(images)
    numpy.testing.assert_equal(base.indices, numpy.arange(len(images)))

    base = Base(images, indices=numpy.arange(20))
    numpy.testing.assert_equal(base.indices, numpy.arange(20))


def test_num_components(images):
    base = Base(images)
    assert base.num_components == 100

    base = Base(images, num_components=10)
    assert base.num_components == 10


def test_W(images):
    base = Base(images, num_components=10)
    base.fit_transform()

    assert base.W.shape == (100, 10)


def test_H(images):
    base = Base(images, num_components=10)
    base.fit_transform()

    assert base.H.shape == (10, 1000)


def test_fit_transform(images):
    base = Base(images)
    base.fit_transform(compute_w=False)
    assert not hasattr(base, "W")
    assert hasattr(base, "H")

    base = Base(images)
    base.fit_transform(compute_h=False)
    assert not hasattr(base, "H")
    assert hasattr(base, "W")


def test_frobenius_norm(images):
    base = Base(images)
    assert base.frobenius_norm() is None

    base.fit_transform()
    assert base.frobenius_norm() is not None
