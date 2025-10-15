from __future__ import annotations

from silx.gui import qt

from ...dtypes import AxisType

AXIS_TYPES: dict[str, AxisType] = {
    "motors": "dims",
    "angles (centered)": "center",
    "angles": None,
}


class AxisTypeComboBox(qt.QComboBox):
    def __init__(self, parent: qt.QWidget | None = None) -> None:
        super().__init__(parent)

        self.addItems(AXIS_TYPES.keys())

    def getCurrentAxisType(self) -> AxisType:
        axis_type = self.currentText()
        return AXIS_TYPES[axis_type]
