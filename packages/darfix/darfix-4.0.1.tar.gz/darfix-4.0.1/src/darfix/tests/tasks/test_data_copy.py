import numpy

from darfix.dtypes import Dataset
from darfix.tasks.copy import DataCopy
from darfix.tests.utils import createDataset


def test_data_copy():
    dataset = Dataset(
        dataset=createDataset(data=numpy.linspace(1, 10, 100).reshape(10, 5, 2)),
        indices=None,
        bg_dataset=numpy.ones(
            100,
        ).reshape(10, 5, 2),
        bg_indices=None,
    )

    task = DataCopy(
        inputs={
            "dataset": dataset,
        }
    )
    task.run()

    assert id(dataset) != id(task.outputs.dataset)
    assert id(dataset.dataset) != id(task.outputs.dataset.dataset)
    assert id(dataset.bg_dataset) != id(task.outputs.dataset.bg_dataset)
    assert dataset.dataset.data.shape == dataset.bg_dataset.shape
    numpy.testing.assert_array_equal(
        dataset.dataset.data, task.outputs.dataset.dataset.data
    )
    numpy.testing.assert_array_equal(
        dataset.bg_dataset, task.outputs.dataset.bg_dataset
    )
