from __future__ import annotations

import logging
from typing import Any
from typing import Sequence

import numpy

from darfix.core import array_utils
from darfix.processing import dimension_detection

_logger = logging.getLogger(__file__)


class AcquisitionDims(dict):
    """
    Define the view of the data which has to be made
    """

    def add_dim(self, axis: int, dim: Dimension | dict):
        if isinstance(dim, dict):
            dim = Dimension.from_dict(dim)
        if not isinstance(dim, Dimension):
            raise TypeError(f"dim is expected to be a {Dimension}. Get {type(dim)}")
        self[axis] = dim

    def remove_dim(self, axis: int):
        if axis in self:
            del self[axis]

    @property
    def ndim(self) -> int:
        return len(self)

    def get(self, axis: int, default=None) -> Dimension | None:
        """
        Get Dimension at certain axis.

        :param int axis: axis of the dimension.
        :return: the requested dimension if exists.
        """
        assert type(axis) is int
        return super().get(axis, default)

    def get_names(self) -> list[str]:
        """
        Get list with all the names of the dimensions.

        :return: array_like of strings
        """

        return [dim.name for dim in self.values()]

    @property
    def shape(self) -> tuple[int, ...]:
        """
        Shape order is reversed from the axis so the data is correctly reshaped
        so that the dimensions which motors move first are at the last axis of the
        data. This is done to mantain the axes order as they are used to in the beamlines.

        :return: shape of the currently defined dims
        """
        shape = []
        for iDim in reversed(range(self.ndim)):
            if iDim not in self:
                shape.append(1)
            else:
                shape.append(self[iDim].size or -1)
        return tuple(shape)

    @staticmethod
    def from_dict(raw_dims: dict[int, Any]) -> AcquisitionDims:
        if not isinstance(raw_dims, dict):
            raise TypeError(f"dims should be a dictionary. Got {raw_dims}.")
        dims = AcquisitionDims()
        # sort by key (axis) to sort from fastest to slowest
        for axis in sorted(raw_dims.keys()):
            dims.add_dim(axis, raw_dims[axis])
        return dims

    def to_dict(self) -> dict:
        return {k: v.to_dict() for k, v in self.items()}


class Dimension:
    """
    Define a dimension used during the dataset

    :param str name: name of the dimension (should fit the fabioh5 mapping
                     for now)
    :param Union[int,None] size: length of the dimension.
    """

    def __init__(
        self,
        name: str,
        size: int = 0,
        start: float = 0,
        stop: float = 0,
    ):
        self.__name = name
        self._size = size
        self._start = start
        self._stop = stop

    @property
    def name(self) -> str:
        """
        Name of the dimension (Typically the name of the related positioner)
        """
        return self.__name

    @property
    def size(self) -> int:
        """
        Size of the dimension
        """
        return self._size

    @property
    def start(self) -> float:
        """
        float start value in the linspace of the dimension
        """
        return self._start

    @property
    def stop(self) -> float:
        """
        float stop value in the linspace of the dimension
        """
        return self._stop

    @property
    def step(self) -> float:
        """
        float step in the linspace of the dimension
        """
        if self._size <= 1:
            return 0.0
        return (self._stop - self._start) / (self._size - 1)

    def compute_unique_values(self) -> numpy.ndarray:
        """
        Compute a linspace with dimension parameters

        :returns numpy array: a linspace with dimension parameters

        """
        return numpy.linspace(self.start, self.stop, self._size)

    def __str__(self):
        return f"{self.name} size: {self.size}"

    def guess_parameters(self, values: Sequence[float], tolerance: float):
        """
        Guess size start and stop values of the dimension

        :param array_like values: list of values.

        :param tolerance: Tolerance to find the unique values
        """
        self._size, self._start, self._stop = (
            dimension_detection.find_linspace_parameters(values, tolerance)
        )

    def to_dict(self) -> dict[str, Any]:
        """Translate the current Dimension to a dictionary"""
        return {
            "name": self.name,
            "size": self.size,
            "start": self.start,
            "stop": self.stop,
        }

    @staticmethod
    def from_dict(_dict: dict) -> Dimension:
        """
        This initialize a new dimension instance from a dict.

        Note :

        In darfix 2.x the dimension had a 'range' attribute and since darfix 3.0, 'range' is replaced by 'start and 'stop' attributes.
        This method also ensure old save from a 2.x darfix program can still be readable.

        :param dict _dict: dict defining the dimension. Should contains the
                            following keys: name, size, start and stop.

        :return dimension instance: A new dimension instance
        """

        assert type(_dict) is dict
        if not ("name" in _dict) or not ("size" in _dict):
            raise ValueError(
                "unable to create a valid dim object because 'name' or 'size' is missing"
            )

        if "range" in _dict:
            # darfix 2.x
            if not isinstance(_dict["range"], list) or len(_dict["range"]) != 3:
                raise ValueError(
                    "unable to create a valid dim object because 'range' is not a list of size 3"
                )

            dim = Dimension(
                name=_dict["name"],
                size=_dict["size"],
                start=_dict["range"][0],
                stop=_dict["range"][1],
            )
        else:
            # darfix 3.x
            if not ("start" in _dict) or not ("stop" in _dict):
                raise ValueError(
                    "unable to create a valid dim object because 'start' or 'stop' is missing"
                )
            dim = Dimension(
                name=_dict["name"],
                size=_dict["size"],
                start=_dict["start"],
                stop=_dict["stop"],
            )

        return dim


def find_dimensions_from_metadata(
    metadata: dict[str, numpy.ndarray], tolerance: float
) -> AcquisitionDims:

    dims = AcquisitionDims()

    dimensions = []

    # For every key that has more than one different value, create a new Dimension.
    for key, values in metadata.items():

        dataset_size = len(values)

        unique_values, unique_counts = array_utils.unique(values, return_counts=True)
        if len(unique_values) == 0:
            continue
        if unique_counts[0] == dataset_size:
            continue
        if not numpy.issubdtype(unique_values.dtype, numpy.number):
            continue
        dimension = Dimension(key)
        dimension.guess_parameters(values, tolerance)
        _logger.info(
            "Axis %d: dimension '%s' with %d unique values",
            len(dimensions),
            key,
            len(unique_values),
        )

        # Value that tells when does the change of value occur. It is used to know the order
        # of the reshaping.
        dimension.changing_value = __compute_changing_value(values)
        dimensions.append(dimension)

    for dimension in sorted(dimensions, key=lambda x: x.changing_value, reverse=True):
        dims.add_dim(axis=dims.ndim, dim=dimension)
        _logger.info(
            "Dimension %s of size %d has been added for reshaping",
            dimension.name,
            dimension.size,
        )
    return dims


def __compute_changing_value(values, changing_value=1):
    """
    Recursive method used to calculate how fast is a dimension. The speed of a dimension is the number of
    times the dimension changes of value while moving through the dataset.
    """
    if len(numpy.unique(values)) > 1:
        return __compute_changing_value(
            values[: int(len(values) / 2)], changing_value + 1
        )
    else:
        return changing_value
