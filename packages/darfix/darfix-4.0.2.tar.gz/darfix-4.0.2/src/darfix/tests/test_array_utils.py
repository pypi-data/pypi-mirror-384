import numpy

from darfix.core import array_utils


def test_unique():
    arr = [10, 11, 10, 11, 2, 2, 2, 3, 3, 1]
    return_type = type(numpy.unique(arr))
    result = array_utils.unique(arr)
    assert return_type is type(result)
    assert result.tolist() == [10, 11, 2, 3, 1]

    return_type = type(numpy.unique(arr, return_index=True))
    result = array_utils.unique(arr, return_index=True)
    assert return_type is type(result)
    assert len(result) == 2
    assert result[0].tolist() == [10, 11, 2, 3, 1]
    assert result[1].tolist() == [0, 1, 4, 7, 9]

    return_type = type(numpy.unique(arr, return_index=True, return_counts=True))
    result = array_utils.unique(arr, return_index=True, return_counts=True)
    assert return_type is type(result)
    assert len(result) == 3
    assert result[0].tolist() == [10, 11, 2, 3, 1]
    assert result[1].tolist() == [0, 1, 4, 7, 9]
    assert result[2].tolist() == [2, 2, 3, 2, 1]

    return_type = type(numpy.unique(arr, return_index=True, return_counts=True))
    result = array_utils.unique(arr, return_counts=True)
    assert return_type is type(result)
    assert len(result) == 2
    assert result[0].tolist() == [10, 11, 2, 3, 1]
    assert result[1].tolist() == [2, 2, 3, 2, 1]
