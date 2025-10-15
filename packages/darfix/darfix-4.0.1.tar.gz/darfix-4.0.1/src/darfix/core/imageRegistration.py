from __future__ import annotations

__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "07/07/2021"

import enum
import warnings

try:
    import cv2
except ImportError:
    has_cv2 = False
else:
    has_cv2 = True

import numpy
import skimage

try:
    from skimage.registration import phase_cross_correlation
except ImportError:
    from skimage.feature import register_translation as phase_cross_correlation

from packaging.version import Version
from scipy.ndimage import center_of_mass
from scipy.ndimage import fourier_shift
from silx.utils.enum import Enum as _Enum

from darfix.io import utils

from .autofocus import normalized_variance


@enum.unique
class ShiftApproach(_Enum):
    """
    Different shifts approaches that can be used for the shift detection and correction.
    """

    LINEAR = "linear"
    FFT = "fft"


def compute_com(data):
    """
    Compute the center of mass of a stack of images.
    First it computes the intensity of every image (by summing its values), and then
    it uses scipy ``center_of_mass`` function to find the centroid.

    :param numpy.ndarray data: stack of images.
    :returns: the vector of intensities and the com.
    """
    intensity = data.sum(axis=1)
    return intensity, int(center_of_mass(intensity)[0])


def diff_com(img1, img2):
    """
    Finds the difference between the center of mass of two images.
    This can be used to find the shift between two images with distinguished
    center of mass.
    """
    return numpy.array(center_of_mass(img2)) - numpy.array(center_of_mass(img1))


def find_shift(img1, img2, upsample_factor=1000) -> numpy.ndarray:
    """
    Uses the function ``register_translation`` from skimage to find the shift between two images.

    :param array_like img1: first image.
    :param array_like img2: second image, must be same dimensionsionality as ``img1``.
    :param int upsample_factor: optional.
    """
    version = Version(skimage.__version__)

    if version >= Version("0.21.0"):
        shifts, _, _ = phase_cross_correlation(
            img1,
            img2,
            upsample_factor=upsample_factor,
            normalization=None,
        )
        return shifts
    if version >= Version("0.19.0"):
        return phase_cross_correlation(
            img1,
            img2,
            upsample_factor=upsample_factor,
            return_error=False,  # deprecated in 0.21 and removed in 0.22
            normalization=None,
        )
    return phase_cross_correlation(
        img1, img2, upsample_factor=upsample_factor, return_error=False
    )


def _numpy_fft_shift(img, dx, dy):
    """
    Shift an image by Fourier approach using Numpy library.

    :param array_like img: Image to shift
    :param number dx: shift in x axis
    :param number dy: shift in y axis
    :returns: ndarray
    """
    img = numpy.asarray(img, dtype=numpy.float32)
    xnum, ynum = img.shape
    """
    Create grid to apply the Fourier transformed theory for translated images.
    Each value of each matrix (Nx, Ny) correspons to the coordinate of the corresponding pixel.
    """
    Nx, Ny = numpy.meshgrid(numpy.fft.fftfreq(ynum), numpy.fft.fftfreq(xnum))
    c = numpy.fft.fft2(img) * numpy.exp(-2 * numpy.pi * 1j * (dx * Nx + dy * Ny))
    return numpy.fft.ifft2(c).real


def _opencv_fft_shift(img, dx, dy):
    """
    Shift an image by Fourier approach using opencv library.

    :param array_like img: Image to shift
    :param number dx: shift in x axis
    :param number dy: shift in y axis
    :returns: ndarray
    """
    img = numpy.asarray(img, dtype=numpy.float32)
    ynum, xnum = img.shape
    """
    Create grid to apply the Fourier transformed theory for translated images.
    Each value of each matrix (Nx, Ny) corresponds to the coordinate of the corresponding pixel
    divided by the size of the image.
    """

    Nx, Ny = numpy.meshgrid(numpy.fft.fftfreq(xnum), numpy.fft.fftfreq(ynum))
    dft = cv2.dft(img, flags=cv2.DFT_COMPLEX_OUTPUT)
    dft = dft[..., 0] + 1j * dft[..., 1]
    dft = dft * numpy.exp(-2 * numpy.pi * 1j * (dx * Nx + dy * Ny))
    real = numpy.reshape(dft.real, dft.real.shape + (1,))
    imag = numpy.reshape(dft.imag, dft.imag.shape + (1,))
    dft = numpy.concatenate((real, imag), axis=2)
    return cv2.idft(dft, flags=cv2.DFT_SCALE + cv2.DFT_REAL_OUTPUT)


def _scipy_fft_shift(img, dx, dy):
    """
    Shift an image by Fourier approach using scipy library.

    :param array_like img: Image to shift
    :param number dx: shift in x axis
    :param number dy: shift in y axis
    :returns: ndarray
    """
    return numpy.fft.ifftn(fourier_shift(numpy.fft.fftn(img), [dy, dx])).real


def apply_opencv_shift(img, shift, shift_approach="fft"):
    """
    Function to apply the shift to an image.

    :param 2-dimensional array_like img: Input array, can be complex.
    :param 2-dimensional array_like shift: The shift to be applied to the image. ``shift[0]``
        refers to the y-axis, ``shift[1]`` refers to the x-axis.
    :param Union[`linear`, `fft`] shift_approach: The shift method to be used to apply the shift.
    :returns: real ndarray
    """
    if not has_cv2:
        raise RuntimeError(
            "opencv-python is not installed. Unable to apply shift with it. Please install it."
        )
    shift_approach = ShiftApproach.from_value(shift_approach)
    if shift_approach == ShiftApproach.LINEAR:
        img = img.astype(numpy.int16)
        M = numpy.float32([[1, 0, shift[1]], [0, 1, shift[0]]])
        return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
    else:
        return _opencv_fft_shift(img, shift[1], shift[0])


def normalize(x):
    """
    Normalizes a vector or matrix.
    """
    if not numpy.count_nonzero(x):
        return x
    return x / numpy.linalg.norm(x)


def improve_linear_shift(
    data, v, h, epsilon, steps, nimages=None, shift_approach="linear"
):
    """
    Function to find the best shift between the images. It loops ``steps`` times,
    applying a different shift each, and trying to find the one that has the best result.

    :param array_like data: The stack of images.
    :param 2-dimensional array_like v: The vector with the direction of the shift.
    :param float epsilon: Maximum value of h
    :param int steps: Number of different tries of h.
    :param int nimages: The number of images to be used to find the best shift. It has to
        be smaller or equal as the length of the data. If it is smaller, the images used
        are chosen using `numpy.random.choice`, without replacement.
    :param Union[`linear`,`fft`] shift_approach: The shift method to be used to apply the shift.
    :returns: ndarray
    """
    shift_approach = ShiftApproach.from_value(shift_approach)
    v = numpy.asanyarray(v)
    iData = range(data.shape[0])

    if nimages:
        iData = numpy.random.choice(iData, nimages, False)

    score = {}
    utils.advancement_display(0, h + epsilon, "Finding shift")
    step = epsilon / steps
    for h_ in numpy.arange(0, h + epsilon, step):
        result = numpy.zeros(data[0].shape)
        for iFrame in iData:
            shift = h_ * v * iFrame
            result += apply_opencv_shift(data[iFrame], shift, shift_approach)

        # Compute score using normalized variance
        # TODO: add more autofocus options
        score[h_] = normalized_variance(result)
        utils.advancement_display(h_ + step, h + epsilon, "Finding shift")
    optimal_h = max(score.keys(), key=(lambda k: score[k]))
    return optimal_h


def shift_detection(
    data: numpy.ndarray, steps: int, shift_approach="linear"
) -> tuple[float, float]:
    """
    Finds the linear shift from a set of images.

    :param ndarray data: Array with the images.
    :returns: the linear shift
    """
    if len(data) == 0:
        return (0, 0)
    shape = data[0].shape
    first_sum = numpy.zeros(shape)
    second_sum = numpy.zeros(shape)
    imid = len(data) / 2
    for i in range(len(data)):
        if i < imid:
            first_sum += data[i]
        else:
            second_sum += data[i]
    if not first_sum.any() or not second_sum.any():
        shift = numpy.zeros(second_sum.ndim)
    else:
        shift = find_shift(first_sum, second_sum, 1000)
    v = normalize(shift)
    v_ = 2 * shift / len(data)
    h = numpy.sqrt(v_[0] ** 2 + v_[1] ** 2)
    if not h:
        return (0, 0)
    epsilon = 2 * h
    h = improve_linear_shift(data, v, h, epsilon, steps, shift_approach=shift_approach)
    return tuple(h * v)


def sum_images(image1, image2=None):
    if image2 is None:
        return numpy.asarray(image1)
    return numpy.asarray(image1) + numpy.asarray(image2)


def shift_correction(data, n_shift, shift_approach="fft", callback=None):
    """
    Function to apply shift correction technique to stack of images.

    :param array_like data: The stack of images to apply the shift to.
    :param array_like n_shift: Array with the shift to be applied at every image.
        The first row has the shifts in the y-axis and the second row the shifts
        in the x-axis. For image ``i`` the shift applied will be:
        ``shift_y = n_shift[0][i] shift_x = n_shift[1][i]```.
    :param Union[`linear`,`fft`] shift_approach: Name of the shift approach
        to be used. Default: `fft`.
    :param Union[None,Function] callback: Callback function to update the
        progress.
    :returns: The shifted images.
    :rtype: ndarray
    """
    shift_approach = ShiftApproach.from_value(shift_approach)

    shift = numpy.asanyarray(n_shift)

    if not numpy.any(shift):
        return data

    assert shift.shape == (
        2,
        len(data),
    ), "n_shift list has to be of same size as stack of images"

    shifted_data = numpy.empty(data.shape, dtype=numpy.float32)

    utils.advancement_display(0, len(data), "Applying shift")

    for count, frame in enumerate(data):
        shifted_data[count] = apply_opencv_shift(frame, shift[:, count], shift_approach)
        utils.advancement_display(count + 1, len(data), "Applying shift")
        if callback:
            callback(int(count / len(data) * 100))

    with warnings.catch_warnings():
        warnings.simplefilter("always")

        if data.dtype.kind == "f":
            if data.dtype.itemsize > shifted_data.dtype.itemsize:
                warnings.warn("Precision loss to float32")
        else:
            warnings.warn("Data cast to float32")

    return shifted_data


def random_search(data, optimal_shift, iterations, sigma=None, shift_approach="linear"):
    """
    Function that performs random search to a set of images to find an improved vector of shifts (one
    for each image). For this, it adds to the optimal shift a series of random samples obtained from
    a multivariate normal distribution, and selects the one with best score.

    :param array_like data: Set of images.
    :param ndarray optimal_shift: Array with two vectors with the linear shift found for axis y and x.
    :param int iterations: Number of times the random search should be done.
    :param number sigma: Standard deviation of the distribution.
    :param Union[`linear`,`fft`] shift_approach: Name of the shift approach
        to be used. Default: `linear`.
    :returns: A vector of length the number of images with the best shift found for every image.
    :rtype: ndarray
    """
    best_score = -numpy.inf
    best_result = numpy.empty(optimal_shift.shape)

    if sigma is None:
        # Using shift from second image
        sigma = abs(optimal_shift[:, 1] / 3)

    utils.advancement_display(0, iterations)
    for i in range(iterations):
        result = []
        normal = numpy.random.multivariate_normal(
            (0, 0), sigma * numpy.eye(2), len(data)
        ).T
        n_shift = optimal_shift + normal
        for iFrame in range(len(data)):
            shifty = n_shift[0][iFrame]
            shiftx = n_shift[1][iFrame]
            result += [
                apply_opencv_shift(data[iFrame], [shifty, shiftx], shift_approach)
            ]
        score = normalized_variance(result)
        if best_score < score:
            best_result = n_shift
            best_score = score

        utils.advancement_display(i + 1, iterations)

    return best_result
