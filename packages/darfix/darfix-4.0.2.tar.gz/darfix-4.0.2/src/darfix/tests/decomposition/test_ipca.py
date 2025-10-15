import numpy
import pytest
from scipy.stats import special_ortho_group

from darfix.decomposition.ipca import IPCA


@pytest.fixture
def rstate():
    return numpy.random.RandomState(seed=1000)


def test_singular_values(rstate):
    data = rstate.random((100, 1000))
    ipca = IPCA(data, 50, num_components=3)
    assert ipca.singular_values is None
    ipca.fit_transform()
    assert len(ipca.singular_values) == 3


def test_fit_transform(rstate):
    # Number of features (dimension of the sample space)
    n = 10
    # Number of samples
    k = 100000
    # Number of principal components (dimension of the affine subspace)
    r = 5

    # Build principal components
    all_dims = numpy.arange(n)
    rstate.shuffle(all_dims)
    sub_dims = all_dims[:r]
    V = numpy.eye(n)[:, sub_dims]  # Subset of the standard basis vectors
    R = special_ortho_group.rvs(n)  # Random rotation in R^n
    V = numpy.dot(R, V)  # Principal components
    mean = rstate.rand(n)  # Affine space translation

    # Build observations
    D = numpy.diag(range(r, 0, -1)) ** 2  # Matrix of decreasing eigenvalues
    Z = rstate.normal(size=(k, r))  # Dimensionality-reduced samples
    Z = numpy.dot(Z, D)
    X = numpy.dot(Z, V.T) + mean  # Observations

    # Apply PCA to X to get Z, V
    ipca = IPCA(X, chunksize=10000, num_components=r)
    ipca.fit_transform()
    estimated_Z = numpy.round(ipca.W, 1)
    estimated_V = numpy.round(ipca.H.T, 1)

    numpy.testing.assert_allclose(numpy.abs(estimated_Z), numpy.abs(Z), rtol=0, atol=1)
    numpy.testing.assert_allclose(numpy.abs(estimated_V), numpy.abs(V), rtol=0, atol=1)


def test_fit_transform_indices(rstate):
    # Number of features (dimension of the sample space)
    n = 10
    # Number of samples
    k = 100000
    # Indices
    indices = numpy.arange(50000)
    # Number of principal components (dimension of the affine subspace)
    r = 5

    # Build principal components
    all_dims = numpy.arange(n)
    rstate.shuffle(all_dims)
    sub_dims = all_dims[:r]
    V = numpy.eye(n)[:, sub_dims]  # Subset of the standard basis vectors
    R = special_ortho_group.rvs(n)  # Random rotation in R^n
    V = numpy.dot(R, V)  # Principal components
    mean = rstate.rand(n)  # Affine space translation

    # Build observations
    D = numpy.diag(range(r, 0, -1)) ** 2  # Matrix of decreasing eigenvalues
    Z = rstate.normal(size=(k, r))  # Dimensionality-reduced samples
    Z = numpy.dot(Z, D)
    X = numpy.dot(Z, V.T) + mean  # Observations

    # Apply PCA to X to get Z, V
    ipca = IPCA(X, chunksize=10000, num_components=r, indices=indices)
    ipca.fit_transform()
    estimated_Z = numpy.round(ipca.W, 1)
    estimated_V = numpy.round(ipca.H.T, 1)

    numpy.testing.assert_allclose(
        numpy.abs(estimated_Z), numpy.abs(Z[indices]), rtol=0, atol=1
    )
    numpy.testing.assert_allclose(numpy.abs(estimated_V), numpy.abs(V), rtol=0, atol=1)
