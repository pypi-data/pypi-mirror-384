__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "12/04/2022"

import numpy
from silx.gui import icons
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot import Plot1D
from silx.gui.plot import ScatterView
from silx.gui.plot import StackView

import darfix
from darfix.io.utils import write_components

from .chooseDimensions import ChooseDimensionDock
from .utils.utils import select_output_hdf5_file_with_dialog


class DisplayComponentsWidget(qt.QMainWindow):
    """
    Widget to display rocking curves and scattering plot from a set of components
    """

    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # Widget with the type of bss and the number of components to compute
        widget = qt.QWidget(self)
        self._sv_components = StackView(parent=self)
        self._sv_components.setColormap(
            Colormap(
                name=darfix.config.DEFAULT_COLORMAP_NAME,
                normalization=darfix.config.DEFAULT_COLORMAP_NORM,
            )
        )
        self._sv_components.setKeepDataAspectRatio(True)
        self._sv_components.setGraphTitle("Components")
        self._mixing_plots_widget = MixingPlotsWidget(self)
        self._mixing_plots_widget.activeCurveChanged.connect(self._setComponent)
        self._sv_components.sigFrameChanged.connect(self._mixing_plots_widget._setCurve)

        self.bottom_widget = qt.QWidget(self)
        layout = qt.QGridLayout()
        componentsLabel = qt.QLabel("Components")
        rockingCurvesLabel = qt.QLabel("Rocking curves")
        font = qt.QFont()
        font.setBold(True)
        componentsLabel.setFont(font)
        rockingCurvesLabel.setFont(font)
        rockingCurvesLabel.setFont(font)
        layout.addWidget(componentsLabel, 1, 0, 1, 2, qt.Qt.AlignCenter)
        layout.addWidget(rockingCurvesLabel, 1, 2, 1, 2, qt.Qt.AlignCenter)
        layout.addWidget(self._sv_components, 2, 0, 2, 2)
        layout.addWidget(self._mixing_plots_widget, 2, 3, 2, 2)
        self.saveB = qt.QPushButton("Save components")
        self.saveB.pressed.connect(self._saveComp)
        layout.addWidget(self.saveB, 4, 4, 1, -1)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def hideButton(self):
        self._computeB.hide()

    def showButton(self):
        self._computeB.show()

    def setComponents(self, components, W, dimensions, values, title=""):
        """
        Components setter. Updates the plots with the components and their
        corresponding rocking curves.

        :param array_like components: stack of images with the components
        :param array_like W: array with the rocking curves intensity
        :param dict dimensions: dictionary with the values of the dimensions
        """
        self.components = numpy.round(components, 5)
        self.W = W
        self.values = values
        self.dimensions = dimensions
        self._sv_components.setStack(self.components)
        if title != "":
            self._sv_components.setTitleCallback(lambda idx: title)
        self._mixing_plots_widget.updatePlots(self.dimensions, self.W.T, values)

    def _saveComp(self):
        """Save components to a HDF5 file"""
        filename = select_output_hdf5_file_with_dialog()
        if filename:
            write_components(
                filename,
                "entry",
                self.dimensions.to_dict(),
                self.W,
                self.components,
                self.values,
                1,
            )

    def _setComponent(self, index=None):
        if index is not None:
            status = self._sv_components.blockSignals(True)
            self._sv_components.setFrameNumber(index)
            self._sv_components.blockSignals(status)

    def setStackViewColormap(self, colormap):
        """
        Sets the stackView colormap

        :param colormap: Colormap to set
        :type colormap: silx.gui.colors.Colormap
        """
        self._sv_components.setColormap(colormap)

    def getStackViewColormap(self):
        """
        Returns the colormap from the stackView

        :rtype: silx.gui.colors.Colormap
        """
        return self._sv_components.getColormap()


class MixingPlotsWidget(qt.QMainWindow):
    """
    Widget to show rocking curves and reciprocal space maps based on the mixing matrix.
    """

    activeCurveChanged = qt.Signal(int)

    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # Widget with the type of bss and the number of components to compute
        widget = qt.QWidget(self)

        self._is2dimensional = False

        self._plot_rocking_curves = PlotRockingCurves()
        self._plot_rocking_curves.sigStateDisabled.connect(self._wholeStack)
        self._plot_rocking_curves.sigMotorChanged.connect(self._updateMotorAxis)
        self._plot_rocking_curves.sigActiveCurveChanged.connect(
            self._activeCurveChanged
        )

        self._rsm_scatter = ScatterView()
        self._rsm_scatter.hide()

        self._toolbar = qt.QToolBar(parent=self)
        self._toolbar.setIconSize(self._toolbar.iconSize() * 1.2)
        curves_icon = icons.getQIcon("darfix:gui/icons/curves")
        scatter_icon = icons.getQIcon("darfix:gui/icons/scatter")
        self.curves_action = qt.QAction(curves_icon, "Curves", self)
        self.curves_action.setCheckable(True)
        self.curves_action.setChecked(True)
        self.rsm_action = qt.QAction(scatter_icon, "Scatter", self)
        self.rsm_action.setCheckable(True)
        self.curves_action.toggled.connect(self._activateCurvesPlot)
        self.rsm_action.triggered.connect(self.curves_action.toggle)
        self._toolbar.addAction(self.curves_action)
        self._toolbar.addAction(self.rsm_action)
        self._toolbar.setOrientation(qt.Qt.Vertical)
        self._toolbar.hide()

        self.bottom_widget = qt.QWidget(self)
        layout = qt.QGridLayout()
        layout.addWidget(self._plot_rocking_curves, 1, 0, 2, 2)
        layout.addWidget(self._rsm_scatter, 1, 0, 2, 2)
        layout.addWidget(self._toolbar, 1, 3, 2, 1)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def is2dimensional(self, is2dimensional):
        self._is2dimensional = is2dimensional

    @property
    def scatter(self):
        return self._rsm_scatter

    def updatePlots(self, dimensions, mixing_matrix, dimensions_values):
        self.dimensions = dimensions
        self.mixing_matrix = mixing_matrix
        self.is2dimensional(True if dimensions.ndim == 2 else False)
        self._activateCurvesPlot(True)
        self.clearPlots()
        self.values = numpy.array(list(dimensions_values.values()))

        for i, row in enumerate(self.mixing_matrix):
            self._plot_rocking_curves.getPlot().addCurve(
                numpy.arange(len(row)), row, legend=str(i)
            )

        if self._is2dimensional:
            colormap = Colormap(name="jet", normalization="linear")
            self._rsm_scatter.getPlotWidget().setGraphXLabel(
                self.dimensions.get(0).name
            )
            self._rsm_scatter.getPlotWidget().setGraphYLabel(
                self.dimensions.get(1).name
            )
            self._rsm_scatter.setData(
                self.values[0], self.values[1], self.mixing_matrix[0]
            )
            self._rsm_scatter.setColormap(colormap)
            self._rsm_scatter.resetZoom()
            self._toolbar.show()
        else:
            self._toolbar.hide()

        if self.dimensions.ndim > 1:
            # Motor dimension and index
            self.dimension = 0
            self.index = 0
            self._plot_rocking_curves._chooseDimensionDock.show()
            self._plot_rocking_curves._chooseDimensionDock.widget().setDimensions(
                self.dimensions
            )
        else:
            self._plot_rocking_curves._chooseDimensionDock.hide()

        self._plot_rocking_curves.getPlot().setActiveCurve("0")

    def _activateCurvesPlot(self, checked=False):
        if checked:
            self.rsm_action.setChecked(False)
            self._rsm_scatter.hide()
            self._plot_rocking_curves.show()
        else:
            self._plot_rocking_curves.hide()
            self._rsm_scatter.show()

    def _activeCurveChanged(self, prev_legend=None, legend=None):
        if legend:
            self.activeCurveChanged.emit(int(legend))
            if self._is2dimensional:
                self._rsm_scatter.setData(
                    self.values[0], self.values[1], self.mixing_matrix[int(legend)]
                )

    def _setCurve(self, index=-1):
        if index >= 0:
            status = self._plot_rocking_curves.blockSignals(True)
            self._plot_rocking_curves.getPlot().setActiveCurve(str(index))
            self._plot_rocking_curves.blockSignals(status)
            if self._is2dimensional:
                self._rsm_scatter.setData(
                    self.values[0], self.values[1], self.mixing_matrix[index]
                )

    def _updateFrameNumber(self, index):
        """Update the current plot.

        :param index: index of the frame to be displayed
        """
        self.index = index
        self.clearPlots()
        dim_values = numpy.take(
            self.values.reshape(self.dimensions.shape), self.index, self.dimension
        )
        for i, row in enumerate(self.mixing_matrix):
            W = numpy.take(
                row.reshape(self.dimensions.shape), self.index, self.dimension
            )
            self._plot_rocking_curves.addCurve(dim_values, W, legend=str(i))

    def _wholeStack(self):
        # Whole rocking curves are showed
        self._plot_rocking_curves.clear()
        for i, row in enumerate(self.mixing_matrix):
            self._plot_rocking_curves.addCurve(
                numpy.arange(len(row)), row, legend=str(i)
            )
        self._plot_rocking_curves.getPlot().setGraphXLabel("Image id")

    def _updateMotorAxis(self, dim=0, val=0):
        """
        Updates the motor to show the rocking curve from.

        :param int axis: 0 if no motor is chosen, else axis of the motor.
        """
        dimension = [dim, val]
        # Make sure dimension and value are lists
        if type(dimension[0]) is int:
            dimension[0] = [dimension[0]]
            dimension[1] = [dimension[1]]
        indx = numpy.arange(len(self.mixing_matrix[0])).reshape(self.dimensions.shape)
        # For every axis, get corresponding elements
        for i, j in sorted(zip(dimension[0], dimension[1])):
            # Flip axis to be consistent with the data shape
            axis = self.dimensions.ndim - i - 1
            # dim_values = numpy.array(list(self.dimensions.values())[dim])
            indx = indx.take(indices=j, axis=axis)
        self._plot_rocking_curves.clear()
        axis = 0
        for i in range(self.dimensions.ndim):
            if i not in dimension[0]:
                axis = i
        text = self.dimensions.get(axis).name
        self._plot_rocking_curves.getPlot().setGraphXLabel(text)
        if len(indx.shape) == 1:
            for i, row in enumerate(self.mixing_matrix):
                W = row[indx]
                self._plot_rocking_curves.addCurve(
                    self.values[axis][indx], W, legend=str(i)
                )

    def clearPlots(self):
        self._plot_rocking_curves.clear()


class PlotRockingCurves(qt.QMainWindow):
    """
    Widget to plot the rocking curves of the components. It can be filtered
    to show only the rocking curves of a certain moving dimension.
    """

    sigStateDisabled = qt.Signal()
    sigMotorChanged = qt.Signal(list, list)
    sigActiveCurveChanged = qt.Signal(object, object)

    def __init__(self, parent=None, dimensions=None):
        qt.QMainWindow.__init__(self, parent)

        self._plot = Plot1D()
        self._plot.setGraphTitle("Rocking curves")
        self._plot.setGraphXLabel("Image id")
        self._plot.sigActiveCurveChanged.connect(self.sigActiveCurveChanged)

        self._chooseDimensionDock = ChooseDimensionDock(self, vertical=False)
        self._chooseDimensionDock.hide()
        self._motors = qt.QWidget()
        self._motors.hide()
        layout = qt.QVBoxLayout()
        layout.addWidget(self._plot)

        centralWidget = qt.QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.addDockWidget(qt.Qt.BottomDockWidgetArea, self._chooseDimensionDock)

        self.addCurve = self._plot.addCurve
        self._chooseDimensionDock.widget().filterChanged.connect(self.sigMotorChanged)
        self._chooseDimensionDock.widget().stateDisabled.connect(self.sigStateDisabled)

    def clear(self):
        self._plot.clear()

    def getPlot(self):
        return self._plot
