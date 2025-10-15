import os
import urllib.parse
import urllib.request
from typing import Optional
from typing import Union

from silx.io.url import DataUrl

from darfix.core.dataset import ImageDataset


def load_process_data(
    detector_url: Union[str, DataUrl],
    root_dir: Optional[str] = None,
    dark_detector_url: Optional[Union[str, DataUrl]] = None,
    title: str = "",
    metadata_url=None,
):
    """
    Loads data from `detector_url`.
    If `detector_url` is:

        - a str: consider it as a file pattern (for EDF files).
        - a DataUrl: consider it readable by silx `get_data` function

    :param detector_url: detector_url to be loaded.
    :param metadata_url: path to the scan metadata for HDF5 containing positioner information in order to load metadata for non-edf files
    """
    indices = li_indices = None
    root_dir_specified = bool(root_dir)

    if isinstance(detector_url, DataUrl):
        assert detector_url.file_path() not in (
            "",
            None,
        ), "no file_path provided to the DataUrl"
        if not root_dir_specified:
            root_dir = os.path.dirname(detector_url.file_path())
        dataset = ImageDataset(
            _dir=root_dir,
            detector_url=detector_url,
            title=title,
            metadata_url=metadata_url,
        )
    elif isinstance(detector_url, str):
        if not detector_url:
            raise ValueError("'detector_url' cannot be an empty string")
        if not root_dir_specified:
            root_dir = _get_root_dir(detector_url)
        dataset = ImageDataset(
            _dir=root_dir,
            detector_url=detector_url,
            title=title,
            metadata_url=metadata_url,
        )
    else:
        raise TypeError(
            f"Expected detector_url to be a string or a silx DataUrl. Got {type(detector_url)} instead."
        )

    if not dark_detector_url:
        bg_dataset = None
    elif isinstance(dark_detector_url, str):
        dark_root_dir = os.path.join(dataset.dir, "dark")
        os.makedirs(dark_root_dir, exist_ok=True)
        bg_dataset = ImageDataset(
            _dir=dark_root_dir,
            detector_url=dark_detector_url,
            metadata_url=None,
        )
    elif isinstance(dark_detector_url, DataUrl):
        assert dark_detector_url.file_path() not in (
            "",
            None,
        ), "no file_path provided to the DataUrl"
        dark_root_dir = os.path.join(dataset.dir, "dark")
        os.makedirs(dark_root_dir, exist_ok=True)
        bg_dataset = ImageDataset(
            _dir=dark_root_dir,
            detector_url=dark_detector_url,
            metadata_url=None,
        )
    else:
        raise TypeError(
            f"Expected dark_detector_url to be a string or a silx DataUrl. Got {type(dark_detector_url)} instead."
        )

    assert dataset.data is not None and dataset.data.size > 0, "No data was loaded!"

    return dataset, indices, li_indices, bg_dataset


def _get_root_dir(filename: str) -> str:
    url = urllib.parse.urlparse(filename, scheme="file")
    return os.path.dirname(urllib.request.url2pathname(url.path))
