import numpy
import pytest

from darfix.core.utils import NoDimensionsError

from .utils import create_2_motors_metadata
from .utils import createDataset

N_FRAMES_DIM0 = 10
N_FRAMES_DIM1 = 5


@pytest.fixture
def dataset(tmpdir):
    n_frames = N_FRAMES_DIM0 * N_FRAMES_DIM1
    dims = (n_frames, 100, 100)
    data = numpy.zeros(dims)

    for i in range(n_frames):
        data[i] = i

    dataset = createDataset(
        data=data,
        metadata_dict=create_2_motors_metadata(N_FRAMES_DIM1, N_FRAMES_DIM0),
        _dir=str(tmpdir),
    )
    return dataset


def test_project_data(dataset):
    data = dataset.as_array3d()

    with pytest.raises(NoDimensionsError):
        proj_data = dataset.project_data(dimension=[0])

    dataset.find_dimensions()
    dataset.reshape_data()
    assert len(dataset.dims) == 2

    proj_dataset = dataset.project_data(dimension=[0])
    assert len(proj_dataset.dims) == 1
    assert proj_dataset.dims[0] == dataset.dims[0]
    proj_data = proj_dataset.as_array3d()
    for i in range(N_FRAMES_DIM0):
        numpy.testing.assert_allclose(proj_data[i], data[i::N_FRAMES_DIM0].sum(axis=0))

    proj_dataset = dataset.project_data(dimension=[1])
    assert len(proj_dataset.dims) == 1
    assert proj_dataset.dims[0] == dataset.dims[1]
    proj_data = proj_dataset.as_array3d()
    for i in range(N_FRAMES_DIM1):
        numpy.testing.assert_allclose(
            proj_data[i],
            data[i * N_FRAMES_DIM0 : (i + 1) * N_FRAMES_DIM0].sum(axis=0),
        )
