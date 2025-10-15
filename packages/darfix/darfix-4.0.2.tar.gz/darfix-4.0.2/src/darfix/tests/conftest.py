import pytest
from silx.io.url import DataUrl
from silx.resources import ExternalResources

from ..core.data_selection import load_process_data
from . import utils


@pytest.fixture(scope="session")
def resource_files():
    try:
        from importlib.resources import files
    except ImportError:
        from importlib_resources import files

    return files


@pytest.fixture
def dataset(tmpdir):

    return utils.create_3motors_dataset(tmpdir)


@pytest.fixture
def input_dataset(tmp_path, silx_resources):
    input_filename = silx_resources.getfile("input.h5")

    detector_url = DataUrl(
        file_path=input_filename, data_path="/2.1/measurement/my_detector"
    )
    metadata_url = DataUrl(
        file_path=input_filename, data_path="/2.1/instrument/positioners"
    )

    dataset, _, _, _ = load_process_data(
        detector_url=detector_url,
        root_dir=tmp_path,
        title="input",
        metadata_url=metadata_url,
    )
    return dataset


@pytest.fixture(scope="session")
def silx_resources(tmp_path_factory):
    silx_resources = ExternalResources(
        "darfix",
        url_base="http://www.silx.org/pub/darfix",
        # Create a sub-folder to avoid name collision
        data_home=tmp_path_factory.mktemp("external"),
    )
    yield silx_resources
    silx_resources.clean_up()
