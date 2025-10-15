import numpy

from ..dtypes import Dataset
from ..pixel_sizes import PixelSize
from ..tasks.rsm_histogram import RSMHistogram
from .utils import create_dataset_for_RSM


def test_rsm_histogram(tmpdir):
    dataset = create_dataset_for_RSM(tmpdir)
    dataset.find_dimensions()
    dataset.compute_transformation(PixelSize["Basler"].value, kind="rsm")

    arr, edges = dataset.compute_rsm(
        Q=(1, 0, 1),
        a=4.08,
        map_range=0.008,
        pixel_size=0.051,
        units="poulsen",
        n=(0, 1, 0),
        map_shape=(200, 200, 200),
    )
    assert isinstance(arr, numpy.ndarray)
    assert len(edges) > 0
    assert isinstance(edges[0], numpy.ndarray)


def test_ewoks_task(tmpdir):
    dataset = create_dataset_for_RSM(tmpdir)
    dataset.find_dimensions()
    dataset.compute_transformation(PixelSize["Basler"].value, kind="rsm")

    task = RSMHistogram(
        inputs=dict(
            dataset=Dataset(dataset),
            Q=(1, 0, 1),
            a=4.08,
            map_range=0.008,
            detector="Basler",
        )
    )
    task.execute()
    values = task.get_output_value("hist_values")
    assert isinstance(values, numpy.ndarray)
    edges = task.get_output_value("hist_edges")
    assert len(edges) > 0
    assert isinstance(edges[0], numpy.ndarray)
