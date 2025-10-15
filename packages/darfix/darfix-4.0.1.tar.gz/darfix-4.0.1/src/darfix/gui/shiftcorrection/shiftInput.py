from __future__ import annotations

from typing import Tuple

from silx.gui import qt

from ..utils.vspacer import VSpacer


class ShiftInput(qt.QWidget):
    """
    Widget used to obtain the double parameters for the shift correction.
    """

    shiftChanged = qt.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.findShiftB = qt.QPushButton("Find shift")
        self.abortShiftB = qt.QPushButton("Abort")
        # First dim is displayed on vertical axis, second on horizontal
        firstDimLabel = qt.QLabel("Vertical shift per frame (pixels)")
        secondDimLabel = qt.QLabel("Horizontal shift per frame (pixels)")
        self._firstDimLE = qt.QLineEdit("0.0")
        self._secondDimLE = qt.QLineEdit("0.0")
        self.correctionB = qt.QPushButton("Correct")

        self._firstDimLE.setValidator(qt.QDoubleValidator())
        self._secondDimLE.setValidator(qt.QDoubleValidator())

        self._firstDimLE.editingFinished.connect(self.shiftChanged.emit)
        self._secondDimLE.editingFinished.connect(self.shiftChanged.emit)

        layout = qt.QGridLayout()

        layout.addWidget(self.findShiftB, 0, 0, 1, 1)
        layout.addWidget(self.abortShiftB, 0, 1, 1, 1)
        layout.addWidget(firstDimLabel, 1, 0)
        layout.addWidget(secondDimLabel, 2, 0)
        layout.addWidget(self._firstDimLE, 1, 1)
        layout.addWidget(self._secondDimLE, 2, 1)
        layout.addWidget(self.correctionB, 4, 0, 1, 2)

        layout.addWidget(VSpacer())

        self.setLayout(layout)

    def getShift(self) -> Tuple[float, float]:
        return float(self._firstDimLE.text()), float(self._secondDimLE.text())

    def setShift(self, shift: Tuple[float, float]):
        first_dim_shift, second_dim_shift = shift
        self._firstDimLE.setText(str(first_dim_shift))
        self._firstDimLE.setCursorPosition(0)
        self._secondDimLE.setText(str(second_dim_shift))
        self._secondDimLE.setCursorPosition(0)
