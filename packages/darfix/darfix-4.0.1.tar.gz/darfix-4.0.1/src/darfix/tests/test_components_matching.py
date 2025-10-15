import numpy
import pytest
from silx.opencl.common import ocl
from skimage import data

from darfix.core.componentsMatching import ComponentsMatching
from darfix.core.componentsMatching import Method


@pytest.fixture(scope="module")
def components_matching():
    moon = data.moon()
    camera = data.camera()
    gravel = data.gravel()
    components1 = numpy.array([moon, camera, gravel])
    components2 = numpy.array([gravel, moon, camera])

    return ComponentsMatching(components=(components1, components2))


def test_euclidean_distance(components_matching):
    components1, components2 = components_matching.components

    assert components_matching.euclidean_distance(components1[0], components2[1]) == 0
    assert components_matching.euclidean_distance(components1[1], components2[1]) != 0


@pytest.mark.skipif(ocl is None, reason="PyOpenCl is missing")
def test_sift_match(components_matching):
    final_matches, matches = components_matching.match_components(
        method=Method.sift_feature_matching
    )
    assert final_matches[0] == 1


def test_orb_match(components_matching):
    final_matches, matches = components_matching.match_components(
        method=Method.orb_feature_matching
    )
    assert final_matches[0] == 1


def test_draw_matches0(components_matching):
    final_matches, matches = components_matching.match_components(
        method=Method.orb_feature_matching
    )
    stack = components_matching.draw_matches(
        final_matches, matches, displayMatches=True
    )
    assert stack[0].shape == (512, 1024)
    stack = components_matching.draw_matches(
        final_matches, matches, displayMatches=False
    )
    assert stack[1].shape == (512, 1024)


def test_draw_matches1(components_matching):
    final_matches, matches = components_matching.match_components(
        method=Method.euclidean_distance
    )
    stack = components_matching.draw_matches(final_matches, matches)
    assert stack[2].shape == (512, 1024)


@pytest.mark.skipif(ocl is None, reason="PyOpenCl is missing")
def test_draw_matches2(components_matching):
    final_matches, matches = components_matching.match_components(
        method=Method.sift_feature_matching
    )
    stack = components_matching.draw_matches(final_matches, matches)
    assert stack[2].shape == (512, 1024)
