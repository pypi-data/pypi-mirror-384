import os
from copy import deepcopy

import numpy
import pytest
from ewokscore.missing_data import MISSING_DATA

from darfix import dtypes
from darfix.tasks.dimensiondefinition import DimensionDefinition
from darfix.tests.utils import create_3_motors_metadata
from darfix.tests.utils import createDataset


@pytest.mark.parametrize("pre_compute_dims", (True, False))
def test_dimension_definition(tmp_path, pre_compute_dims):
    output_dir = os.path.join(tmp_path, "test_dimension_definition")
    os.makedirs(output_dir, exist_ok=True)

    metadata_dict = create_3_motors_metadata("obpitch", "z", "m", 2, 5, 2)
    data = numpy.zeros((20, 10, 100))
    darfix_dataset = createDataset(
        data=data, metadata_dict=metadata_dict, _dir=output_dir
    )

    if pre_compute_dims:
        darfix_dataset.find_dimensions()
        dataset_dims = deepcopy(darfix_dataset.dims)
    else:
        dataset_dims = MISSING_DATA

    dataset = dtypes.Dataset(dataset=darfix_dataset)

    task = DimensionDefinition(
        inputs={
            "dataset": dataset,
            "dims": dataset_dims,
        }
    )
    task.run()
    assert isinstance(task.outputs.dataset, dtypes.Dataset)
    assert len(task.outputs.dataset.dataset.dims) == 3
    assert task.outputs.dataset.dataset.dims[0].name == "m"
    assert task.outputs.dataset.dataset.dims[1].name == "z"
    assert task.outputs.dataset.dataset.dims[2].name == "obpitch"
