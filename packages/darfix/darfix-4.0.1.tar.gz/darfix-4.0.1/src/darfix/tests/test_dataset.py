import copy
import os
import tempfile
import unittest
import uuid

import numpy

from darfix.tests import utils


class _BaseDatasetTest:
    """Tests for class Dataset in `dataset.py`"""

    def createRandomDataset(self, dims, nb_frames, metadata=False):
        raise NotImplementedError("Base class")

    def test_data_load(self):
        """Tests the correct load of the data"""
        self.assertEqual(len(self.dataset.as_array3d()), 3)
        self.assertEqual(self.dataset.nframes, 3)

    def test_nframes(self):
        """Tests the nframes method"""
        self.assertEqual(self.dataset.nframes, 3)

    def test_deepcopy(self):
        """Tests the correct deepcopy of the object"""
        dataset_copy = copy.deepcopy(self.dataset)
        self.assertEqual(self.dataset.nframes, dataset_copy.nframes)
        self.assertEqual(self.dataset.data.shape, dataset_copy.data.shape)

    def test_zsum(self):
        zsum = self.dataset.zsum()
        self.assertEqual(zsum.shape, (100, 100))

        result = numpy.sum(self.dataset.as_array3d(), axis=0)
        numpy.testing.assert_array_equal(zsum, result)

        indices = [0, 1]
        zsum = self.dataset.zsum(indices)
        result = numpy.sum(self.dataset.as_array3d(indices), axis=0)
        numpy.testing.assert_array_equal(zsum, result)

    def test_filter_data(self):
        """Tests the correct separation of empty frames and data frames"""
        dims = (10, 100, 100)
        data = numpy.zeros(dims)
        background = numpy.random.random(dims)
        idxs = [0, 2, 4]
        data[idxs] += background[idxs]
        dataset = utils.createDataset(data=data, _dir=self._dir)
        used_idx, not_used_idx = dataset.partition_by_intensity(bottom_bin=1)
        self.assertEqual(used_idx.shape[0], 3)
        self.assertEqual(not_used_idx.shape[0], 7)

    def test_roi(self):
        """Tests the roi function"""
        new_dataset = self.dataset.apply_roi(origin=[0, 0], size=[20, 20])
        self.assertEqual(new_dataset.nframes, 3)
        numpy.testing.assert_equal(self.dataset.data[:, :20, :20], new_dataset.data)

    def test_find_shift(self):
        """Tests the shift detection"""
        shift = self.dataset.find_shift()

        self.assertEqual(len(shift), 2)

        shift = self.dataset.find_shift(indices=[0, 1])

        self.assertEqual(len(shift), 2)

    def test_pca(self):

        H, W = self.dataset.pca()

        self.assertEqual(
            H.shape, (self.dataset.nframes, len(self.dataset.data[0].flatten()))
        )
        self.assertEqual(W.shape, (self.dataset.nframes, self.dataset.nframes))

        n_components = 1
        indices = [1, 2]
        H, W = self.dataset.pca(num_components=n_components, indices=indices)

        self.assertEqual(H.shape, (n_components, len(self.dataset.data[0].flatten())))
        self.assertEqual(W.shape, (2, n_components))

    def test_nmf(self):

        num_components = 2
        H, W = self.dataset.nmf(num_components)

        self.assertEqual(H.shape, (num_components, len(self.dataset.data[0].flatten())))
        self.assertEqual(W.shape, (self.dataset.nframes, num_components))

        num_components = 1
        indices = [1, 2]
        H, W = self.dataset.nmf(num_components=num_components, indices=indices)

        self.assertEqual(H.shape, (num_components, len(self.dataset.data[0].flatten())))
        self.assertEqual(W.shape, (2, num_components))

    def test_nica(self):

        num_components = 2
        H, W = self.dataset.nica(num_components)

        self.assertEqual(H.shape, (num_components, len(self.dataset.data[0].flatten())))
        self.assertEqual(W.shape, (self.dataset.nframes, num_components))

        num_components = 1
        indices = [1, 2]
        H, W = self.dataset.nica(num_components=num_components, indices=indices)

        self.assertEqual(H.shape, (num_components, len(self.dataset.data[0].flatten())))
        self.assertEqual(W.shape, (2, num_components))


class TestHDF5Dataset(_BaseDatasetTest, unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        output_file = os.path.join(self._dir, str(uuid.uuid1()) + ".hdf5")
        self.dataset = utils.createRandomHDF5Dataset(
            dims=(100, 100), nb_data_frames=3, metadata=True, output_file=output_file
        )

    def createRandomDataset(self, dims, nb_frames, metadata=False):
        return utils.createRandomHDF5Dataset(
            dims=dims, nb_data_frames=nb_frames, metadata=metadata
        )


def test_reshaped_data(dataset):
    """Tests the correct reshaping of the data"""

    dataset.find_dimensions()
    dataset.reshape_data()
    assert dataset.data.shape == (2, 2, 5, 100, 100)


if __name__ == "__main__":
    unittest.main()
