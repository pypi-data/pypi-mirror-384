import numpy

from darfix.dtypes import Dataset
from darfix.tasks.binning import Binning
from darfix.tests.utils import createDataset


def test_binning(tmp_path):
    data = numpy.array(
        [
            [
                [1, 2, 3, 4],
                [2, 2, 3, 4],
                [3, 2, 3, 4],
                [4, 2, 3, 4],
            ],
            [
                [5, 6, 7, 8],
                [5, 6, 7, 8],
                [5, 6, 7, 8],
                [5, 6, 7, 8],
            ],
            [
                [9, 10, 11, 12],
                [9, 10, 11, 12],
                [9, 10, 11, 12],
                [9, 10, 11, 12],
            ],
        ]
    )

    dataset = createDataset(data)

    task = Binning(
        inputs={
            "dataset": Dataset(dataset),
            "scale": 0.5,
        }
    )
    task.run()

    new_dataset = task.outputs.dataset.dataset

    numpy.testing.assert_array_equal(
        new_dataset.data,
        [
            [
                [1, 3],
                [2, 3],
            ],
            [
                [5, 7],
                [5, 7],
            ],
            [
                [9, 11],
                [9, 11],
            ],
        ],
    )
