import os

import h5py
import numpy
from ewoksorange.tests.conftest import qtapp  # noqa F401
from silx.io.url import DataUrl

from orangecontrib.darfix.widgets.dimensions import DimensionWidgetOW

try:
    from importlib.resources import files as resource_files
except ImportError:
    from importlib_resources import files as resource_files

import darfix.resources.tests
from darfix.dtypes import Dataset
from darfix.dtypes import ImageDataset


def test_dimension_NiTi_1PD_002_g411_420MPa_mosalayers_2x(tmp_path, qtapp):  # noqa F811
    """
    test dimension search with a 'real use case' motor positions
    """
    dataset_file = resource_files(darfix.resources.tests).joinpath(
        os.path.join(
            "dimensions_definition", "NiTi_1PD_002_g411_420MPa_mosalayers_2x.h5"
        )
    )

    raw_motor_values = {}
    with h5py.File(dataset_file, mode="r") as h5f:
        raw_motor_values["chi"] = h5f["positioners/chi"][()]
        raw_motor_values["diffry"] = h5f["positioners/diffry"][()]
        raw_motor_values["difftz"] = h5f["positioners/difftz"][()]

    data_folder = tmp_path / "test_fitting"
    data_folder.mkdir()
    data_file_url = DataUrl(
        file_path=os.path.join(str(data_folder), "data.h5"),
        data_path="data",
        scheme="silx",
    )
    number_of_points = 31500
    with h5py.File(data_file_url.file_path(), mode="w") as h5f:
        h5f["data"] = numpy.random.random(number_of_points)

    dataset = Dataset(
        dataset=ImageDataset(
            detector_url=data_file_url.path(),
            metadata_url=DataUrl(
                file_path=str(dataset_file),
                data_path="positioners",
                scheme="silx",
            ).path(),
            _dir=None,
        )
    )

    widget = DimensionWidgetOW()

    def find_dimensions_for_tolerance(tolerance: float):
        widget._widget.setTolerance(tolerance=tolerance)
        widget._findDimensions()

    def check_dimensions_bounds(tolerance):
        """Make sure find_dimension is correctly fitting motor bounds"""
        # check dims object vs dataset real value
        for dim in widget._widget.dims.values():
            dim = dim.toDimension()
            numpy.testing.assert_almost_equal(
                dim.start, min(raw_motor_values[dim.name]), decimal=4
            )
            numpy.testing.assert_almost_equal(
                dim.stop, max(raw_motor_values[dim.name]), decimal=4
            )

        # check display (DimensionItem instances) vs real value
        for dim_item in widget._widget.dims.values():
            numpy.testing.assert_almost_equal(
                dim_item.start, min(raw_motor_values[dim_item.name]), decimal=4
            )
            numpy.testing.assert_almost_equal(
                dim_item.stop, max(raw_motor_values[dim_item.name]), decimal=4
            )

    widget.setDataset(dataset=dataset)
    # check if tolerance == 1e-5
    find_dimensions_for_tolerance(tolerance=1e-5)

    check_dimensions_bounds(tolerance=1e-5)

    # check if tolerance == 1e-4
    find_dimensions_for_tolerance(tolerance=1e-4)
    check_dimensions_bounds(tolerance=1e-4)
