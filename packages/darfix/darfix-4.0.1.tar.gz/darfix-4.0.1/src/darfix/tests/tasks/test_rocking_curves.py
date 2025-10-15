import warnings
from pathlib import Path

import h5py
import numpy
from scipy.optimize import OptimizeWarning

from darfix.core.rocking_curves import Maps_2D
from darfix.dtypes import Dataset
from darfix.tasks.rocking_curves import RockingCurves


def test_rocking_curves(input_dataset, tmp_path):
    output_filename = tmp_path / "rocking_curves.h5"
    input_dataset.find_dimensions()
    input_dataset.reshape_data()
    task = RockingCurves(
        inputs={
            "dataset": Dataset(input_dataset),
            "method": "lm",
            "output_filename": output_filename,
            "int_thresh": 15,
        }
    )
    with warnings.catch_warnings():
        warnings.simplefilter("always", RuntimeWarning)
        warnings.simplefilter("always", OptimizeWarning)
        task.run()

    assert isinstance(task.get_output_value("maps"), numpy.ndarray)
    assert isinstance(task.get_output_value("dataset"), Dataset)
    assert output_filename.is_file()
    with h5py.File(output_filename, "r") as output_file:
        output_entry = output_file["entry"]
        for map_name in Maps_2D.values():
            assert map_name in output_entry
        assert "Residuals" in output_entry


def test_rocking_curves_no_save(input_dataset):
    input_dataset.find_dimensions()
    input_dataset.reshape_data()
    task = RockingCurves(
        inputs={
            "dataset": Dataset(input_dataset),
            "method": "lm",
            "output_filename": None,
            "int_thresh": 15,
        }
    )
    with warnings.catch_warnings():
        warnings.simplefilter("always", RuntimeWarning)
        warnings.simplefilter("always", OptimizeWarning)
        task.run()

    assert isinstance(task.get_output_value("maps"), numpy.ndarray)
    assert isinstance(task.get_output_value("dataset"), Dataset)
    default_filename = Path(input_dataset._dir) / "rocking_curves.h5"
    assert not default_filename.is_file()
