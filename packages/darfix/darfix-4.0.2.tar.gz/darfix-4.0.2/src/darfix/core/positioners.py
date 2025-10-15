from __future__ import annotations

import h5py
import numpy
from silx.io.dictdump import h5todict
from silx.io.url import DataUrl
from silx.io.utils import h5py_read_dataset


class Positioners:
    """
    Class to handle positioners in the hdf5

    For now only load method is available.

    Soon a save method will be implemented as well
    """

    _DATASETS_USED_FOR_TRANSFORMATION = ("mainx", "ffz", "obx", "obpitch")
    """A couple of dataset with hard-coded named used for transformation"""

    def __init__(
        self,
        url: str | DataUrl,
        data: None | dict[str, numpy.ndarray] = None,
    ):
        """
        :param url: url to load data
        :param data: data can be given if already loaded
        """
        self._constants = {}
        self._data = {}
        if not isinstance(url, DataUrl):
            url = DataUrl(url)
        self._url = url
        if data is not None:
            self._data = data
        else:
            self.load()

    def load(self):
        """
        Use url to load data
        """
        h5_positioners_dict = {}
        self._constants = {}
        self._data = {}

        with h5py.File(self._url.file_path()) as f:

            if f.attrs.get("publisher", None) == "bliss":
                h5_positioners_dict = extract_bliss_positioners(
                    f[self._url.data_path()]
                )
            else:
                h5_positioners_dict = h5todict(f, self._url.data_path())

        for key, positioner in h5_positioners_dict.items():
            if isinstance(positioner, numpy.ndarray) and positioner.size > 1:
                self._data[key] = positioner.ravel()
            elif key in Positioners._DATASETS_USED_FOR_TRANSFORMATION:
                # The motor value is constant and we need it for the Transformation
                self._constants[key] = positioner

    @property
    def url(self) -> DataUrl:
        return self._url

    @property
    def data(self) -> dict[str, numpy.ndarray]:
        return self._data

    @property
    def constants(self) -> dict[str, float]:
        """Constant for transformation like obpitch..."""
        return {**self._constants}


def extract_bliss_positioners(
    positioners: h5py.Group,
) -> dict[str, numpy.ndarray | float]:
    # Some positioners are detectors and therefore scalars in `positioners`.
    # To detect those we need to check whether the positioner has a group
    # in the instrument group.
    instrument = positioners.parent
    instrument_names = list(instrument)
    datasets = dict()

    for name in positioners:
        dset = None

        if name in instrument_names:
            group = instrument[name]
            NX_class = group.attrs.get("NX_class", None)
            try:
                if NX_class == "NXpositioner":
                    dset = group["value"]
                elif NX_class == "NXdetector":
                    dset = group["data"]
            except KeyError:
                pass

        if dset is None:
            dset = positioners[name]

        if isinstance(dset, h5py.Dataset):
            if (
                dset.ndim == 0 and name in Positioners._DATASETS_USED_FOR_TRANSFORMATION
            ) or (dset.ndim == 1):
                datasets[name] = h5py_read_dataset(dset)
    return datasets
