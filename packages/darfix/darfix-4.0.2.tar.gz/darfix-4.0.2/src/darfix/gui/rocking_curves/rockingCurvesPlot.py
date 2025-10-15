from __future__ import annotations

import logging

import numpy
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D
from silx.gui.plot import StackView
from silx.gui.plot.items.image import ImageStack

import darfix

from ...core.dataset import ImageDataset
from ...core.dimension import Dimension
from ...core.rocking_curves import fit_1d_rocking_curve
from ...core.rocking_curves import fit_2d_rocking_curve
from ...core.utils import TooManyDimensionsForRockingCurvesError
from ...dtypes import Dataset
from ..utils.axis_type_combobox import AxisTypeComboBox
from .utils import compute_contours

_logger = logging.getLogger(__file__)

FIT_IMAGE_LEGEND = "fit_image"
DATA_MARKER_LEGEND = "data_marker"
FIT_MARKER_LEGEND = "fit_marker"


class RockingCurvesPlot(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._sv = StackView(parent=self, position=True)
        self._sv.setKeepDataAspectRatio(True)
        self._sv.setColormap(Colormap(name=darfix.config.DEFAULT_COLORMAP_NAME))
        self._sv.setLabels(("Frame number", "X pixels", "Y pixels"))

        self._fitPlot = Plot2D(parent=self)
        self._fitPlot.setDefaultColormap(
            Colormap(
                name=darfix.config.DEFAULT_COLORMAP_NAME,
                normalization=darfix.config.DEFAULT_COLORMAP_NORM,
            )
        )
        self._fitPlot.setGraphTitle("Rocking curves")

        self._axisTypeComboBox = AxisTypeComboBox()
        self._axisTypeComboBox.currentTextChanged.connect(self._replotCurves)
        self._lastFitParamsLabel = qt.QLabel("")

        layout = qt.QHBoxLayout(self)
        layout.addWidget(self._sv)

        fitPlotLayout = qt.QVBoxLayout()
        fitPlotLayout.addWidget(self._fitPlot)
        fitPlotLayout.addWidget(self._lastFitParamsLabel)
        comboBoxLayout = qt.QHBoxLayout()
        comboBoxLayout.addWidget(qt.QLabel("Axis values"))
        comboBoxLayout.addWidget(self._axisTypeComboBox)
        fitPlotLayout.addLayout(comboBoxLayout)

        layout.addLayout(fitPlotLayout)

        self._dataset: ImageDataset | None = None
        self._indices = None

    def setDataset(self, dataset: Dataset):
        self._dataset = dataset.dataset
        self._indices = dataset.indices

        self._sv.getPlotWidget().sigPlotSignal.connect(self._onClickOnStack)
        self._sv.sigFrameChanged.connect(self._replotCurves)

        self._sv.setGraphTitle(self._dataset.title)

    def updateStack(self):
        nframe = self._sv.getFrameNumber()

        if self._dataset is None:
            stack = None
        else:
            stack = self._dataset.as_array3d(self._indices)

        self._sv.setStack(stack)
        self._sv.setFrameNumber(nframe)

    def _getStackDisplayedImage(self) -> numpy.ndarray | None:
        stack = self._sv.getActiveImage()
        if not isinstance(stack, ImageStack):
            return None

        stackData = stack.getStackData(copy=False)
        if stackData is None:
            return None

        return stackData[stack.getStackPosition()]

    def _onClickOnStack(self, info):
        if info["event"] != "mouseClicked":
            return

        # In case the user has clicked on a pixel in the stack
        px = info["x"]
        py = info["y"]
        image = self._getStackDisplayedImage()
        if image is not None:
            # Show vertical and horizontal lines for clicked pixel
            xlim, ylim = image.shape
            self._sv.getPlotWidget().addCurve(
                (px, px), (0, xlim), legend="x", color="r"
            )
            self._sv.getPlotWidget().addCurve(
                (0, ylim), (py, py), legend="y", color="r"
            )
        self._plotRockingCurves(px, py)

    def _replotCurves(self, i=None):
        xc = self._sv.getPlotWidget().getCurve("x")
        if xc is None:
            return
        px = xc.getXData()[0]
        py = self._sv.getPlotWidget().getCurve("y").getYData()[0]
        self._plotRockingCurves(px, py)

    def _addFitMarker(self, x: float, y: float):
        self._fitPlot.addMarker(x, y, symbol="o", legend=FIT_MARKER_LEGEND, color="r")

    def _addDataMarker(self, x: float, y: float):
        fit_image = self._fitPlot.getImage(FIT_IMAGE_LEGEND)
        if fit_image is None:
            self._fitPlot.addMarker(
                x, y, symbol="o", legend=DATA_MARKER_LEGEND, color="b"
            )
            return

        x0, y0 = fit_image.getOrigin()
        xscale, yscale = fit_image.getScale()
        # Shift by xscale / 2 and yscale / 2 to land in the middle of the pixel
        self._fitPlot.addMarker(
            x0 + xscale / 2 + x * xscale,
            y0 + yscale / 2 + y * yscale,
            symbol="o",
            legend=DATA_MARKER_LEGEND,
            color="b",
        )

    def _addFitContours(self, contours: list[numpy.ndarray]):
        fit_image = self._fitPlot.getImage(FIT_IMAGE_LEGEND)
        if fit_image is not None:
            x0, y0 = fit_image.getOrigin()
            xscale, yscale = fit_image.getScale()
        else:
            x0, y0 = 0, 0
            xscale, yscale = 1, 1
        for i, contour in enumerate(contours):
            # Shift by xscale / 2 and yscale / 2 to land in the middle of the pixel

            self._fitPlot.addCurve(
                x=x0 + xscale / 2 + contour[:, 1] * xscale,
                y=y0 + yscale / 2 + contour[:, 0] * yscale,
                linestyle="-",
                linewidth=2.0,
                legend=f"Contour {i}",
                resetzoom=False,
                color="w",
            )

    def _computeFitPlotOrigin(
        self, xdim: Dimension, ydim: Dimension
    ) -> tuple[float, float]:
        axis_type = self._axisTypeComboBox.getCurrentAxisType()
        if axis_type == "dims":
            return (xdim.start, ydim.start)

        if axis_type == "center":
            # Center by shifting by half the scaled size
            xscale, yscale = self._computeFitPlotScale(xdim, ydim)
            return (-xscale * (xdim.size / 2), -yscale * (ydim.size / 2))

        return (0.0, 0.0)

    def _computeFitPlotScale(
        self, xdim: Dimension, ydim: Dimension
    ) -> tuple[float, float]:
        return (xdim.step, ydim.step)

    def _plotRockingCurves(self, px: float, py: float):
        """
        Plot rocking curves of data and fitted data at pixel (px, py).

        :param Data data: stack of images to plot
        :param px: x pixel
        :param py: y pixel
        """
        # Get rocking curves from data
        self._fitPlot.clear()
        if self._dataset is None:
            return

        try:
            data = self._dataset.as_array3d(self._indices)
            if isinstance(data, numpy.ndarray):
                rocking_curve = data[:, int(py), int(px)]
            else:
                _logger.warning("Data is not an array!")
                return
        except IndexError:
            _logger.warning("Index out of bounds")
            return

        if self._dataset.dims.ndim == 2:
            self._plot2DRockingCurve(self._dataset, rocking_curve)
        elif self._dataset.dims.ndim == 1:
            self._plot1DRockingCurve(self._dataset, rocking_curve)
        else:
            raise TooManyDimensionsForRockingCurvesError()

    def _plot2DRockingCurve(self, dataset: ImageDataset, rocking_curve: numpy.ndarray):
        y_values = numpy.zeros(dataset.nframes)
        y_values[self._indices] = rocking_curve
        dim1 = dataset.dims.get(1)
        dim0 = dataset.dims.get(0)
        assert dim1 is not None
        assert dim0 is not None

        origin = self._computeFitPlotOrigin(dim1, dim0)
        scale = self._computeFitPlotScale(dim1, dim0)
        self._fitPlot.remove(kind="curve")
        try:
            y_gauss, pars = fit_2d_rocking_curve(
                (y_values, None),
                x_values=[
                    dataset.get_metadata_values(key=dim0.name),
                    dataset.get_metadata_values(key=dim1.name),
                ],
                shape=(dim0.size, dim1.size),
            )
            if numpy.array_equal(y_gauss, y_values):
                raise RuntimeError()
            y_gauss = numpy.reshape(y_gauss, (dim1.size, dim0.size)).T

        except (TypeError, RuntimeError):
            _logger.warning("Cannot fit")
        else:
            self._lastFitParamsLabel.setText(
                "PEAK_X:{:.3f} PEAK_Y:{:.3f} FWHM_X:{:.3f} FWHM_Y:{:.3f} AMP:{:.3f} CORR:{:.3f} BG:{:.3f}".format(
                    *pars
                )
            )
            image = numpy.reshape(y_values, (dim1.size, dim0.size)).T
            self._fitPlot.addImage(
                image,
                xlabel=dim1.name,
                ylabel=dim0.name,
                origin=origin,
                scale=scale,
                legend=FIT_IMAGE_LEGEND,
            )
            contours = compute_contours(image)
            self._addFitContours(contours)

        frameNumber = self._sv.getFrameNumber()
        self._addDataMarker(x=(frameNumber // dim0.size), y=(frameNumber % dim0.size))

    def _plot1DRockingCurve(self, dataset: ImageDataset, rocking_curve: numpy.ndarray):
        dim = dataset.dims.get(0)
        assert dim is not None
        motor_values = dataset.get_metadata_values(key=dim.name, indices=self._indices)
        if self._axisTypeComboBox.getCurrentAxisType() == "dims":
            self._fitPlot.setGraphXLabel(dim.name)
            x = motor_values
        elif self._axisTypeComboBox.getCurrentAxisType() == "center":
            self._fitPlot.setGraphXLabel("Indices")
            x = numpy.arange(len(motor_values)) - int(dim.size / 2)
        else:
            self._fitPlot.setGraphXLabel("Indices")
            x = numpy.arange(len(motor_values))

        self._fitPlot.clear()
        self._fitPlot.addCurve(x, rocking_curve, legend="data", color="b")
        self._fitPlot.setGraphYLabel("Intensity")
        i = self._sv.getFrameNumber()
        try:
            y_gauss, pars = fit_1d_rocking_curve(
                (numpy.array(rocking_curve), None), x_values=x, num_points=1000
            )
            self._lastFitParamsLabel.setText(
                "AMP:{:.3f} PEAK:{:.3f} FWHM:{:.3f} BG:{:.3f}".format(*pars)
            )
        except TypeError:
            y_gauss = rocking_curve
            _logger.warning("Cannot fit")
        else:
            x_gauss = numpy.linspace(x[0], x[-1], len(y_gauss))
            self._fitPlot.addCurve(x_gauss, y_gauss, legend="fit", color="r")
            i_gauss = i * int((len(y_gauss) - 1) / (len(x) - 1))
            self._addFitMarker(x_gauss[i_gauss], y_gauss[i_gauss])

        self._addDataMarker(x[i], rocking_curve[i])
