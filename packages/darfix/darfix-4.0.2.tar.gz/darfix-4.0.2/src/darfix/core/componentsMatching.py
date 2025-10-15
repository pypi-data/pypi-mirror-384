__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "28/02/2020"

from enum import Enum

import numpy
from silx.image import sift

try:
    import cv2
except ImportError:
    has_cv2 = False
else:
    has_cv2 = True


class Method(Enum):
    """
    Methods available to compute the matching.
    """

    orb_feature_matching = "orb feature matching"
    sift_feature_matching = "sift feature matching"
    euclidean_distance = "euclidean distance"

    @staticmethod
    def values():
        return list(map(lambda c: c.value, Method))


class ComponentsMatching:
    """
    Class to compute component matching.

    :param array_like components: List of stack of images. Every element of the
        list contains a stack of components from a certain dataset.
    """

    def __init__(self, components):
        self.components = components

    def _create_descriptors(self):
        """
        Function that detects and computes the keypoints and descriptors for
        the components.
        """
        orb = cv2.ORB_create()
        descripted_components = []

        for array in self.components:
            components = []
            for image in array:
                cv2.normalize(image, image, 0, 255, cv2.NORM_MINMAX)
                image = image.astype(numpy.uint8)
                kp, des = orb.detectAndCompute(image, None)
                components.append(Component(image, kp, des))
            descripted_components.append(components)

        return descripted_components

    def _create_sift_keypoints(self):
        keypoints = []

        for array in self.components:
            sift_ocl = sift.SiftPlan(template=array[0], devicetype="CPU")
            components = [sift_ocl(image) for image in array]
            keypoints.append(components)

        return keypoints

    def euclidean_distance(self, X, Y):
        """
        Compute euclidean distance between two images.
        """
        assert (
            X.shape == Y.shape
        ), "Images have to have same shape to compute euclidean distance"
        dst = numpy.linalg.norm(X - Y)  # their euclidean distances
        return dst

    def match_components(
        self, id1=None, id2=None, method=Method.orb_feature_matching, tol=8
    ):
        """
        Match components. Given the components x1,...,xn of dataset 1 and the
        components y1,...,ym of dataset 2, this function computes the pairs
        (xi,yi) that have better matching. Considering that each component of
        dataset 1 corresponds to one and only one component of dataset 2.

        :param Union[int,None] id1: Id of the first dataset to compare.
        :param Union[int,None] id2: Id of the second dataset to compare.
        :param Method method: Method to use for the matching.

        :returns: Dictionary with components ids of id1 per keys and their
            corresponding id component of id2 match per values, and dictionary
            with the matching info per pair of components.
        :rtype: (dict, dict)
        """
        if not has_cv2:
            raise RuntimeError(
                "Unable to match components without opencv-python. Please install it."
            )
        if id1 is None or id2 is None:
            assert len(self.components) == 2, "Index of components must be given"
            id1 = 0
            id2 = 1

        good = {}
        final_matches = {}
        if method == Method.orb_feature_matching:
            self.descriptors = self._create_descriptors()

            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            # Match components with id1 and id2
            for i, component1 in enumerate(self.descriptors[id1]):
                if component1.descriptor is not None:
                    for j, component2 in enumerate(self.descriptors[id2]):
                        if component2.descriptor is not None:
                            # Match descriptors
                            good[(i, j)] = numpy.array(
                                bf.match(component1.descriptor, component2.descriptor)
                            )

            best_v = []
            # Add matches sorted by number of matches found.
            for x, y in sorted(good, key=lambda match: len(good[match]), reverse=True):
                # Only add match if neither x nor y are already in the list.
                if x not in final_matches.keys() and y not in final_matches.values():
                    kp1 = []
                    kp2 = []
                    for match in good[(x, y)]:
                        kp1 += [self.descriptors[id1][x].keypoints[match.queryIdx].pt]
                        kp2 += [self.descriptors[id2][y].keypoints[match.trainIdx].pt]
                    if len(kp1) > 1 and len(kp2) > 1:
                        v = numpy.mean(numpy.array(kp2) - numpy.array(kp1), axis=0)
                    else:
                        v = numpy.array(kp2) - numpy.array(kp1)
                    if not numpy.any(best_v):
                        best_v = v
                        final_matches[x] = y
                    elif numpy.linalg.norm(best_v - v) < tol:
                        final_matches[x] = y

        elif method == Method.sift_feature_matching:
            keypoints = self._create_sift_keypoints()
            best_v = []
            mp = sift.MatchPlan()
            # Match components with id1 and id2
            for i, kp1 in enumerate(keypoints[id1]):
                for j, kp2 in enumerate(keypoints[id2]):
                    # Match descriptors
                    good[(i, j)] = mp.match(kp1, kp2)
            # Add matches sorted by number of matches found.
            for x, y in sorted(
                good, key=lambda match: good[match].shape[0], reverse=True
            ):
                # Only add match if neither x nor y are already in the list.
                if x not in final_matches.keys() and y not in final_matches.values():
                    v = numpy.array(
                        [
                            numpy.median(good[(x, y)][:, 1].x - good[(x, y)][:, 0].x),
                            numpy.median(good[(x, y)][:, 1].y - good[(x, y)][:, 0].y),
                        ]
                    )
                    if not numpy.any(best_v):
                        best_v = v
                        final_matches[x] = y
                    elif numpy.linalg.norm(best_v - v) < tol:
                        final_matches[x] = y

        elif method == Method.euclidean_distance:
            for i, X in enumerate(self.components[id1]):
                for j, Y in enumerate(self.components[id2]):
                    good[(i, j)] = self.euclidean_distance(X, Y)
            # Add matches sorted by distance.
            for x, y in sorted(good, key=lambda match: good[match]):
                # Only add match if neither x nor y are already in the list.
                if x not in final_matches.keys() and y not in final_matches.values():
                    final_matches[x] = y
        return final_matches, good

    def draw_matches(
        self, final_matches, matches, id1=None, id2=None, displayMatches=False
    ):
        """
        Create stack of images with each pair of matches.

        :param dict final_matches: Dictionary with the best pairs of matches per items.
        :param dict matches: Dictionary with keys the pairs of matches and with
            values the information of every pair of components.
        :param Union[int,None] id1: Id of the first dataset to compare.
        :param Union[int,None] id2: Id of the second dataset to compare.
        :param bool displayMatches: If True, dictionary `matches` has to contain
            values of type `cv2.DMatch`.

        :returns array_like: stack with the pairs of images, and if so, info
            about the matching.
        """
        if id1 is None or id2 is None:
            assert len(self.components) == 2, "Index of components must be given"
            id1 = 0
            id2 = 1
        stack = []
        for i, img1 in enumerate(self.components[id1]):
            if i in final_matches:
                j = final_matches[i]
                img2 = self.components[id2][j]
                # Show link between features
                if displayMatches:
                    # Check that all values are of type `cv2.DMatch`
                    assert all(
                        (isinstance(match, cv2.DMatch) for match in values)
                        for values in matches.values()
                    ), "Dictionary `matches` has to contain values of type `cv2.DMatch`"

                    img = cv2.drawMatches(
                        self.descriptors[id1][i].image,
                        self.descriptors[id1][i].keypoints,
                        self.descriptors[id2][j].image,
                        self.descriptors[id2][j].keypoints,
                        matches[(i, j)],
                        None,
                        flags=2,
                    )
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    shape1, shape2 = img1.shape, img2.shape
                    img = numpy.zeros(
                        (max(shape1[0], shape2[0]), shape1[1] + shape2[1])
                    )
                    img[: shape1[0], : shape1[1]] = img1
                    img[: shape2[0], shape1[1] :] = img2
            else:
                shape1 = img1.shape
                shape2 = self.components[id2][0].shape
                img = numpy.zeros((max(shape1[0], shape2[0]), shape1[1] + shape2[1]))
                img[: shape1[0], : shape1[1]] = img1
            stack.append(img)
        return stack


class Component:
    """
    Class Component. Describes a component of a dataset (image) with its keypoints
    and descriptors.
    """

    def __init__(self, image, kp, des):
        self._image = image
        self._keypoints = kp
        self._descriptor = des

    @property
    def keypoints(self):
        return self._keypoints

    @property
    def descriptor(self):
        return self._descriptor

    @property
    def image(self):
        return self._image
