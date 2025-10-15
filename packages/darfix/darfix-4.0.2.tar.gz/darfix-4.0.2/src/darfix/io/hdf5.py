from __future__ import annotations

import functools
import os.path
from contextlib import AbstractContextManager
from typing import Union

import h5py
from silx.io import utils
from silx.io.url import DataUrl


def is_hdf5(url: Union[DataUrl, str]) -> bool:
    if isinstance(url, DataUrl):
        file_path = url.file_path()
    else:
        try:
            data_url = DataUrl(path=url)
        except Exception:
            file_path = url
        else:
            file_path = data_url.file_path()

    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find {file_path}")

    return h5py.is_hdf5(file_path)


class hdf5_file_cache(AbstractContextManager):
    """
    Context manager that keep the last (HDF5) file used open and keeps a pointer to the last dataset read.

    The goal it to speed up reading from hdf5 dataset. As we expect in most of the case to have a single file.

    File will be closed when leaving the context manager.
    Before this PR most of the time was spend on h5py.__getitem__. This function includes:

    solving dataset path, external links (VDS).
    Keeping a pointer to the latest dataset will avoid doing the data path resolution but more importantly
    when it reads an external link or a VDS it will keep the virtual source origin file open.
    And avoid opening and closing the file.

    For safety all this mechanism is done in a context manager to make sure the files ares properly closed
    after processing or if any exception occurs during reading.

    Note: we expect this class to be removed once the io mechanism will be reworked.
    """

    def __enter__(self):
        self.__h5_file = None
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_h5_file()

    def close_h5_file(self):
        if self.__h5_file:
            self.__h5_file.close()
        self.__h5_file = None

    @functools.lru_cache(maxsize=1)
    def open_file(self, file_path: str):
        """cache the latest HDF5 file open"""
        self.close_h5_file()
        self.__h5_file = h5py.File(file_path, mode="r")
        return self.__h5_file

    @functools.lru_cache(maxsize=1)
    def _get_h5py_object(
        self, file_path: str, data_path: str
    ) -> h5py.Group | h5py.Dataset:
        """
        Return the h5py Object (Group or Dataset) at the given position.
        """
        h5f = self.open_file(file_path)
        if data_path not in h5f:
            raise KeyError(f"Data path from URL '{data_path}' not found")
        return h5f[data_path]

    def get_data(self, url: DataUrl):
        """
        Retrieve data contained in 'url'.
        """
        if url.scheme() == "silx":

            data = self._get_h5py_object(
                file_path=url.file_path(),
                data_path=url.data_path(),
            )

            if not utils.is_dataset(data):
                raise ValueError(f"Data path from URL '{url.path()}' is not a dataset")

            data_slice = url.data_slice()
            if data_slice is not None:
                return utils.h5py_read_dataset(data, index=data_slice)
            else:
                # works for scalar and array
                return utils.h5py_read_dataset(data)
        else:
            return utils.get_data(url=url)
