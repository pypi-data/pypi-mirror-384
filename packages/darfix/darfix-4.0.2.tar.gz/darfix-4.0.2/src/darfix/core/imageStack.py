from __future__ import annotations

from typing import NamedTuple
from typing import Sequence

import numpy


class FixedDimension(NamedTuple):
    """
    A data class to describe a fixed dimension. Used as a parameter for ImageStack::filter_indices().

    This is used when we want to filter the image stack by one of the dimension.

    For instance, in my dataset dimensions, i have two motors `motor_slow` and `motor_fast`

    motor_fast
    - axis = 0
    - size : 3
    - linspace : 1, 2, 3

    motor_slow
    - axis = 1
    - size : 4
    - linspace : 0.5, 1, 1.5, 2

    Let say we want images indice of my dataset only when `motor_slow` value = 1.5

    `motor_slow` axis is 1 and value 1.5 is at index 2.

    So, I can use dataset.filter_indices(FixedDimension(axis = 1, index = 2))
    """

    axis: int
    index: int

    def get_reversed_axis(self, ndim: int) -> int:
        """
        In darfix Dimension class, `axis` =  Ndim - real_data_array_axis - 1.
        This is due to legacy.
        """
        assert ndim - self.axis - 1 >= 0
        return ndim - self.axis - 1

    @staticmethod
    def from_iterable(dimension: Sequence[int | Sequence[int]]) -> FixedDimension:
        # this is not really ideal but as for now dimension type is a mess in the code i prefere do all the dirty code here
        assert len(dimension) == 2
        dim0, dim1 = dimension
        axis = dim0 if isinstance(dim0, int) else dim0[0]
        index = dim1 if isinstance(dim1, int) else dim1[0]
        return FixedDimension(axis, index)


class ImageStack:
    def __init__(self, data: numpy.ndarray):
        self._data = data

    @property
    def nframes(self) -> int:
        """
        Return number of frames
        """
        return int(numpy.prod(self.scan_shape))

    @property
    def scan_shape(self) -> tuple:
        return self.data.shape[:-2]

    @property
    def frame_shape(self) -> tuple:
        return self.data.shape[-2:]

    @property
    def data(self) -> numpy.ndarray:
        return self._data

    def as_array3d(self, indices=None) -> numpy.ndarray:
        if indices is None:
            indices = Ellipsis
        return self._data.reshape((self.nframes,) + self.frame_shape)[indices]

    def as_array2d(self, indices=None) -> numpy.ndarray:
        if indices is None:
            indices = Ellipsis
        return self._data.reshape((self.nframes, self.data.size // self.nframes))[
            indices
        ]

    def filter_indices(
        self,
        indices: numpy.ndarray | None = None,
        fixed_dimension: FixedDimension | Sequence | None = None,
    ) -> numpy.ndarray:
        """
        :return selected_indices: a list of indices filtered by input `indices` and optionally filtered with one fixed dimension `fixed_dimension`. If inputs are None return the full range of indices.
        """
        if fixed_dimension is not None and not isinstance(
            fixed_dimension, FixedDimension
        ):
            fixed_dimension = FixedDimension.from_iterable(fixed_dimension)

        all_indices = numpy.arange(self.nframes)
        selected_indices = indices if indices is not None else all_indices

        if fixed_dimension is None or len(self._data.shape) <= 3:
            return selected_indices

        # Take indices with one fixed dimension
        filtered_by_dim_indices = all_indices.reshape(self.scan_shape)
        filtered_by_dim_indices = filtered_by_dim_indices.take(
            indices=fixed_dimension.index,
            axis=fixed_dimension.get_reversed_axis(self._data.ndim - 2),
        )
        filtered_by_dim_indices = filtered_by_dim_indices.flatten()

        selected_indices = numpy.intersect1d(
            selected_indices, filtered_by_dim_indices, assume_unique=True
        )

        return selected_indices

    def get_filtered_data(
        self,
        indices: numpy.ndarray | None = None,
        fixed_dimension: FixedDimension | None = None,
    ):
        return self.as_array3d()[
            self.filter_indices(indices=indices, fixed_dimension=fixed_dimension)
        ]
