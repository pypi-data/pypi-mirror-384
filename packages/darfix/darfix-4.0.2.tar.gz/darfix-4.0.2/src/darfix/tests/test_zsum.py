import numpy

from darfix.core.imageStack import FixedDimension


def test_zsum(dataset):
    indices = [1, 2, 3, 6]

    dataset.find_dimensions()
    dataset.reshape_data()
    result = numpy.sum(
        dataset.get_filtered_data(
            fixed_dimension=FixedDimension(0, 1), indices=indices
        ),
        axis=0,
    )
    zsum = dataset.zsum(indices=indices, dimension=FixedDimension(0, 1))
    numpy.testing.assert_array_equal(zsum, result)
