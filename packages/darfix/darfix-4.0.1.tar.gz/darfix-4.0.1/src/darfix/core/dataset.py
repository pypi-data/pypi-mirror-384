from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Tuple

import numpy
import tqdm
from silx.io import open
from silx.io import utils
from silx.io.dictdump import dicttoh5
from silx.io.dictdump import h5todict
from silx.io.url import DataUrl
from sklearn import decomposition
from sklearn.exceptions import ConvergenceWarning

from darfix import __version__
from darfix.core.dimension import AcquisitionDims
from darfix.core.dimension import find_dimensions_from_metadata
from darfix.core.imageRegistration import apply_opencv_shift
from darfix.core.imageRegistration import shift_detection
from darfix.core.imageStack import ImageStack
from darfix.core.mapping import calculate_RSM_histogram
from darfix.core.mapping import compute_magnification
from darfix.core.mapping import compute_moments
from darfix.core.mapping import compute_rsm
from darfix.core.positioners import Positioners
from darfix.core.rocking_curves import fit_1d_data
from darfix.core.rocking_curves import fit_2d_data
from darfix.core.rocking_curves import fit_3d_data
from darfix.core.roi import apply_2D_ROI
from darfix.core.roi import apply_3D_ROI
from darfix.core.state_of_operation import Operation
from darfix.core.state_of_operation import StateOfOperations
from darfix.core.utils import NoDimensionsError
from darfix.core.utils import TooManyDimensionsForRockingCurvesError
from darfix.decomposition.nica import NICA
from darfix.io import utils as io_utils_legacy
from darfix.processing.imageOperations import threshold_removal

from ..math import Vector3D
from .transformation import Transformation

_logger = logging.getLogger(__file__)

CHUNK_SIZE = 100


def _read_data_by_chunk(detector_url: DataUrl | str) -> numpy.ndarray:
    if isinstance(detector_url, DataUrl):
        detector_url = detector_url.path()
    with open(detector_url) as detector_data:
        raw_data = numpy.ndarray(detector_data.shape, detector_data.dtype)
        n_frames = detector_data.shape[0]
        if n_frames > CHUNK_SIZE:
            n_chunk = n_frames // CHUNK_SIZE
            # Iterate by chunk of CHUNK_SIZE
            for i_chunk in tqdm.tqdm(
                range(n_chunk), desc="Read data by chunk", total=n_chunk
            ):
                chunk_slice = slice(i_chunk * CHUNK_SIZE, (i_chunk + 1) * CHUNK_SIZE)
                raw_data[chunk_slice] = detector_data[chunk_slice]
            # Last frames
            chunk_slice = slice(n_chunk * CHUNK_SIZE, None)
            raw_data[chunk_slice] = detector_data[chunk_slice]
            return raw_data
        # In case there is only a few frames (less than CHUNK_SIZE)
        return utils.h5py_read_dataset(detector_data)


class ImageDataset(ImageStack):
    """Class to define a darfix dataset.

    :param _dir: Global directory to use and save all the data in the different
        operations.
    :param raw_data: If not None, set detector data to this numpy array.
    :param detector_url: data url of the detector data. Either `raw_data` or `detector_url` should be given.
    :param dims: Dimensions dictionary
    :param transformation: Axes to use when displaying the images
    :param metadata_url: url to the metadata
    :param positioners: positioners metadata instance
    .. warning::

        When loading the full dataset will be store to memory.
    """

    def __init__(
        self,
        _dir: str,
        raw_data: numpy.ndarray | None = None,
        detector_url: str | DataUrl | None = None,
        dims: AcquisitionDims | None = None,
        transformation: numpy.ndarray | None = None,
        title: str | None = None,
        metadata_url: DataUrl | str | None = None,
        positioners: Positioners | None = None,
    ):

        if raw_data is None:
            raw_data = _read_data_by_chunk(detector_url)
        super().__init__(raw_data)

        self._frames_intensity = []
        self.moments_dims = {}
        self.state_of_operations = StateOfOperations()
        self._dir = _dir
        self._transformation = transformation
        self._title = title or ""

        if dims is None:
            self.__dims = AcquisitionDims()
        else:
            assert isinstance(
                dims, AcquisitionDims
            ), "Attribute dims has to be of class AcquisitionDims"
            self.__dims = dims
        # Keys: dimensions names, values: dimensions values
        self._dimensions_values = {}

        if positioners is not None and metadata_url is not None:
            raise ValueError("Cannot set both positioners and metadata_url")

        if positioners is not None:
            self._positioners = positioners
        elif metadata_url is not None:

            self._positioners = Positioners(metadata_url)
        else:
            # No metadata in Dark dataset for instance
            self._positioners = None

    def stop_operation(self, operation):
        """
        Method used for cases where threads are created to apply functions to the dataset.
        If method is called, the flag concerning the stop is set to 0 so that if the concerned
        operation is running in another thread it knows to stop.

        :param int operation: operation to stop
        :type int: Union[int, `Operation`]
        """
        if self.state_of_operations.is_running(operation):
            self.state_of_operations.stop(operation)

    @property
    def transformation(self):
        return self._transformation

    @transformation.setter
    def transformation(self, value):
        self._transformation = value

    @property
    def title(self):
        return self._title

    @property
    def metadata_url(self) -> DataUrl | None:
        if self._positioners is None:
            return None
        return self._positioners.url

    @property
    def dir(self):
        return self._dir

    @property
    def metadata_dict(self) -> dict[str, numpy.ndarray]:
        if self._positioners is None:
            return {}
        return self._positioners.data

    def compute_frames_intensity(self, kernel=(3, 3), sigma=20):
        """
        Returns for every image a number representing its intensity. This number
        is obtained by first blurring the image and then computing its variance.
        """
        _logger.info("Computing intensity per frame")
        io_utils_legacy.advancement_display(0, self.nframes, "Computing intensity")
        frames_intensity = []
        with self.state_of_operations.run_context(Operation.PARTITION):
            for i in range(self.nframes):
                import cv2

                if not self.state_of_operations.is_running(Operation.PARTITION):
                    return
                frames_intensity += [
                    cv2.GaussianBlur(self.as_array3d(i), kernel, sigma).var()
                ]
                io_utils_legacy.advancement_display(
                    i + 1, self.nframes, "Computing intensity"
                )
            self._frames_intensity = frames_intensity
            return frames_intensity

    def partition_by_intensity(
        self,
        bins: Optional[int] = None,
        bottom_bin: Optional[int] = None,
        top_bin: Optional[int] = None,
    ):
        """
        :param bins: number of bins to used for computing the frame intensity histogram
        :param bottom_bin: index of the bins to retrieve bottom threshold filter value. If not provided, there will be no bottom threshold (default).
        :param top_bin: index of the bins to retrieve top threshold filter value. If not provided, there will be no top threshold (default).

        Function that computes the data from the set of urls.
        If the filter_data flag is activated it filters the data following the next:
        -- First, it computes the intensity for each frame, by calculating the variance after
        passing a gaussian filter.
        -- Second, computes the histogram of the intensity.
        -- Finally, saves the data of the frames with an intensity bigger than a threshold.
        The threshold is set to be the second bin of the histogram.
        """
        frames_intensity = (
            self._frames_intensity
            if self._frames_intensity
            else self.compute_frames_intensity()
        )
        if frames_intensity is None:
            return
        _, bins = numpy.histogram(
            frames_intensity, self.nframes if bins is None else bins
        )
        frames_intensity = numpy.asanyarray(frames_intensity)
        if top_bin is None:
            top_bin = len(bins) - 1
        if bottom_bin is None:
            bottom_bin = 0

        bottom_threshold = frames_intensity >= bins[bottom_bin]
        top_threshold = frames_intensity <= bins[top_bin]
        threshold = numpy.array(
            [a and b for a, b in zip(bottom_threshold, top_threshold)]
        )
        return numpy.flatnonzero(threshold), numpy.flatnonzero(~threshold)

    def copy(
        self,
        new_dir: str | None = None,
        new_data: numpy.ndarray | None = None,
        new_positioners: Positioners | None = None,
        new_transformation: numpy.ndarray | None = None,
        new_dims: AcquisitionDims | None = None,
    ) -> ImageDataset:
        new_dataset = ImageDataset(
            _dir=new_dir if new_dir is not None else self._dir,
            raw_data=new_data if new_data is not None else self._data,
            positioners=(
                new_positioners if new_positioners is not None else self._positioners
            ),
            transformation=(
                new_transformation
                if new_transformation is not None
                else self._transformation
            ),
            dims=new_dims if new_dims is not None else self.__dims,
            title=self._title,
        )
        new_dataset.reshape_data()
        return new_dataset

    @property
    def dims(self):
        return self.__dims

    @dims.setter
    def dims(self, _dims):
        if not isinstance(_dims, AcquisitionDims):
            raise TypeError(
                "Dimensions dictionary has " "to be of class `AcquisitionDims`"
            )
        self.__dims = _dims

    def zsum(self, indices=None, dimension=None) -> numpy.ndarray:
        data = self.get_filtered_data(indices, dimension)
        return data.sum(axis=0)

    def reshape_data(self):
        """
        Function that reshapes the data to fit the dimensions.
        """
        if self.dims.ndim == 0:
            # No dimension => reshape to simple 3d array
            dims_shape = (self.nframes,)
        else:
            dims_shape = self.__dims.shape

        try:
            self._data = self.as_array3d().reshape(dims_shape + self.frame_shape)
        except Exception:
            dimensions = " ".join(self.__dims.get_names())
            raise ValueError(
                f"Dimensions {dimensions} have {dims_shape} points while there are {self.nframes} images. Try using other tolerance or step values."
            )

    def find_dimensions(self, tolerance: float = 1e-9) -> None:
        """
        Call core.dimension.find_dimensions_from_metadata to set __dims

        :param tolerance: Tolerance used to find dimensions
        """
        self.__dims = find_dimensions_from_metadata(self.metadata_dict, tolerance)

    def get_metadata_values(self, key: str, indices=None) -> numpy.ndarray:
        if key not in self.metadata_dict:
            # The key does not exist -> return an array of the desired size and with NaN value
            return numpy.full(self.nframes, numpy.nan)
        if indices is None:
            return self.metadata_dict[key]
        return self.metadata_dict[key][indices]

    def get_dimensions_values(self, indices=None):
        """
        Returns all the metadata values of the dimensions.
        The values are assumed to be numbers.

        :returns: array_like
        """
        if not self._dimensions_values or indices is not None:
            for dimension in self.__dims.values():
                self._dimensions_values[dimension.name] = self.get_metadata_values(
                    key=dimension.name, indices=indices
                )
        return self._dimensions_values

    def apply_roi(
        self, origin=None, size=None, center=None, indices=None, roi_dir=None
    ):
        """
        Applies a region of interest to the data.

        :param origin: Origin of the roi
        :param size: [Height, Width] of the roi.
        :param center: Center of the roi
        :type origin: Union[2d vector, None]
        :type center: Union[2d vector, None]
        :type size: Union[2d vector, None]
        :param indices: Indices of the images to apply background subtraction.
            If None, the roi is applied to all the data.
        :type indices: Union[None, array_like]
        :param roi_dir: Directory path for the new dataset
        :type roi_dir: str
        :returns: dataset with data with roi applied.
            Note: To preserve consistence of shape between images, if `indices`
            is not None, only the data modified is returned.
        :rtype: Dataset
        """

        new_data = apply_3D_ROI(self.as_array3d(), origin, size, center)

        transformation = self.transformation
        if transformation is not None:
            transformation = Transformation(
                transformation.kind,
                apply_2D_ROI(transformation.x, origin, size, center),
                apply_2D_ROI(transformation.y, origin, size, center),
                transformation.rotate,
            )

        return self.copy(new_data=new_data, new_transformation=transformation)

    def z_sum_along_axis(self, axis_to_keep: int) -> numpy.ndarray:
        """
        Compute the zsum for each point of the `axis_to_keep`.

        For instance, let's take self.data with shape (a,b,c,m,n)` where (m,n) is the frame shape in pixels and (a,b,c) the shape of the 3 motors :

        If `axis_to_keep` = 0, it means we compute we sum pixel values in axis 0 and 2 in order to obtain an array with shape (a, m, n).
        If `axis_to_keep` = 1, shape of the resulting array would be (b, m, n)
        If `axis_to_keep` = 2, shape of the resulting array would be (c, m, n)

        Note that the method assumes self.data.ndim >= 3.
        """
        axis_array = tuple(
            axis for axis in range(self.data.ndim - 2) if axis_to_keep != axis
        )
        return self.data.sum(axis_array)

    def find_shift(
        self, selected_axis: int | None = None, steps=50, indices=None
    ) -> tuple[float, float]:
        """
        Find shift of the data or part of it.

        :param int selected_axis: specify one motor (axis). The method try to find shift along this axis.
        :param array_like indices: Boolean index list with True in the images to apply the shift to.
        :returns: tuple with shift x and y
        """
        # TODO : indices are not used. Maybe it is possible to use it for performance or maybe it is better to simply remove it.
        data = (
            self.z_sum_along_axis(selected_axis)
            if selected_axis is not None
            else self.as_array3d()
        )

        return shift_detection(data, steps)

    def apply_shift(
        self,
        shift: tuple[float, float],
        axis: int | None = None,
        shift_approach: str | None = None,
        indices=None,
    ):
        """
        Apply shift of the data or part of it and save new data into disk.

        :param array_like shift: Shift per frame.
        :param int axis: Select one axis (motor) where to apply the shift. If None, the shift id not applied to one axis but to the whole stack.
        :param Literal['fft', 'linear'] shift_approach: Method to use to apply the shift.
        :param array_like indices: Boolean index list with True in the images to apply the shift to.
            If None, the hot pixel removal is applied to all the data.
        """
        assert len(shift) > 0, "Shift list can't be empty"

        if shift_approach is None:
            shift_approach = "linear"

        if axis is None:

            # Cumulative shift: frame 0 shift is 0, frame 1 shift is `shift`, frame 2 shift is `2*shift`, ...
            cumulative_shift_per_frames = numpy.outer(
                shift, numpy.arange(self.nframes)
            ).T
        else:
            cumulative_shift_per_frames = numpy.outer(
                shift, numpy.indices(self.scan_shape)[axis]
            ).T

        data = self.as_array3d()

        for img_index, shift in enumerate(
            tqdm.tqdm(
                cumulative_shift_per_frames,
                "Apply shift",
                len(cumulative_shift_per_frames),
            )
        ):
            if numpy.isclose(shift[0], 0) and numpy.isclose(shift[1], 0):
                # No need to apply a (0,0) shift
                continue
            if indices is not None and img_index not in indices:
                # Not really optimized but the simplest way i found to take indices into account.
                continue
            data[img_index] = apply_opencv_shift(
                data[img_index],
                shift,
                shift_approach=shift_approach,
            )

    def find_and_apply_shift(
        self,
        selected_axis: int | None = None,
        steps=100,
        indices=None,
        shift_approach: str = "linear",
    ):
        """
        Find the shift of the data or part of it and apply it.

        :param int selected_axis: specify one motor (axis). The method try to find shift along this axis.
        :param float h_step: See `core.imageRegistration.shift_detection`
        :param Union['fft', 'linear'] shift_approach: Method to use to apply the shift.
        :param array_like indices: Indices of the images to find and apply the shift to.
        :param Literal['fft', 'linear'] shift_approach: Method to use to apply the shift.
        """
        shift = self.find_shift(selected_axis, steps, indices=indices)
        self.apply_shift(
            shift, selected_axis, indices=indices, shift_approach=shift_approach
        )

    def _waterfall_nmf(
        self, num_components, iterations, vstep=None, hstep=None, indices=None
    ):
        """
        This method is used as a way to improve the speed of convergence of
        the NMF method. For this, it uses a waterfall model where at every step
        the output matrices serve as input for the next.
        That is, the method starts with a smaller resized images of the data,
        and computes the NMF decomposition. The next step is the same but with
        bigger images, and using as initial H and W the precomputed matrices.
        The last step is done using the actual size of the images.
        This way, the number of iterations with big images can be diminished, and
        the method converges faster.

        :param int num_components: Number of components to find.
        :param array_like iterations: Array with number of iterations per step of the waterfall.
            The size of the array sets the size of the waterfall.
        :param Union[None, array_like] indices: If not None, apply method only to indices of data.
        """

        from skimage.transform import resize

        W = None
        H = None
        shape = self.frame_shape
        first_size = (shape / (len(iterations) + 1)).astype(int)
        size = first_size

        _logger.info("Starting waterfall NMF")

        for i in range(len(iterations)):
            if vstep:
                v_step = vstep * (len(iterations) - i)
            if hstep:
                h_step = hstep * (len(iterations) - i)
            H, W = self.nmf(
                num_components, iterations[i], W=W, H=H, vstep=v_step, hstep=h_step
            )
            size = first_size * (i + 2)
            H2 = numpy.empty((H.shape[0], size[0] * size[1]))
            for row in range(H.shape[0]):
                H2[row] = resize(H[row].reshape((i + 1) * first_size), size).flatten()
            H = H2

        H = resize(H, (num_components, shape[0] * shape[1]))

        return H, W

    def pca(self, num_components=None, indices=None, return_vals=False):
        """
        Compute Principal Component Analysis on the data.
        The method, first converts, if not already, the data into an hdf5 file object
        with the images flattened in the rows.

        :param num_components: Number of components to find.
            If None, it uses the minimum between the number of images and the
            number of pixels.
        :type num_components: Union[None, int]
        :param indices: If not None, apply method only to indices of data, defaults to None
        :type indices: Union[None, array_like], optional
        :param return_vals: If True, returns only the singular values of PCA, else returns
            the components and the mixing matrix, defaults to False
        :type return_vals: bool, optional

        :return: (H, W): The components matrix and the mixing matrix.
        """
        bss_dir = os.path.join(self.dir, "bss")
        os.makedirs(bss_dir, exist_ok=True)

        model = decomposition.PCA(n_components=num_components)

        W = model.fit_transform(self.as_array2d((indices)))

        H, vals, W = model.components_, model.singular_values_, W

        return vals if return_vals else (H, W)

    def nica(
        self,
        num_components,
        chunksize=None,
        num_iter=500,
        error_step=None,
        indices=None,
    ):
        """
        Compute Non-negative Independent Component Analysis on the data.
        The method, first converts, if not already, the data into an hdf5 file object
        with the images flattened in the rows.

        :param num_components: Number of components to find
        :type num_components: Union[None, int]
        :type chunksize: Union[None, int], optional
        :param num_iter: Number of iterations, defaults to 500
        :type num_iter: int, optional
        :param error_step: If not None, find the error every error_step and compares it
            to check for convergence. TODO: not able for huge datasets.
        :param indices: If not None, apply method only to indices of data, defaults to None
        :type indices: Union[None, array_like], optional

        :return: (H, W): The components matrix and the mixing matrix.
        """

        model = NICA(
            self.as_array2d(),
            num_components,
            chunksize,
            indices=indices,
        )
        model.fit_transform(max_iter=num_iter, error_step=error_step)
        return numpy.abs(model.H), numpy.abs(model.W)

    def nmf(
        self,
        num_components,
        num_iter=100,
        error_step=None,
        waterfall=None,
        H=None,
        W=None,
        vstep=100,
        hstep=1000,
        indices=None,
        init=None,
    ):
        """
        Compute Non-negative Matrix Factorization on the data.
        The method, first converts, if not already, the data into an hdf5 file object
        with the images flattened in the rows.

        :param num_components: Number of components to find
        :type num_components: Union[None, int]
        :param num_iter: Number of iterations, defaults to 100
        :type num_iter: int, optional
        :param error_step: If not None, find the error every error_step and compares it
            to check for convergence, defaults to None
            TODO: not able for huge datasets.
        :type error_step: Union[None, int], optional
        :param waterfall: If not None, NMF is computed using the waterfall method.
            The parameter should be an array with the number of iterations per
            sub-computation, defaults to None
        :type waterfall: Union[None, array_like], optional
        :param H: Init matrix for H of shape (n_components, n_samples), defaults to None
        :type H: Union[None, array_like], optional
        :param W: Init matrix for W of shape (n_features, n_components), defaults to None
        :type W: Union[None, array_like], optional
        :param indices: If not None, apply method only to indices of data, defaults to None
        :type indices: Union[None, array_like], optional

        :return: (H, W): The components matrix and the mixing matrix.
        """
        bss_dir = os.path.join(self.dir, "bss")
        os.makedirs(bss_dir, exist_ok=True)

        model = decomposition.NMF(
            n_components=num_components, init=init, max_iter=num_iter
        )
        X = self.as_array2d(indices)

        if numpy.any(X[:, :] < 0):
            _logger.warning("Setting negative values to 0 to compute NMF")
            X[X[:, :] < 0] = 0
        if H is not None:
            X = X.astype(H.dtype)
        elif W is not None:
            X = X.astype(W.dtype)
        with warnings.catch_warnings():
            warnings.simplefilter("always", ConvergenceWarning)
            W = model.fit_transform(X, W=W, H=H)
        return model.components_, W

    def nica_nmf(
        self,
        num_components,
        chunksize=None,
        num_iter=500,
        waterfall=None,
        error_step=None,
        vstep=100,
        hstep=1000,
        indices=None,
    ):
        """
        Applies both NICA and NMF to the data. The init H and W for NMF are the
        result of NICA.
        """
        H, W = self.nica(num_components, chunksize, num_iter, indices=indices)

        # Initial NMF factorization: X = F0 * G0
        W = numpy.abs(W)
        H = numpy.abs(H)

        return self.nmf(
            min(num_components, H.shape[0]),
            num_iter,
            error_step,
            waterfall,
            H,
            W,
            vstep,
            hstep,
            indices=indices,
            init="custom",
        )

    def apply_moments(
        self,
        indices=None,
    ):
        """
        Compute the COM, FWHM, skewness and kurtosis of the data for very dimension.

        :param indices: If not None, apply method only to indices of data, defaults to None
        :type indices: Union[None, array_like], optional
        """

        if not self.dims.ndim:
            raise NoDimensionsError("apply_moments")
        for axis, dim in self.dims.items():
            # Get motor values per image of the stack
            values = self.get_dimensions_values(indices)[dim.name]
            self.moments_dims[axis] = numpy.asarray(
                compute_moments(values, self.as_array3d(indices)),
                dtype=numpy.float64,
            )

        return self.moments_dims

    def apply_fit(
        self,
        indices=None,
        int_thresh: float | None = 15.0,
        method: str | None = None,
        _dir: str | None = None,
    ) -> Tuple[ImageDataset, numpy.ndarray]:
        """
        Fits the data around axis 0 and saves the new data into disk.

        :param indices: Indices of the images to fit.
            If None, the fit is done to all the data.
        :type indices: Union[None, array_like]
        :param int_thresh: see `mapping.fit_pixel`
        :type int_thresh: Union[None, float]
        :returns: dataset with data of same size as `self.data` but with the
            modified images. The urls of the modified images are replaced with
            the new urls.
        """
        if not self.dims.ndim:
            raise NoDimensionsError("apply_fit")

        new_dataset = self.copy(new_data=self.data.copy())

        with self.state_of_operations.run_context(Operation.FIT):
            data = new_dataset.as_array3d(indices)
            # Fit can only be done if rocking curves are at least of size 3
            if len(data) < 3:
                raise ValueError(
                    f"Fit can only be done if rocking curves are at least of dimensionality 3. Got {len(data)}"
                )

            if self.dims.ndim == 1:
                dim0 = self.dims.get(0)
                data[:], maps = fit_1d_data(
                    data=data,
                    values=self.get_metadata_values(dim0.name, indices),
                    int_thresh=int_thresh,
                    method=method,
                )
            elif self.dims.ndim == 2:
                # TODO: `indices` seem to be handled differently here ??
                dim0 = self.dims.get(0)
                dim1 = self.dims.get(1)
                values = [
                    self.get_metadata_values(key=dim0.name),
                    self.get_metadata_values(key=dim1.name),
                ]
                data[:], maps = fit_2d_data(
                    data=self.as_array3d(),
                    values=values,
                    shape=(dim0.size, dim1.size),
                    int_thresh=int_thresh,
                    indices=indices,
                    method=method,
                )
            elif self.dims.ndim == 3:
                # TODO: `indices` seem to be handled differently here ??
                dim0 = self.dims.get(0)
                dim1 = self.dims.get(1)
                dim2 = self.dims.get(2)
                data[:], maps = fit_3d_data(
                    data=self.as_array3d(),
                    motor_values=[
                        self.get_metadata_values(key=dim0.name),
                        self.get_metadata_values(key=dim1.name),
                        self.get_metadata_values(key=dim2.name),
                    ],
                    shape=(dim0.size, dim1.size, dim2.size),
                    int_thresh=int_thresh,
                    indices=indices,
                    method=method,
                )
            else:
                raise TooManyDimensionsForRockingCurvesError()

        return (
            new_dataset,
            maps,
        )

    def compute_transformation(
        self,
        d: float,
        kind: Literal["magnification", "rsm"] = "magnification",
        rotate: bool = False,
        topography_orientation: int | None = None,
        center: bool = True,
    ):
        """
        Computes transformation matrix.
        Depending on the kind of transformation, computes either RSM or magnification
        axes to be used on future widgets.

        :param d: Size of the pixel
        :param kind: Transformation to apply, either 'magnification' or 'rsm'
        :param rotate: To be used only with kind='rsm', if True the images with
            transformation are rotated 90 degrees.
        :param topography: To be used only with kind='magnification', if True
            obpitch values are divided by its sine.
        """

        if not self.dims:
            raise NoDimensionsError("compute_transformation")

        H, W = self.frame_shape
        self.rotate = rotate

        def get_dataset(name) -> float | numpy.array | None:
            if name in self._positioners.data:
                return numpy.median(self._positioners.data[name])
            if name not in self._positioners.constants:
                raise ValueError(
                    f"No dataset named '{name}' found. Unable to compute transformation"
                )
            return self._positioners.constants[name]

        mainx = get_dataset("mainx")

        if kind == "rsm":
            if self.dims.ndim != 1:
                raise ValueError(
                    "RSM transformation matrix computation is only for 1D datasets. Use kind='magnification' or project the dataset first."
                )
            ffz = get_dataset("ffz")
            x, y = compute_rsm(H, W, d, ffz, -mainx, rotate)
        else:
            obx = get_dataset("obx")
            obpitch = get_dataset("obpitch")
            x, y = compute_magnification(
                H, W, d, obx, obpitch, -mainx, topography_orientation, center
            )
        self.transformation = Transformation(kind, x, y, rotate)

    def project_data(self, dimension: Sequence[int], indices=None, _dir=None):
        """
        Applies a projection to the data.
        The new Dataset will have the same size as the chosen dimension, where
        the data is projected on.

        :param dimension: Dimensions to project the data onto
        :type dimension: array_like
        :param indices: Indices of the images to use for the projection.
            If None, the projection is done using all data.
        :type indices: Union[None, array_like]
        :param str _dir: Directory filename to save the new data
        """

        if not self.dims:
            raise NoDimensionsError("project_data")

        dims = AcquisitionDims()
        if len(dimension) == 1:
            axis = self.dims.ndim - dimension[0] - 1
            dim = self.dims.get(dimension[0])
            data = []
            for i in range(dim.size):
                _sum = self.zsum(indices=indices, dimension=[dimension[0], i])
                if len(_sum):
                    data += [_sum]
            data = numpy.array(data)
            dims.add_dim(0, dim)
        elif len(dimension) == 2:
            axis = int(numpy.setdiff1d(range(self.dims.ndim), dimension)[0])
            dim1 = self.dims.get(dimension[0])
            dim2 = self.dims.get(dimension[1])
            dims.add_dim(0, dim1)
            dims.add_dim(1, dim2)
            data = []
            for i in range(dim1.size):
                for j in range(dim2.size):
                    _sum = self.zsum(indices=indices, dimension=[dimension, [i, j]])
                    if len(_sum):
                        data += [_sum]
            data = numpy.array(data)
        else:
            raise ValueError("Only 1D and 2D projection is allowed")

        dim = self.dims.get(axis)

        return self.copy(new_data=data, new_dims=dims)

    def compute_rsm(
        self,
        Q: Vector3D,
        a: float,
        map_range: float,
        pixel_size: float,
        units: Literal["poulsen", "gorfman"] | None = None,
        n: Vector3D | None = None,
        map_shape: Vector3D | None = None,
        energy: float | None = None,
        transformation: Transformation | None = None,
    ):
        diffry = self.get_metadata_values("diffry")
        if transformation is None:
            transformation = self.transformation

        if transformation is None:
            raise ValueError(
                "Transformation has to be computed first using the `compute_transformation` method"
            )

        return calculate_RSM_histogram(
            data=self.as_array3d(),
            diffry_values=diffry,
            twotheta=transformation.y,
            eta=transformation.x,
            Q=Q,
            a=a,
            map_range=map_range,
            units=units,
            map_shape=map_shape,
            n=n,
            E=energy,
        )

    def apply_binning(self, scale, _dir=None):
        from darfix.tasks.binning import Binning  # avoid cyclic import

        _dir = self.dir if _dir is None else _dir
        task = Binning(
            inputs={
                "dataset": self,
                "output_dir": _dir,
                "scale": scale,
            }
        )
        task.run()
        return task.outputs.dataset

    def recover_weak_beam(self, n, indices=None):
        """
        Set to zero all pixels higher than n times the standard deviation across the stack dimension

        :param n: Increase or decrease the top threshold by this fixed value.
        :type n: float
        :param indices: Indices of the images to use for the filtering.
            If None, the filtering is done using all data.
        :type indices: Union[None, array_like]
        """
        std = numpy.std(self.as_array3d(indices).view(numpy.ndarray), axis=0)

        dataset = self.copy(new_data=self.data.copy())
        threshold_removal(dataset.as_array3d(indices), top=n * std)
        return dataset

    @staticmethod
    def load_from_output_dir(output_dir: str, filename: str = "data.h5"):
        file = Path(output_dir) / filename
        h5dict = h5todict(file)

        if "positioners" in h5dict:
            positioners = Positioners(
                DataUrl(file_path=file, data_path="/positioners", scheme="silx"),
                h5dict["positioners"],
            )
        else:
            positioners = None

        if "dimensions" in h5dict:
            # h5dict values are numpy dict but we want a string
            for dim in h5dict["dimensions"].values():
                dim["name"] = str(dim["name"])
            # h5dict keys are str but we want a integer
            raw_dimensions = {
                int(str_axis): dim for str_axis, dim in h5dict["dimensions"].items()
            }
            dimensions = AcquisitionDims.from_dict(raw_dimensions)
        else:
            dimensions = None

        loaded_dataset = ImageDataset(
            output_dir,
            raw_data=h5dict["raw_data"],
            dims=dimensions,
            transformation=h5dict.get("transformation", None),
            title=h5dict.get("title", None),
            positioners=positioners,
        )
        loaded_dataset.reshape_data()
        return loaded_dataset

    def save_in_output_dir(self, filename: str = "data.h5"):
        file = Path(self._dir) / filename
        if "RAW_DATA" in file.parts:
            raise PermissionError(
                f"Write in RAW_DATA dir of ESRF is not allowed: {file}"
            )
        h5dict = {
            "raw_data": self.as_array3d(),
            "dimensions": self.dims.to_dict(),
            "positioners": self.metadata_dict,
            "transformation": self.transformation,
            "title": self.title,
            "writer": {"name": "darfix", "version": __version__},
        }
        dicttoh5(h5dict, file, mode="a", update_mode="modify")
