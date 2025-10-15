from __future__ import annotations

import logging

from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D
from silx.gui.plot.items import ImageBase
from silx.io.dictdump import dicttonx

from ... import dtypes
from ...core.grainplot import OrientationDistImage
from ...core.grainplot import generate_grain_maps_nxdict
from ..utils.utils import select_output_hdf5_file_with_dialog
from .mosaicityWidget import MosaicityWidget
from .utils import MapType
from .utils import add_image_with_transformation

_logger = logging.getLogger(__file__)


class GrainPlotWidget(qt.QMainWindow):
    """
    Widget to show a series of maps for the analysis of the data.
    """

    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        self.dataset: dtypes.ImageDataset | None = None
        self._plots: list[Plot2D] = []

        self._mapTypeComboBox = qt.QComboBox()
        self._mapTypeComboBox.addItems(MapType.values())
        self._mapTypeComboBox.currentTextChanged.connect(self._updatePlot)

        self._plotWidget = qt.QWidget()
        plotsLayout = qt.QHBoxLayout()
        self._plotWidget.setLayout(plotsLayout)
        widget = qt.QWidget(parent=self)
        layout = qt.QVBoxLayout()

        self._mosaicity_widget = MosaicityWidget()

        self._exportButton = qt.QPushButton("Export maps")
        self._exportButton.clicked.connect(self.exportMaps)

        self._messageWidget = qt.QLabel("No dataset in input.")

        layout.addWidget(self._mapTypeComboBox)
        layout.addWidget(self._plotWidget)
        layout.addWidget(self._mosaicity_widget)
        layout.addWidget(self._messageWidget)
        layout.addWidget(self._exportButton)
        self._plotWidget.hide()
        self._mosaicity_widget.hide()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self._mapTypeComboBox.setDisabled(True)
        self._exportButton.setDisabled(True)

    def setMessage(self, message: str):
        self._messageWidget.setText(message)

    def setDataset(self, dataset: dtypes.Dataset):
        if len(dataset.dataset.moments_dims) == 0:
            raise ValueError(
                "Please compute moments (dataset.apply_moments) before setting the dataset"
            )

        self.dataset = dataset.dataset

        for i in reversed(range(self._plotWidget.layout().count())):
            self._plotWidget.layout().itemAt(i).widget().setParent(None)

        self._plots.clear()
        for dim in self.dataset.dims.values():
            plot = Plot2D(parent=self)
            plot.setKeepDataAspectRatio(True)
            plot.setGraphTitle(self.dataset.title + "\n" + dim.name)
            plot.setDefaultColormap(Colormap(name="viridis"))
            self._plots.append(plot)
            self._plotWidget.layout().addWidget(plot)

        # Enable mosaicity if ndim >= 2
        if self.dataset.dims.ndim >= 2:
            self._mosaicity_widget.setDataset(self.dataset)
            self._mapTypeComboBox.model().item(4).setEnabled(True)
            self._mapTypeComboBox.setCurrentText(MapType.MOSAICITY.value)
        else:
            self._mapTypeComboBox.model().item(4).setEnabled(False)
            self._mapTypeComboBox.setCurrentText(MapType.COM.value)
        # Force plot update since setCurrentText does not fire currentTextChanged if the text is the same
        # https://doc.qt.io/qt-6/qcombobox.html#currentTextChanged
        self._updatePlot(self._mapTypeComboBox.currentText())

        self._messageWidget.hide()
        self._mapTypeComboBox.setEnabled(True)
        self._exportButton.setEnabled(True)

    def _updatePlot(self, raw_map_type: str):
        """
        Update shown plots in the widget
        """

        map_type = MapType(raw_map_type)
        if map_type == MapType.MOSAICITY:
            self._mosaicity_widget.show()
            self._plotWidget.hide()
            return

        if self.dataset is None:
            return

        moments = self.dataset.moments_dims
        self._mosaicity_widget.hide()
        if map_type == MapType.FWHM:
            self._plotWidget.show()
            for i, plot in enumerate(self._plots):
                self._addImage(plot, moments[i][1])
        elif map_type == MapType.COM:
            self._plotWidget.show()
            for i, plot in enumerate(self._plots):
                self._addImage(plot, moments[i][0])
        elif map_type == MapType.SKEWNESS:
            self._plotWidget.show()
            for i, plot in enumerate(self._plots):
                self._addImage(plot, moments[i][2])
        elif map_type == MapType.KURTOSIS:
            self._plotWidget.show()
            for i, plot in enumerate(self._plots):
                self._addImage(plot, moments[i][3])
        else:
            _logger.warning("Unexisting map method")

    def _generate_maps_nxdict(self) -> dict:
        orientation_image_plot: ImageBase | None = (
            self._mosaicity_widget.getContoursImage()
        )
        orientation_dist_data = self._mosaicity_widget.getOrientationDist()

        if orientation_image_plot and orientation_dist_data:
            orientation_dist_image = OrientationDistImage(
                data=orientation_dist_data.data,
                as_rgb=orientation_dist_data.as_rgb,
                origin=orientation_image_plot.getOrigin(),
                scale=orientation_image_plot.getScale(),
                xlabel=orientation_image_plot.getXLabel(),
                ylabel=orientation_image_plot.getYLabel(),
                contours=self._mosaicity_widget.contours,
            )
        else:
            orientation_dist_image = None

        return generate_grain_maps_nxdict(
            self.dataset,
            self._mosaicity_widget.getMosaicity(),
            orientation_dist_image,
        )

    def exportMaps(self):
        """
        Creates dictionary with maps information and exports it to a nexus file
        """
        nx = self._generate_maps_nxdict()

        filename = select_output_hdf5_file_with_dialog()
        if filename:
            dicttonx(nx, filename)

    def _addImage(self, plot, image):
        if self.dataset is None:
            transformation = None
        else:
            transformation = self.dataset.transformation
        add_image_with_transformation(plot, image, transformation)
