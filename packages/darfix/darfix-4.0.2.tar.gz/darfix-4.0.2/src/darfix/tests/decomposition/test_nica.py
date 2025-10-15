import numpy
import pytest
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA

from darfix.decomposition.ipca import IPCA
from darfix.decomposition.nica import NICA
from darfix.tests.decomposition.utils import images
from darfix.tests.decomposition.utils import sampler


@pytest.fixture
def X():
    iris = load_iris()
    return iris.data


def test_whiten_pca(X):
    nica = NICA(X, 2)
    pca = PCA(2, whiten=True)
    X = pca.fit_transform(X.T).T
    numpy.testing.assert_equal(X, nica.Z)
    numpy.testing.assert_equal(pca.components_, nica.V)


def test_whiten_ipca(X):
    nica = NICA(X, 2, chunksize=2)
    ipca = IPCA(X, 2, 2, whiten=True, rowvar=False)
    ipca.fit_transform()
    numpy.testing.assert_equal(ipca.W.T, nica.Z)
    numpy.testing.assert_equal(ipca.H, nica.V)


def test_W(X):
    nica = NICA(X, 2)
    nica.fit_transform()
    assert nica.W.shape == (X.shape[0], 2)


def test_H(X):
    nica = NICA(X, 2)
    nica.fit_transform()
    assert nica.H.shape == (2, X.shape[1])


def test_fit_transform(X):
    resources = ["circle", "star", "pentagon", "square"]
    num_images = 100
    means = [15, 30, 45, 60]
    tol = 0.7
    sample = sampler(resources, means)

    X = numpy.array([sample(i).flatten() for i in range(num_images)])
    nica = NICA(X, 4)
    nica.fit_transform(max_iter=1000)

    stack = numpy.asarray(images(resources))
    for img in stack:
        img = img / numpy.linalg.norm(img)
        found = False
        for component in nica.H:
            comp = component.reshape(img.shape)
            comp = comp / numpy.linalg.norm(comp)
            err = numpy.linalg.norm(comp - img)
            if err < tol:
                found = True
                break
        assert found is True


def test_fit_transform_IPCA(X):
    resources = ["circle", "star", "pentagon", "square"]
    num_images = 100
    means = [15, 30, 45, 60]
    tol = 0.7
    sample = sampler(resources, means)

    X = numpy.array([sample(i).flatten() for i in range(num_images)])
    nica = NICA(X, 4, chunksize=1000)
    nica.fit_transform(max_iter=1000)

    stack = numpy.asarray(images(resources))
    for img in stack:
        img = img / numpy.linalg.norm(img)
        found = False
        for component in nica.H:
            comp = component.reshape(img.shape)
            comp = comp / numpy.linalg.norm(comp)
            err = numpy.linalg.norm(comp - img)
            if err < tol:
                found = True
                break
        assert found is True


def test_fit_transform_indices(X):
    resources = ["circle", "star", "pentagon", "square"]
    num_images = 100
    means = [15, 30, 45, 60]
    tol = 0.7
    sample = sampler(resources, means)

    X = numpy.array([sample(i).flatten() for i in range(num_images)])
    nica = NICA(X, 4, indices=numpy.arange(50))
    nica.fit_transform(max_iter=1000)

    stack = numpy.asarray(images(resources[:-1]))
    for img in stack:
        img = img / numpy.linalg.norm(img)
        found = False
        for component in nica.H:
            comp = component.reshape(img.shape)
            comp = comp / numpy.linalg.norm(comp)
            err = numpy.linalg.norm(comp - img)
            if err < tol:
                found = True
                break
        assert found is True


def test_fit_transform_IPCA_indices(X):
    resources = ["circle", "star", "pentagon", "square"]
    num_images = 100
    means = [15, 30, 45, 60]
    tol = 0.7
    sample = sampler(resources, means)

    X = numpy.array([sample(i).flatten() for i in range(num_images)])
    nica = NICA(X, 4, chunksize=1000, indices=numpy.arange(50))
    nica.fit_transform(max_iter=1000)

    stack = numpy.asarray(images(resources[:-1]))
    for img in stack:
        img = img / numpy.linalg.norm(img)
        found = False
        for component in nica.H:
            comp = component.reshape(img.shape)
            comp = comp / numpy.linalg.norm(comp)
            err = numpy.linalg.norm(comp - img)
            if err < tol:
                found = True
                break
        assert found is True
