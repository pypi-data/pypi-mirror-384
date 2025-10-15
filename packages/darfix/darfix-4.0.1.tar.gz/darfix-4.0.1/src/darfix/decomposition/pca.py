__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "19/03/2020"

import numpy

from .base import Base


class PCA(Base):
    def __init__(
        self, data, num_components=None, center=True, whiten=False, rowvar=True
    ):
        Base.__init__(self, data, num_components=num_components)

        self.rowvar = rowvar
        if self.rowvar:
            self.data = self.data[:, :].T

        self._rows, self._columns = self.data.shape
        self._data_orig = self.data
        self._mean = self._data_orig[:, :].mean(axis=0)

        self._whiten = whiten
        self._center = center

        if self._center:
            # copy the data before centering it
            self.data = self._data_orig - self._mean

    def _update_h(self):
        self.H = numpy.matmul(self.data[:, :], self.W.T)

        if self.rowvar:
            self.H = self.H.T

    def _update_w(self):
        X = self.data[:, :]
        r = self.num_components

        if self._columns > self._rows:  # n x n matrix
            if not self._center:
                M = numpy.matmul((X - self._mean), (X - self._mean).T)
            else:
                M = numpy.matmul(X, X.T)

            # Eigenvector decomposition
            vals, vecs = numpy.linalg.eig(M)
            vals, vecs = vals.real, vecs.real

            # Sort the eigenvectors by "importance" and get the first r
            pairs = sorted(
                [(vals[i], vecs[:, i]) for i in range(len(vals))],
                key=lambda x: x[0],
                reverse=True,
            )
            pairs = [
                p for p in pairs if abs(p[0]) > 1e-10
            ]  # Remove the eigenvectors of 0 eigenvalue
            pairs = pairs[:r]

            # nxr matrix of eigenvectors (each column is an n-dimensional eigenvector)
            E = numpy.array([p[1] for p in pairs]).transpose()

            # pxr matrix of the first r eigenvectors of the covariance of X
            # Note that we normalize!
            E = numpy.matmul((X - self._mean).transpose(), E)
            E /= numpy.linalg.norm(E, axis=0)

            if self._whiten:
                # Eigenvalues of cov(X) to the -1/2
                # Note that we rescale the eigenvalues of M to get the eigenvalues of cov(X)!
                diag = numpy.array(
                    [1 / numpy.sqrt(p[0] / (self._rows - 1)) for p in pairs]
                )

        else:  # p x p matrix
            C = numpy.cov(X, rowvar=False)

            # Eigenvector decomposition
            vals, vecs = numpy.linalg.eig(C)
            vals, vecs = vals.real, vecs.real

            # Sort the eigenvectors by "importance" and get the first r
            pairs = sorted(
                [(vals[i], vecs[:, i]) for i in range(len(vals))],
                key=lambda x: x[0],
                reverse=True,
            )
            pairs = [
                p for p in pairs if abs(p[0]) > 1e-10
            ]  # Remove the eigenvectors of 0 eigenvalue
            pairs = pairs[:]

            # pxr matrix of the first r eigenvectors of the covariance of X
            E = numpy.array([p[1] for p in pairs]).transpose()

            if self._whiten:  # Eigenvalues of cov(X) to the -1/2
                diag = numpy.array([1 / numpy.sqrt(p[0]) for p in pairs])

        if self._whiten:
            self.W = E * diag
        else:
            self.W = E

        self.W = self.W.T

    def fit_transform(self, max_iter=1, error_step=None):
        Base.fit_transform(self, max_iter=1, error_step=error_step)
