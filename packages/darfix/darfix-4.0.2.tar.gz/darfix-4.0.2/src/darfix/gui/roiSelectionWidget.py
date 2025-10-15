__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "26/04/2021"

import logging

import silx
from packaging.version import Version
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot.items.roi import RectangleROI
from silx.gui.plot.StackView import StackViewMainWindow
from silx.gui.plot.tools.roi import RegionOfInterestManager

import darfix
from darfix import dtypes
from darfix.core.roi import clampROI

from .roiLimitsToolbar import RoiLimitsToolBar

_logger = logging.getLogger(__file__)


class ROISelectionWidget(qt.QWidget):
    """
    Widget that allows the user to pick a ROI in any image of the dataset.
    """

    sigValidate = qt.Signal()
    """Emit when user wants to keep the current resized dataset and move to next widget"""

    sigApply = qt.Signal()
    """Emit when user wants to Apply a ROI. Then we wait for a refinement or a validation"""

    sigReset = qt.Signal()
    """Emit when user wants to come back to the initial dataset"""

    sigROIChanged = qt.Signal()
    """Emit when the roi is changed"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setLayout(qt.QVBoxLayout())
        self._sv = StackViewMainWindow()
        _buttons = qt.QDialogButtonBox(parent=self)

        self._okB = _buttons.addButton(_buttons.Ok)
        self._applyB = _buttons.addButton(_buttons.Apply)
        self._resetB = _buttons.addButton(_buttons.Reset)
        self._okB.setDefault(False)

        self._sv.setColormap(
            Colormap(
                name=darfix.config.DEFAULT_COLORMAP_NAME,
                normalization=darfix.config.DEFAULT_COLORMAP_NORM,
            )
        )
        self._sv.setKeepDataAspectRatio(True)
        self.layout().addWidget(self._sv)
        self.layout().addWidget(_buttons)

        if Version(silx.version) < Version("2.0.0"):
            plot = self._sv.getPlot()
        else:
            plot = self._sv.getPlotWidget()

        self._roiManager = RegionOfInterestManager(plot)

        self._roi = RectangleROI()
        if Version(silx.version) < Version("2.0.0"):
            self._roi.setLabel("ROI")
        else:
            self._roi.setText("ROI")
        self._roi.setGeometry(origin=(0, 0), size=(10, 10))
        self._roi.setEditable(True)
        self._roiManager.addRoi(self._roi)

        self._roiToolBar = RoiLimitsToolBar(roiManager=self._roiManager)
        self._sv.addToolBar(qt.Qt.BottomToolBarArea, self._roiToolBar)

        # connect signal / slot
        self._applyB.clicked.connect(self.applyRoi)
        self._okB.clicked.connect(self.sigValidate)
        self._resetB.clicked.connect(self.sigReset)
        # self._roiManager.sigRoiChanged.connect(self.sigROIChanged)
        self._roi.sigRegionChanged.connect(self.sigROIChanged)

    def setDataset(self, dataset: dtypes.Dataset):
        """Saves the dataset and updates the stack with the dataset data."""
        if dataset.dataset.title != "":
            self._sv.setGraphTitle(dataset.dataset.title)
        self.setStack(dataset=dataset.dataset)

    def _setROIForNewDataset(self, dataset: dtypes.ImageDataset):
        if not isinstance(dataset, dtypes.ImageDataset):
            raise dtypes.DatasetTypeError(dataset)
        first_frame_shape = dataset.frame_shape
        center = first_frame_shape[1] // 2, first_frame_shape[0] // 2
        size = first_frame_shape[1] // 5, first_frame_shape[0] // 5
        self.setRoi(center=center, size=size)

    def setStack(self, dataset: dtypes.ImageDataset):
        """
        Sets new data to the stack.
        Maintains the current frame showed in the view.

        :param Dataset dataset: if not None, data set to the stack will be from the given dataset.
        """
        if not isinstance(dataset, dtypes.ImageDataset):
            raise TypeError(
                f"dataset is expected to be an instance of {dtypes.ImageDataset}. Got {type(dataset)}."
            )

        nframe = self._sv.getFrameNumber()
        self._sv.setStack(dataset.as_array3d())
        self._sv.setFrameNumber(nframe)

    def setRoi(self, roi=None, origin=None, size=None, center=None):
        """
        Sets a region of interest of the stack of images.

        :param RectangleROI roi: A region of interest.
        :param Tuple origin: If a roi is not provided, used as an origin for the roi
        :param Tuple size: If a roi is not provided, used as a size for the roi.
        :param Tuple center: If a roi is not provided, used as a center for the roi.
        """
        if roi is not None and (
            size is not None or center is not None or origin is not None
        ):
            _logger.warning(
                "Only using provided roi, the rest of parameters are omitted"
            )

        if roi is not None:
            self._roi = roi
        else:
            self._roi.setGeometry(origin=origin, size=size, center=center)

    def getRoi(self):
        """
        Returns the roi selected in the stackview.

        :rtype: silx.gui.plot.items.roi.RectangleROI
        """
        return self._roi

    def applyRoi(self):
        """
        Function to apply the region of interest at the data of the dataset
        and show the new data in the stack. Dataset data is not yet replaced.
        A new roi is created in the middle of the new stack.
        """
        if self._sv.getPlotWidget().getActiveImage() is None:
            return

        self.enableApplyingROI(False)
        self.sigApply.emit()

    def enableApplyingROI(self, enable: bool) -> None:
        self._applyB.setEnabled(enable)

    def _fitROIToDataset(self, dataset: dtypes.ImageDataset):
        """
        This function is called when the ROI is applied to the dataset.
        The ROI must be updated to match the contour of the new shape.
        """
        dataset_shape = dataset.frame_shape
        self._roi.setGeometry(
            size=dataset_shape[::-1],
            center=(dataset_shape[1] / 2.0, dataset_shape[0] / 2.0),
        )

    def setVisible(self, visible):
        super().setVisible(visible)  # sets okB as default
        self._okB.setDefault(False)

    def getDataset(self) -> dtypes.Dataset:
        return self._update_dataset

    def getStackViewColormap(self):
        """
        Returns the colormap from the stackView

        :rtype: silx.gui.colors.Colormap
        """
        return self._sv.getColormap()

    def setStackViewColormap(self, colormap):
        """
        Sets the stackView colormap

        :param colormap: Colormap to set
        :type colormap: silx.gui.colors.Colormap
        """
        self._sv.setColormap(colormap)

    def clearStack(self):
        """
        Clears stack.
        """
        self._sv.setStack(None)
        self._roi.setGeometry(origin=(0, 0), size=(10, 10))

    def clampRoiToDataset(self, dataset: dtypes.ImageDataset):
        frame_height, frame_width = dataset.frame_shape
        # warning: we need to invert the order of the frame shape (frame_height, frame_width) vs (frame_width, frame_height)
        new_origin, new_size = clampROI(
            roi_origin=self._roi.getOrigin(),
            roi_size=self._roi.getSize(),
            frame_origin=(0, 0),
            frame_size=(frame_width, frame_height),
        )
        self._roi.setGeometry(
            origin=new_origin,
            size=new_size,
        )

    def enableValidation(self, isAllowed: bool) -> None:
        self._okB.setEnabled(isAllowed)
