from typing import Optional

from silx.gui import qt
from silx.gui.plot.items import ItemChangedType
from silx.gui.plot.items.roi import RectangleROI


class RoiLimitsToolBar(qt.QToolBar):
    """Toolbar to edit a single rectangular ROI managed by a `RegionOfInterestManager`."""

    def __init__(self, parent=None, roiManager=None, roiIndex=0, title="ROI"):
        super().__init__(title, parent)
        assert roiManager is not None
        self._roiManager = roiManager
        self._roiManager.sigRoiChanged.connect(self._handleRoiPlotChanged)
        self._roiIndex = roiIndex
        self._initWidgets()

    @property
    def roi(self) -> RectangleROI:
        """The `RectangleROI` the toolbar is attached to."""
        rois = self._roiManager.getRois()
        return rois[self._roiIndex]

    def _initWidgets(self):
        """Create and init Toolbar widgets."""
        x0, y0 = self.roi.getOrigin()
        xs, ys = self.roi.getSize()

        self.addWidget(qt.QLabel("ROI: "))
        self.addWidget(qt.QLabel(" Origin: "))
        self._xOriginSpinBox = _createQSpinBox(self, int(x0), 0, 1000000)
        self._xOriginSpinBox.editingFinished[()].connect(self._handleRoiEditChanged)
        self.addWidget(self._xOriginSpinBox)

        self._yOriginSpinBox = _createQSpinBox(self, int(y0), 0, 1000000)
        self._yOriginSpinBox.editingFinished[()].connect(self._handleRoiEditChanged)
        self.addWidget(self._yOriginSpinBox)

        self.addWidget(qt.QLabel(" Size: "))
        self._xSizeSpinBox = _createQSpinBox(self, int(xs), 0, 1000000)
        self._xSizeSpinBox.editingFinished[()].connect(self._handleRoiEditChanged)
        self.addWidget(self._xSizeSpinBox)

        self._ySizeSpinBox = _createQSpinBox(self, int(ys), 0, 1000000)
        self._ySizeSpinBox.editingFinished[()].connect(self._handleRoiEditChanged)
        self.addWidget(self._ySizeSpinBox)

        self.roi.sigItemChanged.connect(self._handleRoiVisibiltyChanged)

    def _handleRoiPlotChanged(self) -> None:
        """Listen to ROI changes caused by the user dragging the ankor points on the plot."""
        x0, y0 = self.roi.getOrigin()
        xs, ys = self.roi.getSize()
        self._xOriginSpinBox.setValue(int(x0))
        self._yOriginSpinBox.setValue(int(y0))
        self._xSizeSpinBox.setValue(int(xs))
        self._ySizeSpinBox.setValue(int(ys))

    def _handleRoiEditChanged(self) -> None:
        """Listen to ROI changes caused by the user editing the spin boxes."""
        x0, y0 = self._xOriginSpinBox.value(), self._yOriginSpinBox.value()
        xs, ys = self._xSizeSpinBox.value(), self._ySizeSpinBox.value()
        self.roi.setGeometry(origin=(x0, y0), size=(xs, ys))

    def _handleRoiVisibiltyChanged(self, event=None) -> None:
        """Listen to ROI visibility changes caused by the user applying the ROI."""
        if event == ItemChangedType.VISIBLE:
            visible = self.roi.isVisible()
            self._xOriginSpinBox.setEnabled(visible)
            self._yOriginSpinBox.setEnabled(visible)
            self._xSizeSpinBox.setEnabled(visible)
            self._ySizeSpinBox.setEnabled(visible)


def _createQSpinBox(
    parent,
    value: Optional[int] = None,
    vmin: Optional[int] = None,
    vmax: Optional[int] = None,
) -> qt.QSpinBox:
    spinBox = qt.QSpinBox(parent=parent)
    if vmin is not None:
        spinBox.setMinimum(vmin)
    if vmax is not None:
        spinBox.setMaximum(vmax)
    if value is not None:
        spinBox.setValue(value)
    return spinBox
