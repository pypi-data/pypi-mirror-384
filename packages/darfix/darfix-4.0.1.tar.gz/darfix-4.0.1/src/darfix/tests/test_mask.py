import numpy

from darfix.processing.imageOperations import mask_removal

from .utils import create_1d_dataset


def test_apply_mask_from_file(tmpdir):
    dataset = create_1d_dataset(tmpdir, motor1="diffrx", motor2="diffry")
    mask_shape = dataset.data.shape[1:]
    mask = numpy.ones(mask_shape)
    mask[20:40, 20:40] = 0

    masked_data = dataset.data.copy()
    mask_removal(masked_data, mask)
    # Do the assert frame by frame since we can't slice through DataUrls
    for i in range(len(dataset.data)):
        expected_data = dataset.data[i]
        expected_data[20:40, 20:40] = 0
        numpy.testing.assert_allclose(masked_data[i], expected_data)


def test_apply_mask_from_memory(tmpdir):
    dataset = create_1d_dataset(tmpdir, motor1="diffrx", motor2="diffry")
    mask_shape = dataset.data.shape[1:]
    mask = numpy.ones(mask_shape)
    mask[20:40, 20:40] = 0

    masked_data = dataset.data.copy()
    mask_removal(masked_data, mask)

    expected_data = dataset.data
    expected_data[:, 20:40, 20:40] = 0
    numpy.testing.assert_allclose(masked_data, expected_data)
