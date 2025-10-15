from __future__ import annotations

import numpy
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D

import darfix

from ..core.transformation import Transformation


class WeakBeamWidget(qt.QMainWindow):
    """
    Widget to recover weak beam to obtain dislocations.
    """

    sigValidate = qt.Signal()
    """Emit when user validate weak beam (ok pressed)"""
    sigApplyThreshold = qt.Signal()
    """Emit when user ask to apply a threshold"""
    sigNValueChanged = qt.Signal()
    """Emit when N value has changed"""

    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        widget = qt.QWidget()
        layout = qt.QGridLayout()

        self._nLE = qt.QLineEdit("")
        validator = qt.QDoubleValidator()
        self._nLE.setValidator(validator)
        _buttons = qt.QDialogButtonBox(parent=self)
        self._okB = _buttons.addButton(_buttons.Ok)
        self._applyThresholdB = _buttons.addButton(_buttons.Apply)

        self._plot = Plot2D()
        self._plot.setDefaultColormap(
            Colormap(
                name=darfix.config.DEFAULT_COLORMAP_NAME,
                normalization=darfix.config.DEFAULT_COLORMAP_NORM,
            )
        )
        layout.addWidget(
            qt.QLabel("Increase/decrease threshold std by a value of : "), 0, 0
        )
        layout.addWidget(self._nLE, 0, 1)
        layout.addWidget(self._plot, 1, 0, 1, 2)
        layout.addWidget(_buttons, 2, 0, 1, 2)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # connect signal / slot
        self._applyThresholdB.clicked.connect(self.sigApplyThreshold)
        self._okB.clicked.connect(self.sigValidate)
        self._nLE.editingFinished.connect(self.sigNValueChanged)

        # set up
        self.nvalue = 1

    @property
    def nvalue(self) -> float:
        text = self._nLE.text()
        value, ok = self.locale().toFloat(text)
        if not ok:
            raise ValueError(f"Could not convert string to float: '{text}'")
        return value

    @nvalue.setter
    def nvalue(self, nvalue: str | int | float):
        toStr = self.locale().toString
        self._nLE.setText(toStr(nvalue))
        self.sigNValueChanged.emit()

    def setResult(
        self, center_of_mass: numpy.ndarray, transformation: None | Transformation
    ):
        self._plot.clear()
        if transformation is None:
            self._plot.addImage(center_of_mass, xlabel="pixels", ylabel="pixels")
        else:
            if self._dataset.transformation.rotate:
                center_of_mass = numpy.rot90(center_of_mass, 3)
            self._plot.addImage(
                center_of_mass,
                origin=transformation.origin,
                scale=transformation.scale,
                xlabel=transformation.label,
                ylabel=transformation.label,
            )

    def setProcessingButtonsEnabled(self, enabled):
        self._applyThresholdB.setEnabled(enabled)
        self._okB.setEnabled(enabled)
