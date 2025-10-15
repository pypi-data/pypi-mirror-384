import numpy

from darfix.math import bivariate_gaussian
from darfix.math import gaussian
from darfix.math import trivariate_gaussian


def test_gaussian():
    X = numpy.random.random((100))
    X0 = X.mean()

    result = gaussian(X, amplitude=1, x0=X0, std_dev=0.5, background=0)

    assert result.shape == (100,)


def test_bivariate_gaussian():
    X = numpy.random.random((2, 100))
    X0 = X.mean(axis=1)

    result = bivariate_gaussian(X, X0[0], X0[1], 0.5, 0.5, 1, 0.1)

    assert result.shape == (100,)


def test_trivariate_gaussian():
    X = numpy.random.random((3, 100))
    X0 = X.mean(axis=1)

    result = trivariate_gaussian(
        X,
        X0[0],
        X0[1],
        X0[2],
        sigma_x0=1,
        sigma_x1=1,
        sigma_x2=1,
        c10=0.5,
        c20=0.2,
        c12=0.1,
        amplitude=1,
    )

    assert result.shape == (100,)
