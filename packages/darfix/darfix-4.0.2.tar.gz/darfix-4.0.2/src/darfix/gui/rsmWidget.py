from __future__ import annotations

from silx.gui import qt

from ..pixel_sizes import PixelSize


class RSMWidget(qt.QWidget):
    """
    Widget to transform axes of RSM data
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._rotate = False
        self._moments = None
        self._pixelSize = None

        layout = qt.QGridLayout()

        pixelSizeLabel = qt.QLabel("Pixel size:")
        self._pixelSizeCB = qt.QComboBox()
        self._pixelSizeCB.addItems(PixelSize.names())
        self._rotateCB = qt.QCheckBox("Rotate RSM", self)
        layout.addWidget(pixelSizeLabel, 0, 0)
        layout.addWidget(self._pixelSizeCB, 0, 1)
        layout.addWidget(self._rotateCB, 1, 1)
        self.setLayout(layout)

    @property
    def pixelSize(self):
        return self._pixelSizeCB.currentText()

    @pixelSize.setter
    def pixelSize(self, pixelSize):
        self._pixelSizeCB.setCurrentText(str(pixelSize))

    @property
    def rotate(self):
        return self._rotateCB.isChecked()

    @rotate.setter
    def rotate(self, rotate):
        self._rotateCB.setChecked(rotate)
