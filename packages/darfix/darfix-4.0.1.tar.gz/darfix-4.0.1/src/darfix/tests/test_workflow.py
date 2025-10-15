import numpy
import pytest

try:
    import scipy
except ImportError:
    pytest.skip("scipy is missing", allow_module_level=True)

from darfix.core import roi
from darfix.processing import imageOperations
from darfix.tests import utils


@pytest.fixture
def dataset(tmpdir):
    first_frame = numpy.zeros((100, 100))
    # Simulating a series of frame with information in the middle.
    first_frame[25:75, 25:75] = numpy.random.randint(50, 300, size=(50, 50))
    data = [first_frame]
    shift = [1.0, 0]
    for i in range(9):
        data += [
            numpy.fft.ifftn(
                scipy.ndimage.fourier_shift(numpy.fft.fftn(data[-1]), shift)
            ).real
        ]
    data = numpy.asanyarray(data, dtype=numpy.int16)
    return utils.createDataset(data=data, _dir=str(tmpdir))


@pytest.fixture
def dark_dataset(tmpdir):
    background = [
        numpy.random.randint(-5, 5, size=(100, 100), dtype="int16") for i in range(5)
    ]
    return utils.createDataset(data=background, _dir=str(tmpdir))


def test_workflow0(dataset, dark_dataset):
    """Tests a possible workflow"""

    expected = numpy.subtract(
        dataset.data[:, 49:52, 50:51],
        numpy.median(dark_dataset.data[:, 49:52, 50:51], axis=0).astype(numpy.int16),
        dtype=numpy.int64,
    ).astype(numpy.int16)
    expected[expected > 20] = 0
    expected[expected < 1] = 0
    # ROI of the data
    data = roi.apply_3D_ROI(
        dataset.data,
        size=[3, 3],
        center=(numpy.array(dataset.data[0].shape) / 2).astype(int),
    )

    # ROI of the dark frames
    dark_frames = roi.apply_3D_ROI(
        numpy.array(dark_dataset.data),
        size=[3, 3],
        center=(numpy.array(dark_dataset.data[0].shape) / 2).astype(int),
    )

    # Background substraction of the data
    imageOperations.background_subtraction(
        data, imageOperations.compute_background(dark_frames, "median")
    )
    # ROI of the data
    data = roi.apply_3D_ROI(
        data, size=[3, 1], center=(numpy.array(data[0].shape) / 2).astype(int)
    )
    # Threshold removal of the data
    imageOperations.threshold_removal(data, 1, 20)
    numpy.testing.assert_array_equal(data, expected)


def test_workflow1(dataset, dark_dataset):
    """Tests a possible workflow"""

    first_frame = numpy.asarray(dataset.data[0])
    expected = (
        numpy.tile(first_frame, (10, 1))
        .reshape(10, 100, 100)[:, 25:75, 25:75]
        .astype(numpy.float32)
    ).copy()
    # Detect and apply the shift
    dataset.find_and_apply_shift()
    # ROI of the data
    dataset = dataset.apply_roi(
        size=[50, 50],
        center=(numpy.array(dataset.data[0].shape) / 2).astype(int),
    )

    numpy.testing.assert_allclose(
        dataset.data[0, 0:10, 0:10], expected[0, 0:10, 0:10], rtol=0.1
    )
