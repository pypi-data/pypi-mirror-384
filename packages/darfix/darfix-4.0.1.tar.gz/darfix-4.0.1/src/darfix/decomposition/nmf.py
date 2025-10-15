__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "06/04/2020"

import logging

import numpy

from .base import Base

_logger = logging.getLogger(__file__)


class NMF(Base):
    """
    Non-Negative Matrix Factorization.

    Find two non-negative matrices whose product approximates the non-negative
    matrix data.
    """

    def _init_w(self):
        if self.W is None:
            Base._init_w(self)
        self.W = numpy.abs(self.W)

    def _init_h(self):
        if self.H is None:
            Base._init_h(self)
        self.H = numpy.abs(self.H)

    def _update_h(self):
        _logger.info("Updating H")
        V, W, H = self.data, self.W, self.H
        if self.indices is None:
            for column in range(0, self.H.shape[1], self._hstep):
                mult = numpy.matmul(W.T, V[:, column : column + self._hstep]) / (
                    numpy.matmul(
                        numpy.matmul(W.T, W), H[:, column : column + self._hstep]
                    )
                    + 10**-9
                )
                self.H[:, column : column + self._hstep] *= mult
        else:
            for column in range(0, self.H.shape[1], self._hstep):
                mult = numpy.matmul(
                    W.T, V[self.indices, column : column + self._hstep]
                ) / (
                    numpy.matmul(
                        numpy.matmul(W.T, W), H[:, column : column + self._hstep]
                    )
                    + 10**-9
                )
                self.H[:, column : column + self._hstep] *= mult

    def _update_w(self):
        _logger.info("Updating W")
        V, W, H = self.data, self.W, self.H
        if self.indices is None:
            for row in range(0, len(self.W), self._vstep):
                mult = numpy.matmul(V[row : row + self._vstep], H.T) / (
                    numpy.matmul(numpy.matmul(W[row : row + self._vstep], H), H.T)
                    + 10**-9
                )
                self.W[row : row + self._vstep] *= mult
        else:
            for row in range(0, len(self.W), self._vstep):
                indx = self.indices[row : row + self._vstep]
                mult = numpy.matmul(V[indx], H.T) / (
                    numpy.matmul(numpy.matmul(W[row : row + self._vstep], H), H.T)
                    + 10**-9
                )
                self.W[row : row + self._vstep] *= mult

    def fit_transform(
        self,
        H=None,
        W=None,
        max_iter=1000,
        compute_w=True,
        compute_h=True,
        vstep=100,
        hstep=1000,
        error_step=None,
    ):
        """
        Find the two non-negative matrices (H, W) using Lee and Seung's multiplicative update rule (https://proceedings.neurips.cc/paper/2000/file/f9d1152547c0bde01830b7e8bd60024c-Paper.pdf).
        The images are loaded from disk in chunks.

        :param H: If not None, used as initial guess for the solution.
        :type H: array_like, shape (n_components, n_features), optional
        :param W: If not None, used as initial guess for the solution.
        :type W: array_like, shape (n_samples, n_components)
        :param max_iter: Maximum number of iterations before timing out,
            defaults to 200
        :type max_iter: int, optional
        :param compute_w: If False, W is not computed.
        :type compute_w: bool, optional
        :param compute_h: If False, H is not computes.
        :type compute_h: bool, optional
        :param vstep: vertical size of the chunks to take from data.
            When updating W, `vstep` images are retrieved from disk per iteration,
            defaults to 100.
        :type vstep: int, optional
        :param hstep: horizontal size of the chunks to take from fata.
            When updating H, `hstep` pixels are retrieved from disk per iteration,
            defaults to 1000.
        :type hstep: int, optional
        :param error_step: If None, error is not computed, else compute error for
            every `error_step` iterations.
        :type error_step: Union[None,int], optional
        """

        self.H = H
        self.W = W
        self._vstep = vstep
        self._hstep = hstep

        _logger.info("Starting NMF algorithm")

        Base.fit_transform(
            self,
            max_iter=max_iter,
            error_step=error_step,
            compute_w=compute_w,
            compute_h=compute_h,
            norm="squared_frobenius",
        )
