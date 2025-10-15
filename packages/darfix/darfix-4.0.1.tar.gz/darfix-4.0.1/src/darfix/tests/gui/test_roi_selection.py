from darfix.core.roi import clampROI


def test_roi_clamping():
    """Test clamping of the ROI according to frame shape"""
    frame_origin = (0, 0)

    new_origin, new_size = clampROI(
        roi_origin=(0, 0),
        roi_size=(10, 10),
        frame_origin=frame_origin,
        frame_size=(100, 100),
    )
    assert new_origin == (0, 0)
    assert new_size == (10, 10)

    # check case ROI is fully inside the frame
    new_origin, new_size = clampROI(
        roi_origin=(0, 0),
        roi_size=(10, 10),
        frame_origin=frame_origin,
        frame_size=(3, 3),
    )
    assert new_origin == (0, 0)
    assert new_size == (3, 3)

    # check case ROI is at the upper-right corner of the frame
    new_origin, new_size = clampROI(
        roi_origin=(5, 5),
        roi_size=(10, 10),
        frame_origin=frame_origin,
        frame_size=(10, 10),
    )
    assert new_origin == (5, 5)
    assert new_size == (5, 5)

    # check case ROI is at the right of the frame
    new_origin, new_size = clampROI(
        roi_origin=(0, 5),
        roi_size=(10, 10),
        frame_origin=frame_origin,
        frame_size=(10, 10),
    )
    assert new_origin == (0, 5)
    assert new_size == (10, 5)

    # check case ROI is at the bottom of the frame
    new_origin, new_size = clampROI(
        roi_origin=(0, -5),
        roi_size=(10, 10),
        frame_origin=frame_origin,
        frame_size=(10, 10),
    )
    assert new_origin == (0, 0)
    assert new_size == (10, 5)

    # check case ROI is at the left of the frame
    new_origin, new_size = clampROI(
        roi_origin=(0, 0),
        roi_size=(10, 10),
        frame_origin=frame_origin,
        frame_size=(100, 100),
    )
    assert new_origin == (0, 0)
    assert new_size == (10, 10)
