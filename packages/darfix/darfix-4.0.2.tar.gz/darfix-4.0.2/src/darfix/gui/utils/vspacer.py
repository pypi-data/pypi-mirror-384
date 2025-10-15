from __future__ import annotations

from silx.gui import qt


class VSpacer(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(qt.QVBoxLayout())
        self.setSizePolicy(
            qt.QSizePolicy.Policy.Minimum, qt.QSizePolicy.Policy.Expanding
        )
