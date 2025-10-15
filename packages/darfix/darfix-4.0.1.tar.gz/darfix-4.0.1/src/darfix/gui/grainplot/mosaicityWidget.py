from __future__ import annotations

from enum import Enum

import numpy
from ewoksorange.gui.parameterform import block_signals
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D
from silx.gui.plot.items import ImageBase
from silx.image.marchingsquares import find_contours

from ...core.grainplot import MultiDimMomentType
from ...core.grainplot import OrientationDistData
from ...core.grainplot import compute_mosaicity
from ...dtypes import ImageDataset
from ..chooseDimensions import ChooseDimensionWidget
from ..utils.axis_type_combobox import AxisTypeComboBox
from .utils import MapType
from .utils import add_image_with_transformation


class OriDistButtonIds(Enum):
    DATA = 0
    COLOR_KEY = 1


class MosaicityWidget(qt.QWidget):
    """Widget to display and explore mosaicity plots"""

    def __init__(self, parent: qt.QWidget | None = None) -> None:
        super().__init__(parent)

        self._dataset: ImageDataset | None = None
        self._orientation_dist_data: OrientationDistData | None = None
        self._mosaicity: numpy.ndarray | None = None
        self.contours = {}

        layout = qt.QVBoxLayout()
        mosaicity_layout = qt.QHBoxLayout()

        self._chooseDimensionWidget = ChooseDimensionWidget(
            self, vertical=False, values=False
        )
        self._chooseDimensionWidget.valueChanged.connect(
            self._computeMosaicityAndOriDist
        )
        layout.addWidget(self._chooseDimensionWidget)

        self._mosaicityPlot = Plot2D(parent=self)
        self._mosaicityPlot.getColorBarWidget().hide()
        mosaicity_layout.addWidget(self._mosaicityPlot)
        self._levelsWidget = qt.QWidget()

        self._contoursPlot = Plot2D(parent=self)
        self._contoursPlot.getColorBarWidget().hide()

        self._levelsLE = qt.QLineEdit("20")
        self._levelsLE.setToolTip("Number of levels to use when finding the contours")
        self._levelsLE.setValidator(qt.QIntValidator())

        self._computeContoursB = qt.QPushButton("Find contours")
        self._computeContoursB.clicked.connect(self._computeContours)

        self._axisTypeCB = AxisTypeComboBox()
        self._axisTypeCB.currentIndexChanged.connect(self._plotOrientationData)

        self._oriDistTypeButtons = qt.QButtonGroup()
        oriDistButtonsLayout = qt.QHBoxLayout()
        dataButton = qt.QRadioButton(text="Data")
        self._oriDistTypeButtons.addButton(dataButton, id=OriDistButtonIds.DATA.value)
        oriDistButtonsLayout.addWidget(dataButton)
        colorKeyButton = qt.QRadioButton(text="Color key")
        colorKeyButton.setChecked(True)
        oriDistButtonsLayout.addWidget(colorKeyButton)
        self._oriDistTypeButtons.addButton(
            colorKeyButton, id=OriDistButtonIds.COLOR_KEY.value
        )
        self._oriDistTypeButtons.buttonClicked.connect(self._plotOrientationData)

        levelsLayout = qt.QGridLayout()
        levelsLayout.addWidget(qt.QLabel("Number of levels:"), 0, 0, 1, 1)
        levelsLayout.addWidget(self._levelsLE, 0, 1, 1, 1)
        levelsLayout.addWidget(qt.QLabel("Axis values"), 0, 2, 1, 1)
        levelsLayout.addWidget(self._axisTypeCB, 0, 3, 1, 1)
        levelsLayout.addWidget(self._computeContoursB, 1, 0, 1, 2)
        levelsLayout.addLayout(oriDistButtonsLayout, 2, 0, 1, 4)
        levelsLayout.addWidget(self._contoursPlot, 3, 0, 1, 4)
        self._levelsWidget.setLayout(levelsLayout)
        mosaicity_layout.addWidget(self._levelsWidget)

        layout.addLayout(mosaicity_layout)
        self.setLayout(layout)

    @property
    def dimension1(self) -> int:
        try:
            return self._chooseDimensionWidget.dimension[0]
        except IndexError:
            return 0

    @property
    def dimension2(self) -> int:
        try:
            return self._chooseDimensionWidget.dimension[1]
        except IndexError:
            return 1

    def getMosaicity(self):
        return self._mosaicity

    def getContoursImage(self):
        return self._contoursPlot.getImage()

    def getOrientationDist(self):
        return self._orientation_dist_data

    def setDataset(self, dataset: ImageDataset):
        self._dataset = dataset

        with block_signals(self._chooseDimensionWidget):
            self._chooseDimensionWidget.setDimensions(self._dataset.dims)
            self._chooseDimensionWidget._updateState(True)

        self._contoursPlot.setGraphTitle(
            self._dataset.title + "\n" + MultiDimMomentType.ORIENTATION_DIST.value
        )
        self._mosaicityPlot.setKeepDataAspectRatio(True)
        self._mosaicityPlot.setGraphTitle(
            self._dataset.title + "\n" + MapType.MOSAICITY.value
        )

        self._computeMosaicityAndOriDist()

    def _plotMosaicity(self):
        if self._dataset is None:
            return

        if self._mosaicity is not None:
            add_image_with_transformation(
                self._mosaicityPlot, self._mosaicity, self._dataset.transformation
            )

    def _plotOrientationData(self, state=None):
        if self._dataset is None or self._orientation_dist_data is None:
            return

        self._contoursPlot.remove(kind="curve")
        self._contoursPlot.resetZoom()

        origin = self._orientation_dist_data.origin(
            self._axisTypeCB.getCurrentAxisType()
        )

        if self._oriDistTypeButtons.checkedId() == OriDistButtonIds.COLOR_KEY.value:
            data = self._orientation_dist_data.rgb_key
            scale = self._orientation_dist_data.rgb_key_plot_scale()
        else:
            data = self._orientation_dist_data.data
            scale = self._orientation_dist_data.data_plot_scale()

        self._contoursPlot.addImage(
            data,
            xlabel=self._orientation_dist_data.x_label,
            ylabel=self._orientation_dist_data.y_label,
            origin=origin,
            scale=scale,
        )
        self._computeContours()

    def _computeContours(self):
        """
        Compute contours map based on orientation distribution.
        """
        self._contoursPlot.remove(kind="curve")
        orientation_image_plot: ImageBase | None = self._contoursPlot.getImage()

        if self._orientation_dist_data is None or orientation_image_plot is None:
            return

        min_orientation = numpy.min(self._orientation_dist_data.data)
        max_orientation = numpy.max(self._orientation_dist_data.data)

        polygons = []
        levels = []
        for i in numpy.linspace(
            min_orientation, max_orientation, int(self._levelsLE.text())
        ):
            polygons.append(find_contours(self._orientation_dist_data.data, i))
            levels.append(i)

        colormap = Colormap(
            name="temperature", vmin=min_orientation, vmax=max_orientation
        )
        colors = colormap.applyToData(levels)
        self.contours = {}
        for ipolygon, polygon in enumerate(polygons):
            # iso contours
            for icontour, contour in enumerate(polygon):
                if len(contour) == 0:
                    continue

                x = contour[:, 1]
                y = contour[:, 0]
                x_pts, y_pts = self._orientation_dist_data.to_motor_coordinates(
                    x, y, self._axisTypeCB.getCurrentAxisType()
                )
                legend = f"poly{icontour}.{ipolygon}"
                self.contours[legend] = {
                    "points": (x_pts.copy(), y_pts.copy()),
                    "color": colors[ipolygon],
                    "value": levels[ipolygon],
                    "pixels": (x, y),
                }
                self._contoursPlot.addCurve(
                    x=x_pts,
                    y=y_pts,
                    linestyle="-",
                    linewidth=2.0,
                    legend=legend,
                    resetzoom=False,
                    color=colors[ipolygon],
                )

    def _computeMosaicityAndOriDist(self):
        """
        Compute mosaicity and orientation distribution.

        Called when dimensions are changed (by setting the dataset or user interaction).
        """

        if self._dataset is None:
            return

        self._mosaicity = compute_mosaicity(
            self._dataset.moments_dims,
            x_dimension=self.dimension1,
            y_dimension=self.dimension2,
        )

        self._orientation_dist_data = OrientationDistData(
            self._dataset,
            x_dimension=self.dimension1,
            y_dimension=self.dimension2,
        )
        self._chooseDimensionWidget.setVisible(self._dataset.dims.ndim == 3)
        self._plotMosaicity()
        self._plotOrientationData()
