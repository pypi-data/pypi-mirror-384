import numpy
import pytest

from darfix import dtypes
from darfix.tasks.datapartition import DataPartition
from darfix.tests.utils import createDataset


@pytest.fixture
def one_motor_dataset():
    # Dataset with scan shape 100, and frame shape 3,3, with frame intensity gradually increasing from 1 to 10
    return dtypes.Dataset(
        dataset=createDataset(
            data=numpy.linspace(1, 10, 100).repeat(9).reshape((100, 3, 3))
        ),
    )


def test_data_partition(one_motor_dataset):

    # test default processing
    task = DataPartition(
        inputs={
            "dataset": one_motor_dataset,
        }
    )
    task.run()

    # if no filtering then indices of all frames must exist
    numpy.testing.assert_array_equal(
        task.outputs.dataset.indices,
        numpy.arange(0, 100, step=1),
    )


def test_data_partition_with_filtering(one_motor_dataset):

    # test filtering
    task = DataPartition(
        inputs={
            "dataset": one_motor_dataset,
            "filter_bottom_bin_idx": 5,
            "filter_top_bin_idx": 45,
        },
    )
    task.run()

    # if filtering then some indices must be ignored
    assert not numpy.array_equal(
        task.outputs.dataset.indices,
        numpy.arange(0, 100, step=1),
    )
