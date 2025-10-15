__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "22/04/2020"

import numpy
from PIL import Image

from darfix.tests.utils import utilstest


def sampler(resources, means, sigma=10):
    """
    Image sampler. Returns a function that, given an integer, returns
    an image with a mix of the images in resources.

    :resources: list of images name in ExternalResources.
    :means: Mean for every image in resources when computing the
        gaussian function.
    :sigma: sigma used in the gaussian function, defaults to 10.
    """
    stack = images(resources)
    stack = [(s - s.min()) / (s.max() - s.min()) for s in stack]

    def f(z):
        """
        Given the integer z, returns a new image with a mix (sum)
        of the images in stack. z will define the intensity of the
        images (for every image in stack, the closer is z to its
        corresponding mean, the more intense this image will appear).
        """
        result = numpy.zeros_like(stack[0], dtype=float)

        for i, im in enumerate(stack):
            G = (1 / numpy.sqrt(2 * numpy.pi * sigma)) * numpy.exp(
                -0.5 * ((z - means[i]) ** 2) / sigma**2
            )
            result += G * numpy.array(im, dtype=float)

        return result

    return f


def images(resources):
    """
    Given list of names, returns list of images from ExternalResources.
    """
    return [
        numpy.asarray(Image.open(utilstest.getfile(f)).convert("L")) for f in resources
    ]
