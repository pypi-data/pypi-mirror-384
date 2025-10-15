import logging
from typing import Iterable
from typing import Optional

from silx.gui import qt

from darfix.core.noiseremoval import NoiseRemovalOperation
from darfix.core.noiseremoval import Operation
from darfix.processing.imageOperations import Method

_logger = logging.getLogger(__file__)

_KERNEL_SIZES = (3, 5)


class ParametersWidget(qt.QWidget):
    def __init__(self, parent=None):
        """Widget containing the input parameters for the noise removal operations."""
        super().__init__(parent)
        self._layout = qt.QGridLayout()
        titleFont = qt.QFont()
        titleFont.setBold(True)

        # Background subtraction
        bsLabel = qt.QLabel("Background Subtraction")
        bsLabel.setFont(titleFont)
        self._layout.addWidget(bsLabel, 0, 0, 1, 2)
        self.bsMethodsCB = qt.QComboBox(self)
        for method in Method.values():
            self.bsMethodsCB.addItem(method)
        self.bsBackgroundCB = qt.QComboBox(self)
        self.computeBS = qt.QPushButton("Compute")
        methodLabel = qt.QLabel("Method:")
        bgLabel = qt.QLabel("Background:")
        methodLabel.setMargin(0)

        self._layout.addWidget(methodLabel, 1, 0, 1, 1)
        self._layout.addWidget(bgLabel, 2, 0, 1, 1)
        self._layout.addWidget(self.bsMethodsCB, 1, 1, 1, 1)
        self._layout.addWidget(self.bsBackgroundCB, 2, 1, 1, 1)
        self._layout.addWidget(self.computeBS, 4, 1, 1, 1)
        self.computeBS.hide()

        # Hot pixel removal
        hpLabel = qt.QLabel("Hot Pixel Removal")
        hpLabel.setFont(titleFont)
        self._layout.addWidget(hpLabel, 0, 2, 1, 2)
        ksizeLabel = qt.QLabel("Kernel size:")
        self._layout.addWidget(ksizeLabel, 1, 2, 1, 1)
        self.hpSizeCB = qt.QComboBox(self)
        for size in _KERNEL_SIZES:
            self.hpSizeCB.addItem(str(size))
        self.computeHP = qt.QPushButton("Compute")
        self._layout.addWidget(self.hpSizeCB, 1, 3, 1, 1)
        self._layout.addWidget(self.computeHP, 4, 3, 1, 1)
        self.computeHP.hide()

        # Threshold removal
        tpLabel = qt.QLabel("Threshold Removal")
        tpLabel.setFont(titleFont)
        self._layout.addWidget(tpLabel, 0, 4, 1, 2)
        bottomLabel = qt.QLabel("Bottom threshold:")
        topLabel = qt.QLabel("Top threshold:")
        self._layout.addWidget(bottomLabel, 1, 4, 1, 1)
        self._layout.addWidget(topLabel, 2, 4, 1, 1)
        self.bottomLE = qt.QLineEdit()
        self.bottomLE.setValidator(qt.QIntValidator())
        self.bottomLE.setSizePolicy(qt.QSizePolicy.Ignored, qt.QSizePolicy.Preferred)
        self.topLE = qt.QLineEdit()
        self.topLE.setValidator(qt.QIntValidator())
        self.topLE.setSizePolicy(qt.QSizePolicy.Ignored, qt.QSizePolicy.Preferred)
        self.computeTP = qt.QPushButton("Compute")
        self._layout.addWidget(self.bottomLE, 1, 5, 1, 1)
        self._layout.addWidget(self.topLE, 2, 5, 1, 1)
        self._layout.addWidget(self.computeTP, 4, 5, 1, 1)
        self.computeTP.hide()

        # Mask removal
        mrLabel = qt.QLabel("Mask Removal")
        mrLabel.setFont(titleFont)
        self._layout.addWidget(mrLabel, 0, 6, 1, 2)
        maskLabel = qt.QLabel("Use mask from toolbox.\n Set values off mask to 0.")
        self.computeMR = qt.QPushButton("Compute")
        self._layout.addWidget(maskLabel, 1, 6, 1, 2)
        self._layout.addWidget(self.computeMR, 4, 7, 1, 1)
        self.computeMR.hide()

        self._layout.setHorizontalSpacing(10)
        self.setLayout(self._layout)
        self.set_default_values()

    def set_default_values(
        self, history: Optional[Iterable[NoiseRemovalOperation]] = None
    ):
        self.bottomLE.setText("0")
        self.topLE.setText("100")
        if not history:
            return
        # follow history to obtain last values set by the user
        for operation in history:
            try:
                if operation["type"] is Operation.BS:
                    index = self.bsMethodsCB.findText(
                        str(operation["parameters"]["method"])
                    )
                    if index > 0:
                        self.bsMethodsCB.setCurrentIndex(index)
                elif operation["type"] is Operation.HP:
                    index = self.hpSizeCB.findText(
                        str(operation["parameters"]["kernel_size"])
                    )
                    if index > 0:
                        self.hpSizeCB.setCurrentIndex(index)
                elif operation["type"] is Operation.THRESHOLD:
                    self.bottomLE.setText(str(operation["parameters"]["bottom"]))
                    self.topLE.setText(str(operation["parameters"]["top"]))
            except KeyError as e:
                _logger.debug(e)
                _logger.debug(f"A key is missing in {operation}")
