from __future__ import annotations

from numbers import Number

import numpy


class Transformation:
    def __init__(self, kind: str, x: numpy.ndarray, y: numpy.ndarray, rotate: bool):
        self.x = x  # shape (sy, sx)
        self.y = y  # shape (sy, sx)
        self.rotate = rotate
        self.kind = kind

    @property
    def shape(self) -> tuple[int, int]:
        return self.x.shape

    @property
    def sx(self) -> int:
        return self.shape[1]

    @property
    def sy(self) -> int:
        return self.shape[0]

    @property
    def label(self) -> str:
        return "degrees" if self.kind == "rsm" else "µm"

    @property
    def xregular(self) -> numpy.ndarray:
        return self.xscale * numpy.arange(self.sx) + self.xorigin

    @property
    def yregular(self) -> numpy.ndarray:
        return self.yscale * numpy.arange(self.sy) + self.yorigin

    @property
    def xorigin(self) -> Number:
        return self.x[0][0]

    @property
    def yorigin(self) -> Number:
        return self.y[0][0]

    @property
    def origin(self) -> tuple[Number, Number]:
        return self.xorigin, self.yorigin

    @property
    def xscale(self) -> Number:
        x = self.x
        return (x[-1][-1] - x[0][0]) / self.sx

    @property
    def yscale(self) -> Number:
        y = self.y
        return (y[-1][-1] - y[0][0]) / self.sy

    @property
    def scale(self) -> tuple[Number, Number]:
        return self.xscale, self.yscale
