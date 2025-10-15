import numpy

from darfix.core.zigzag_mode import reorder_frames_of_zigzag_scan
from darfix.tests.utils import createHDF5Dataset

DIM_SLOW_NPOINTS = 10
DIM_FAST_NPOINTS = 5
SCANS_COUNT = DIM_SLOW_NPOINTS * DIM_FAST_NPOINTS
FRAME_SHAPE = (2, 2)

TOLERANCE = 1e-9


def test_zigzag():

    motor_slow = numpy.linspace(1, 4, DIM_SLOW_NPOINTS).repeat(DIM_FAST_NPOINTS)
    motor_fast = numpy.tile(numpy.linspace(10, 12, DIM_FAST_NPOINTS), DIM_SLOW_NPOINTS)

    # Generate random noise in the range of [-1e-8, 1e-8]
    noise1 = numpy.random.uniform(-TOLERANCE / 2, TOLERANCE / 2, (SCANS_COUNT,))
    noise2 = numpy.random.uniform(-TOLERANCE / 2, TOLERANCE / 2, (SCANS_COUNT,))

    motor_slow = motor_slow + noise1
    motor_fast = motor_fast + noise2

    motor_fast = motor_fast.reshape((DIM_SLOW_NPOINTS, DIM_FAST_NPOINTS))
    motor_fast[1::2][:] = motor_fast[1::2, ::-1]
    motor_fast = motor_fast.flatten()

    frame = numpy.arange(1, SCANS_COUNT + 1)
    scans = frame[:, numpy.newaxis, numpy.newaxis] * numpy.ones(FRAME_SHAPE)

    dataset = createHDF5Dataset(
        scans, {"motor_fast": motor_fast, "motor_slow": motor_slow}
    )

    dataset.find_dimensions(TOLERANCE)

    assert dataset.dims[0].name == "motor_fast"
    assert dataset.dims[0].size == DIM_FAST_NPOINTS
    assert dataset.dims[1].name == "motor_slow"
    assert dataset.dims[1].size == DIM_SLOW_NPOINTS

    metadata_dict_before = dataset.metadata_dict.copy()

    reorder_frames_of_zigzag_scan(dataset.dims, dataset)

    for i in range(DIM_SLOW_NPOINTS):
        if i % 2 == 0:
            continue
        for y in range(DIM_FAST_NPOINTS):
            index = i * DIM_FAST_NPOINTS + y
            index_reverse = i * DIM_FAST_NPOINTS + (DIM_FAST_NPOINTS - 1 - y)
            numpy.testing.assert_array_equal(scans[index], dataset.data[index_reverse])
            assert (
                metadata_dict_before["motor_fast"][index]
                == dataset.metadata_dict["motor_fast"][index_reverse]
            )
            assert (
                metadata_dict_before["motor_slow"][index]
                == dataset.metadata_dict["motor_slow"][index_reverse]
            )
