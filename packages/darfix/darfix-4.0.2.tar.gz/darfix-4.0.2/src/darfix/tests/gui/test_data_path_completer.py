import os

import pytest
from ewoksorange.tests.conftest import qtapp  # noqa F401

from darfix.core.datapathfinder import DETECTOR_KEYWORD
from darfix.core.datapathfinder import FIRST_SCAN_KEYWORD
from darfix.core.datapathfinder import LAST_SCAN_KEYWORD
from darfix.core.datapathfinder import SCAN_KEYWORD
from darfix.gui.utils.data_path_completer import DataPathLineEditWithCompleter
from darfix.gui.utils.data_path_completer import DataPathModel
from darfix.tests.utils import create_scans


@pytest.mark.parametrize("display_dataset", (True, False))
def test_DataPathModel_scan_and_detector_keywords(
    tmp_path, qtapp, display_dataset: bool  # noqa F811
):
    """
    test keywords handling in the case we have '{scan}' and '{detector}' keywords
    """
    test_folder = tmp_path / "test_DataPathModel_scan_and_detector_keywords"
    test_folder.mkdir()
    test_file = os.path.join(test_folder, "scans")
    create_scans(file_path=test_file, n_scan=2)

    allowed_keywords = (SCAN_KEYWORD, DETECTOR_KEYWORD)
    widget = DataPathLineEditWithCompleter(
        allowed_keywords=allowed_keywords, completer_display_dataset=display_dataset
    )
    widget.setFile(test_file)

    completer_model = widget.completer().model()
    assert isinstance(completer_model, DataPathModel)

    assert completer_model.getAllowedKeywords() == allowed_keywords

    # check that the 'root' keywords are at root
    assert completer_model.rowCount() == 1
    assert completer_model.columnCount() == 1
    assert len(completer_model.findItems(SCAN_KEYWORD)) == 1
    assert len(completer_model.findItems(FIRST_SCAN_KEYWORD)) == 0
    assert len(completer_model.findItems(LAST_SCAN_KEYWORD)) == 0
    # check the 'scan' keyword tree is correctly solved
    scan_item = completer_model.findItems(SCAN_KEYWORD)[0]
    assert scan_item.columnCount() == 1
    assert scan_item.rowCount() == 3
    scan_root_det = scan_item.child(0, 0)
    scan_instrument = scan_item.child(1, 0)
    assert scan_root_det.text() == DETECTOR_KEYWORD
    assert scan_instrument.text() == "instrument"
    measurement_item = scan_item.child(2, 0)
    assert measurement_item.text() == "measurement"

    # make sure the r'{detector}' keyword is a leaf
    assert scan_root_det.rowCount() == 0
    assert scan_root_det.columnCount() == 0

    # check that the 2.1/instrument item is correctly solved until the end
    assert scan_instrument.rowCount() == 2
    assert scan_instrument.columnCount() == 1
    detector_item = scan_instrument.child(1, 0)
    assert detector_item.text() == DETECTOR_KEYWORD
    measurement_item = scan_instrument.child(0, 0)

    positioners_item = scan_instrument.child(0, 0)
    assert positioners_item.text() == "positioners"

    assert positioners_item.rowCount() == (4 if display_dataset else 0)
    assert positioners_item.columnCount() == (1 if display_dataset else 0)


@pytest.mark.parametrize("display_dataset", (True, False))
def test_DataPathModel_first_scan_and_last_scan_and_detectorkeywords(
    tmp_path, qtapp, display_dataset: bool  # noqa F811
):
    """
    test keywords handling in the case we have '{first_scan}', '{last_scan}' and {detector} keywords
    """
    test_folder = tmp_path / "test_DataPathModel_first_scan_and_last_scan_keywords"
    test_folder.mkdir()
    test_file = os.path.join(test_folder, "scans")
    create_scans(file_path=test_file, n_scan=2)

    allowed_keywords = (FIRST_SCAN_KEYWORD, LAST_SCAN_KEYWORD, DETECTOR_KEYWORD)
    widget = DataPathLineEditWithCompleter(
        allowed_keywords=allowed_keywords, completer_display_dataset=display_dataset
    )
    widget.setFile(test_file)
    completer_model = widget.completer().model()
    assert isinstance(completer_model, DataPathModel)

    assert completer_model.getAllowedKeywords() == allowed_keywords

    # check that the 'root' keywords are at root
    assert completer_model.rowCount() == 4  # {first_scan}, {last_scan}, 1.1, 2.1
    assert completer_model.columnCount() == 1
    assert len(completer_model.findItems("")) == 1  # file root level
    assert len(completer_model.findItems(SCAN_KEYWORD)) == 0
    assert len(completer_model.findItems(FIRST_SCAN_KEYWORD)) == 1
    assert len(completer_model.findItems(LAST_SCAN_KEYWORD)) == 1
    # check the 'scan' keyword tree is correctly solved
    scan_item = completer_model.findItems(FIRST_SCAN_KEYWORD)[0]
    assert scan_item.columnCount() == 1
    assert scan_item.rowCount() == 3
    scan_root_det = scan_item.child(0, 0)
    scan_instrument = scan_item.child(1, 0)
    assert scan_root_det.text() == DETECTOR_KEYWORD
    assert scan_instrument.text() == "instrument"
    measurement_item = scan_item.child(2, 0)
    assert measurement_item.text() == "measurement"

    # make sure the r'{detector}' keyword is a leaf
    assert scan_root_det.rowCount() == 0
    assert scan_root_det.columnCount() == 0

    # check that the 2.1/instrument item is correctly solved until the end
    assert scan_instrument.rowCount() == 2
    assert scan_instrument.columnCount() == 1
    detector_item = scan_instrument.child(1, 0)
    assert detector_item.text() == DETECTOR_KEYWORD
    measurement_item = scan_instrument.child(0, 0)

    positioners_item = scan_instrument.child(0, 0)
    assert positioners_item.text() == "positioners"

    assert positioners_item.rowCount() == (4 if display_dataset else 0)
    assert positioners_item.columnCount() == (1 if display_dataset else 0)

    # check one real scan path
    existing_path_item = completer_model.findItems("")[0]
    assert existing_path_item.rowCount() == 3  # 1.1, 2.1 and {detector}
    assert existing_path_item.columnCount() == 1
    item_1_1 = existing_path_item.child(0, 0)
    assert item_1_1.text() == "1.1"
    item_2_1 = existing_path_item.child(2, 0)
    assert item_2_1.text() == "2.1"
    item_detector = existing_path_item.child(1, 0)
    assert item_detector.text() == DETECTOR_KEYWORD

    assert item_1_1.rowCount() == 3  # instrument, measurement and {detector}
