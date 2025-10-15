import numpy
import pytest

try:
    import scipy
except ImportError:
    scipy = None

from darfix.core import imageRegistration
from darfix.tests import utils


@pytest.fixture
def data():

    return numpy.array(
        [
            [
                [1, 2, 3, 4, 5],
                [2, 2, 3, 4, 5],
                [3, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
            [
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 3],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
            [
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [8, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
        ]
    )


@pytest.fixture
def rstate():
    return numpy.random.RandomState(1000)


@pytest.fixture
def metadata_dict():
    return utils.create_2_motors_metadata(2, 5)


@pytest.fixture
def first_frame(rstate):
    first_frame = numpy.zeros((100, 100))
    first_frame[30:40, 30:40] = rstate.randint(50, 100, size=(10, 10))

    return first_frame


def test_find_shift(data):
    """Tests the shift found"""
    shift = (-1.4, 1.32)
    for img in data:
        # The shift corresponds to the pixel offset relative to the reference image
        offset_image = imageRegistration._opencv_fft_shift(img, shift[1], shift[0])
        computed_shift = imageRegistration.find_shift(img, offset_image, 100)
        numpy.testing.assert_allclose(shift, -computed_shift, rtol=1e-04)


def test_apply_shift(data):
    """Tests the correct apply of the shift"""
    shift = (0, 0)
    for img in data:
        shifted_image = imageRegistration.apply_opencv_shift(img, shift)
        numpy.testing.assert_allclose(img, shifted_image, rtol=1e-04)
    for img in data:
        shifted_image = imageRegistration.apply_opencv_shift(
            img, shift, shift_approach="linear"
        )
        numpy.testing.assert_allclose(img, shifted_image, rtol=1e-04)


def test_improve_shift(data):
    """Tests the shift improvement"""
    h = imageRegistration.improve_linear_shift(
        data, [1, 1], 0.1, 0.1, 1, shift_approach="fft"
    )
    numpy.testing.assert_allclose(h, 0.0)
    h = imageRegistration.improve_linear_shift(
        data, [1, 1], 0.1, 0.1, 1, shift_approach="linear"
    )
    numpy.testing.assert_allclose(h, 0.0)


@pytest.mark.skipif(scipy is None, reason="scipy is missing")
def test_shift_detection10(rstate):
    """Tests the shift detection with tolerance of 3 decimals"""
    first_frame = numpy.zeros((100, 100))
    # Simulating a series of frame with information in the middle.
    first_frame[25:75, 25:75] = rstate.randint(50, 300, size=(50, 50))
    data = [first_frame]
    shift = [1.0, 0]
    for i in range(9):
        data += [
            numpy.fft.ifftn(
                scipy.ndimage.fourier_shift(numpy.fft.fftn(data[-1]), shift)
            ).real
        ]
    data = numpy.asanyarray(data, dtype=numpy.int16)
    optimal_shift = imageRegistration.shift_detection(data, 100, shift_approach="fft")

    shift = [-1, 0]

    numpy.testing.assert_allclose(shift, numpy.round(optimal_shift))


@pytest.mark.skipif(scipy is None, reason="scipy is missing")
def test_shift_detection01(rstate):
    """Tests the shift detection with tolerance of 5 decimals"""
    # Create a frame and repeat it shifting it every time
    first_frame = numpy.zeros((100, 100))
    first_frame[25:75, 25:75] = rstate.randint(50, 300, size=(50, 50))
    data = [first_frame]
    shift = [0, 1]
    for i in range(9):
        data += [
            numpy.fft.ifftn(
                scipy.ndimage.fourier_shift(numpy.fft.fftn(data[-1]), shift)
            ).real
        ]
    data = numpy.asanyarray(data, dtype=numpy.int16)
    optimal_shift = imageRegistration.shift_detection(data, 100, shift_approach="fft")

    shift = [0, -1]

    numpy.testing.assert_allclose(shift, numpy.round(optimal_shift))


@pytest.mark.skipif(scipy is None, reason="scipy is missing")
def test_shift_detection11(rstate):
    """Tests the shift detection with tolerance of 2 decimals"""
    # Create a frame and repeat it shifting it every time
    first_frame = numpy.zeros((100, 100))
    first_frame[25:75, 25:75] = rstate.randint(50, 300, size=(50, 50))
    data = [first_frame]
    shift = [1, 1]
    for i in range(9):
        data += [
            numpy.fft.ifftn(
                scipy.ndimage.fourier_shift(numpy.fft.fftn(data[-1]), shift)
            ).real
        ]
    data = numpy.asanyarray(data, dtype=numpy.int16)

    optimal_shift = imageRegistration.shift_detection(data, 100)

    shift = [-1, -1]

    numpy.testing.assert_allclose(shift, numpy.round(optimal_shift))


@pytest.mark.skipif(scipy is None, reason="scipy is missing")
def test_shift_detection_float(rstate):
    """Tests the shift detection using shifted float with tolerance of 2 decimals"""
    first_frame = numpy.zeros((100, 100))
    # Simulating a series of frame with information in the middle.
    first_frame[25:75, 25:75] = rstate.randint(50, 300, size=(50, 50))
    data = [first_frame]
    shift = [0.5, 0.2]
    for i in range(9):
        data += [
            numpy.fft.ifftn(
                scipy.ndimage.fourier_shift(numpy.fft.fftn(data[-1]), shift)
            ).real
        ]
    data = numpy.asanyarray(data, dtype=numpy.int16)
    optimal_shift = imageRegistration.shift_detection(data, 100)
    shift = [-0.5, -0.2]

    numpy.testing.assert_allclose(shift, numpy.round(optimal_shift, 1))


def test_shift_correction00(data):
    """Tests the shift correction of a [0,0] shift."""

    data = imageRegistration.shift_correction(
        data, numpy.outer([0, 0], numpy.arange(3))
    )
    numpy.testing.assert_allclose(data, data, rtol=1e-03)


def test_shift_correction01(data):
    """Tests the shift correction of a [0,1] shift."""

    expected = numpy.array(
        [
            [
                [1, 2, 3, 4, 5],
                [2, 2, 3, 4, 5],
                [3, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
            [
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 3],
                [1, 2, 3, 4, 5],
            ],
            [
                [8, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
        ]
    )

    new_data = imageRegistration.shift_correction(
        data, numpy.outer([1, 0], numpy.arange(3))
    )
    numpy.testing.assert_allclose(new_data, expected, rtol=1e-03)


def test_shift_correction10(data):
    """Tests the shift correction of a [1,0] shift."""

    expected = numpy.array(
        [
            [
                [1, 2, 3, 4, 5],
                [2, 2, 3, 4, 5],
                [3, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
            [
                [5, 1, 2, 3, 4],
                [5, 1, 2, 3, 4],
                [3, 1, 2, 3, 4],
                [5, 1, 2, 3, 4],
                [5, 1, 2, 3, 4],
            ],
            [
                [4, 5, 1, 2, 3],
                [4, 5, 1, 2, 3],
                [4, 5, 1, 2, 3],
                [4, 5, 8, 2, 3],
                [4, 5, 1, 2, 3],
            ],
        ]
    )

    new_data = imageRegistration.shift_correction(
        data, numpy.outer([0, 1], numpy.arange(3))
    )
    numpy.testing.assert_allclose(new_data, expected, rtol=1e-05)


def test_shift_correction11(data):
    """Tests the shift correction of a [1,1] shift."""

    expected = numpy.array(
        [
            [
                [1, 2, 3, 4, 5],
                [2, 2, 3, 4, 5],
                [3, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
                [1, 2, 3, 4, 5],
            ],
            [
                [5, 1, 2, 3, 4],
                [5, 1, 2, 3, 4],
                [5, 1, 2, 3, 4],
                [3, 1, 2, 3, 4],
                [5, 1, 2, 3, 4],
            ],
            [
                [4, 5, 8, 2, 3],
                [4, 5, 1, 2, 3],
                [4, 5, 1, 2, 3],
                [4, 5, 1, 2, 3],
                [4, 5, 1, 2, 3],
            ],
        ]
    )
    new_data = imageRegistration.shift_correction(
        data, numpy.outer([1, 1], numpy.arange(3))
    )
    numpy.testing.assert_allclose(new_data, expected, rtol=1e-05)


def test_shift_correction_float(data):
    """Tests the shift correction of a [0.1, 0.25] shift between images."""

    expected = [
        [
            [1, 2, 3, 4, 5],
            [2, 2, 3, 4, 5],
            [3, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
            [1, 2, 3, 4, 5],
        ],
        [
            [1.2595824, 1.7349374, 3.0299857, 3.756984, 4.9321423],
            [1.3387496, 1.6893137, 3.0737815, 3.690435, 5.6077204],
            [1.0840675, 1.836086, 2.9328897, 3.904524, 3.4343739],
            [1.220753, 1.7573147, 3.008505, 3.7896245, 4.600788],
            [1.3292272, 1.6948014, 3.0685136, 3.6984396, 5.5264597],
        ],
        [
            [0.03080546, 1.01156497, 3.30827889, 3.27796478, 5.64089073],
            [2.96707199, 1.77546528, 2.90155831, 3.6526126, 5.10329182],
            [0.03080546, 1.01156497, 3.30827889, 3.27796478, 5.64089073],
            [5.90333852, 2.53936558, 2.49483774, 4.02726042, 4.56569291],
            [5.90333852, 2.53936558, 2.49483774, 4.02726042, 4.56569291],
        ],
    ]

    new_data = imageRegistration.shift_correction(
        data, numpy.outer([0.25, 0.1], numpy.arange(3))
    )
    numpy.testing.assert_allclose(new_data, expected, rtol=1e-05)


@pytest.mark.skipif(scipy is None, reason="scipy is missing")
def test_shift_detection0(tmpdir, first_frame, metadata_dict):
    """Tests the shift detection using only an axis (dimension).
    The shift is only applied to the dimension."""
    data = numpy.ndarray((10, *first_frame.shape), first_frame.dtype)
    shift = numpy.array([0.5, 0.2])
    for j in range(2):
        for i in range(0, 5):
            data[j * 5 + i] = numpy.array(
                numpy.fft.ifftn(
                    scipy.ndimage.fourier_shift(numpy.fft.fftn(first_frame), shift * i)
                ).real
            )
    data = numpy.asanyarray(data, dtype=numpy.int16)
    dataset = utils.createDataset(
        data=data, metadata_dict=metadata_dict, _dir=str(tmpdir)
    )

    dataset.find_dimensions()
    dataset.reshape_data()

    # Detects shift using only images where value 1 of dimension 1 is fixed
    optimal_shift = dataset.find_shift(selected_axis=1)

    shift = [-0.5, -0.2]

    numpy.testing.assert_allclose(shift, numpy.round(optimal_shift, 1))


@pytest.mark.skipif(scipy is None, reason="scipy is missing")
def test_shift_detection1(tmpdir, first_frame, metadata_dict):
    """Tests the shift detection using only an axis (dimension).
    The shift is applied to all the dataset."""
    data = [first_frame]
    shift = [0.5, 0.2]
    for i in range(1, 10):
        data += [
            numpy.fft.ifftn(
                scipy.ndimage.fourier_shift(numpy.fft.fftn(data[-1]), shift)
            ).real
        ]
    data = numpy.asanyarray(data, dtype=numpy.int16)
    dataset = utils.createDataset(
        data=data, metadata_dict=metadata_dict, _dir=str(tmpdir)
    )

    dataset.find_dimensions()
    dataset.reshape_data()

    # Detects shift using only images where value 1 of dimension 1 is fixed
    optimal_shift = dataset.find_shift(selected_axis=0)

    shift = [-2.5, -1]

    numpy.testing.assert_allclose(shift, numpy.round(optimal_shift, 1))


@pytest.mark.skipif(scipy is None, reason="scipy is missing")
def test_shift_correction0(tmpdir, first_frame, metadata_dict):
    """Tests the shift correction using only an axis (dimension).
    The shift is only applied to the dimension."""
    data = numpy.ndarray((10, *first_frame.shape), first_frame.dtype)

    shift = numpy.array([0.5, 0.2])
    for j in range(2):
        for i in range(0, 5):
            data[j * 5 + i] = numpy.array(
                numpy.fft.ifftn(
                    scipy.ndimage.fourier_shift(numpy.fft.fftn(first_frame), shift * i)
                ).real
            )

    data = numpy.asanyarray(data, dtype=numpy.int16)
    dataset = utils.createDataset(
        data=data, metadata_dict=metadata_dict, _dir=str(tmpdir)
    )

    dataset.find_dimensions()
    dataset.reshape_data()

    dataset.find_and_apply_shift(selected_axis=1, shift_approach="fft")

    for frame in dataset.data.take(0, 0):
        # Check if the difference between the shifted frames and the sample frame is small enough
        numpy.testing.assert_allclose(dataset.as_array3d(0), frame, atol=6)
