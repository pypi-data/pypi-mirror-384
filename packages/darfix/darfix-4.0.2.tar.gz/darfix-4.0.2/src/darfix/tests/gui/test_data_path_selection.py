from ewoksorange.tests.conftest import qtapp  # noqa F401

from darfix.gui.utils.data_path_selection import DataPathSelection
from darfix.tests.utils import create_scans


def test_DataPathSelection(tmp_path, qtapp):  # noqa F811
    """Test DataPathSelection pattern"""

    default_detector_data_path = r"{scan}/measurement/{detector}"
    default_positioners_data_path = r"{scan}/instrument/positioners"

    test_folder = tmp_path / "test_data_path_selection"
    test_folder.mkdir()
    input_file = test_folder / "scans.hdf5"

    create_scans(file_path=input_file)

    # test the find_detector_dataset callback
    widget = DataPathSelection(
        pattern=default_detector_data_path,
    )

    widget.setInputFile(str(input_file))
    qtapp.processEvents()

    assert widget.getPattern() == default_detector_data_path
    assert widget.getDefaultPattern() == default_detector_data_path
    assert widget._dataPathFinder._solved_pattern == "{scan}/measurement/my_detector"
    assert widget.getExample() == "/1.1/measurement/my_detector"
    assert widget._dataPathFinder._can_be_solved is True

    # test with find_positioner callback
    widget.setPattern(
        pattern=default_positioners_data_path,
    )
    qtapp.processEvents()
    assert widget.getPattern() == default_positioners_data_path
    assert widget.getExample() == "/1.1/instrument/positioners"
    assert widget.getDefaultPattern() == default_detector_data_path
    widget.setDefaultPattern(default_positioners_data_path)
    assert widget.getDefaultPattern() == default_positioners_data_path
    assert widget._dataPathFinder._solved_pattern == "{scan}/instrument/positioners"
    assert widget._dataPathFinder._can_be_solved is True

    # test with a not existing foler to search
    pattern_not_existing = "{scan}/pattern/not/existing"
    widget.setPattern(
        pattern=pattern_not_existing,
    )
    qtapp.processEvents()
    assert widget.getExample() == ""
    assert widget.getPattern() == pattern_not_existing
    assert widget._dataPathFinder._solved_pattern == pattern_not_existing
    assert widget._dataPathFinder._can_be_solved is False
