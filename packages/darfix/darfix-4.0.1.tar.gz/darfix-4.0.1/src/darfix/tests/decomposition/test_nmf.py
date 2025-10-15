import numpy

from darfix.decomposition.nmf import NMF
from darfix.tests.decomposition.utils import images
from darfix.tests.decomposition.utils import sampler


def test_fit_transform():
    rstate = numpy.random.RandomState(1000)
    resources = ["circle", "star", "pentagon", "square"]
    num_images = 100
    means = [15, 30, 45, 60]
    tol = 0.5
    sample = sampler(resources, means)

    X = numpy.array([sample(i).flatten() for i in range(num_images)])

    nmf = NMF(X, 4)
    H = rstate.random((nmf.num_components, nmf.num_features)) + 10**-4
    W = rstate.random((nmf.num_samples, nmf.num_components)) + 10**-4
    nmf.fit_transform(max_iter=500, H=H, W=W)

    stack = numpy.asarray(images(resources))
    for img in stack:
        img = img / numpy.linalg.norm(img)
        found = False
        for component in nmf.H:
            comp = component.reshape(img.shape)
            comp = comp / numpy.linalg.norm(comp)
            err = numpy.linalg.norm(comp - img)
            if err < tol:
                found = True
                break
        assert found is True
