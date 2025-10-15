import numpy

from darfix.core.dataset import ImageDataset

from . import utils


def test_load_and_save():
    imgs = numpy.arange(1000).reshape((5, 2, 10, 10))
    dset = utils.createHDF5Dataset2D(imgs)
    dset.find_dimensions()
    dset.save_in_output_dir()
    dset2 = ImageDataset.load_from_output_dir(dset.dir)

    assert dset2.dims.ndim == 2
    assert dset2.dims[0].name == "motor1"
    assert dset2.dims[1].name == "motor2"
    assert "motor1" in dset2.metadata_dict
    assert "motor2" in dset2.metadata_dict
    numpy.testing.assert_allclose(dset2.data, imgs)
