import numpy
from scipy import stats

import darfix
from darfix.core import mapping


def test_moments():
    """Tests the correct moments calculation"""
    weights = list()
    moments = list()
    rs = numpy.random.RandomState(100)

    n0 = 200
    n1 = 3
    n2 = 4
    x = numpy.linspace(-2, 6, n0)
    aparams = rs.uniform(-5, 5, n1 * n2)
    scales = rs.uniform(0.5, 1, n1 * n2)
    locs = rs.uniform(1, 3, n1 * n2)

    for loc, scale, a in zip(locs, scales, aparams):
        rv = stats.skewnorm(a=a, loc=loc, scale=scale)
        w = rv.pdf(x)

        # Theoretical
        mean0, var0, skew0, kurt0 = rv.stats(moments="mvsk")

        # Calculate from data
        mean = sum(w * x) / w.sum()
        resid = x - mean
        var = sum(w * resid**2) / w.sum()
        sigma = numpy.sqrt(var)
        resid /= sigma
        fwhm = sigma * darfix.config.FWHM_VAL
        skew = sum(w * resid**3) / w.sum()
        kurt = (sum(w * resid**4) / w.sum()) - 3

        # Compare
        numpy.testing.assert_allclose(mean, mean0, rtol=1e-4)
        numpy.testing.assert_allclose(var, var0, rtol=1e-3)
        numpy.testing.assert_allclose(skew, skew0, rtol=1e-1)
        numpy.testing.assert_allclose(kurt, kurt0, rtol=2e-1)

        moments.append([mean, fwhm, skew, kurt])
        weights.append(w)

    weights = numpy.asarray(weights)
    weights = weights.reshape((n1, n2, n0))
    weights = numpy.transpose(weights, (2, 0, 1))
    moments = numpy.asarray(moments).reshape((n1, n2, 4))
    moments = numpy.transpose(moments, (2, 0, 1))
    mean1, fwhm1, skew1, kurt1 = moments

    mean2, fwhm2, skew2, kurt2 = mapping.compute_moments(x, weights, smooth=False)

    numpy.testing.assert_allclose(mean1, mean2)
    numpy.testing.assert_allclose(fwhm1, fwhm2)
    numpy.testing.assert_allclose(skew1, skew2)
    numpy.testing.assert_allclose(kurt1, kurt2)

    if False:
        import matplotlib.pyplot as plt

        for i in range(n1):
            for j in range(n2):
                y = weights[:, i, j]
                plt.plot(x, y)
                plt.vlines(mean1[i, j], 0, y.max())
                plt.vlines(mean2[i, j], 0, y.max())
        plt.show()


def test_rsm():
    """Tests RSM"""
    data = numpy.random.random(size=(3, 10, 10))
    H, W = data.shape[1:]
    d = 0.1
    ffz = 10
    mainx = 5

    pix_arr = mapping.compute_rsm(H, W, d, ffz, mainx)

    assert pix_arr[0].shape == (H, W)
    assert pix_arr[1].shape == (H, W)


def test_magnification():
    """Tests magnification"""
    data = numpy.random.random(size=(3, 10, 10))
    H, W = data.shape[1:]
    d = 0.1
    obx = 10
    obpitch = 25.1
    mainx = 5

    pix_arr = mapping.compute_magnification(H, W, d, obx, obpitch, mainx)

    assert pix_arr[0].shape == (H, W)
    assert pix_arr[1].shape == (H, W)


def test_magnification_uncentered():
    """Tests magnification uncentered"""
    data = numpy.random.random(size=(3, 10, 10))
    H, W = data.shape[1:]
    d = 0.1
    obx = 10
    obpitch = 25.1
    mainx = 50  # Has to be big enough

    pix_arr = mapping.compute_magnification(H, W, d, obx, obpitch, mainx, center=False)

    assert pix_arr[0][0][0] == 0
    assert pix_arr[1][H - 1][0] == 0


def test_peak_position():
    """Tests peak position map"""
    data = numpy.random.random(size=(3, 10, 10))
    image = mapping.compute_peak_position(data)
    assert image[0, 1] == numpy.argmax(data[:, 0, 1])


def test_peak_position_values():
    """Tests peak position map with values"""
    data = numpy.random.random(size=(3, 10, 10))
    values = numpy.repeat([numpy.linspace(0.1, 1, 10)], 3).flatten()
    image = mapping.compute_peak_position(data, values)

    assert image[0, 0] == values[numpy.argmax(data[:, 0, 0])]
