import os
import time

from ewoksorange.tests.conftest import qtapp  # noqa F401
from silx.io.url import DataUrl

import darfix.resources.tests
from darfix.core.dataset import ImageDataset
from darfix.core.dimension import Dimension
from darfix.dtypes import Dataset
from orangecontrib.darfix.widgets.transformation import TransformationWidgetOW


def test_TransformationWidgetOW(
    resource_files,
    qtapp,  # noqa F811
):
    _316H_dummy_insitu_g1_RSM_2 = str(
        resource_files(darfix.resources.tests).joinpath(
            os.path.join("transformation", "316H_dummy_insitu_g1_RSM_2.h5")
        )
    )

    data_file_url = DataUrl(
        file_path=_316H_dummy_insitu_g1_RSM_2,
        data_path="/1.1/measurement/basler_ff",
        scheme="silx",
    )

    dataset = Dataset(
        dataset=ImageDataset(
            detector_url=data_file_url.path(),
            metadata_url=DataUrl(
                file_path=str(_316H_dummy_insitu_g1_RSM_2),
                data_path="/1.1/instrument/positioners",
                scheme="silx",
            ).path(),
            _dir=None,
        ),
    )

    # Actually the dataset 316H_dummy_insitu_g1_RSM_2 is weird as diffry size does not match number of frames
    dataset.dataset.dims.add_dim(0, Dimension("diffry", 11))

    widget = TransformationWidgetOW()
    widget.setDataset(dataset)
    assert dataset.dataset.transformation is None
    widget._execute_task()
    # Wait until the task finished
    time.sleep(1)
    new_dataset: Dataset = widget.get_task_output_value("dataset")
    assert new_dataset.dataset.transformation is not None
    assert new_dataset.dataset.transformation.kind == "magnification"

    widget._methodCB.setCurrentText("RSM")
    widget._execute_task()
    # Wait until the task finished
    time.sleep(1)
    new_dataset: Dataset = widget.get_task_output_value("dataset")
    assert new_dataset.dataset.transformation is not None
    assert new_dataset.dataset.transformation.kind == "rsm"
