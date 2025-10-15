from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot.StackView import StackViewMainWindow

import darfix
from darfix import dtypes
from darfix.core.state_of_operation import Operation
from darfix.gui.utils.message import missing_dataset_msg


class BinningWidget(qt.QMainWindow):
    """
    Widget to bin the data for fastest processing
    """

    sigComputed = qt.Signal()
    """Emit once the user has validated the binned dataset"""

    sigApply = qt.Signal()
    """Emit when the user ask to apply the binning"""

    sigScaleChanged = qt.Signal(float)
    """Emit when the scale changed"""

    sigAbort = qt.Signal()
    """Emit when user request to abort processing"""

    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        self._display_tooltip_msg = True

        widget = qt.QWidget()
        layout = qt.QGridLayout()

        self._dataset = None
        # original dataset, the one treated. Keep it to be able to re-apply modifications
        self._update_dataset = None
        # dataset with applied modifications. This is the one displayed
        self.indices = None
        self.bg_indices = None
        self.bg_dataset = None

        self._scaleLE = qt.QLineEdit("1")
        validator = qt.QDoubleValidator()
        self._scaleLE.setValidator(validator)
        _buttons = qt.QDialogButtonBox(parent=self)
        self._okB = _buttons.addButton(_buttons.Ok)
        self._applyB = _buttons.addButton(_buttons.Apply)
        self._abortB = _buttons.addButton(_buttons.Abort)
        self._resetB = _buttons.addButton(_buttons.Reset)
        self._abortB.hide()

        self._applyB.released.connect(self._applyBinning)
        self._okB.released.connect(self.apply)
        self._resetB.released.connect(self.resetStack)
        self._abortB.released.connect(self.sigAbort)

        self._sv = StackViewMainWindow()
        self._sv.setKeepDataAspectRatio(True)
        self._sv.setColormap(
            Colormap(
                name=darfix.config.DEFAULT_COLORMAP_NAME,
                normalization=darfix.config.DEFAULT_COLORMAP_NORM,
            )
        )
        layout.addWidget(qt.QLabel("Scale: "), 0, 0)
        layout.addWidget(self._scaleLE, 0, 1)
        layout.addWidget(self._sv, 1, 0, 1, 2)
        layout.addWidget(_buttons, 2, 0, 1, 2)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # connect signal / slot
        self._scaleLE.editingFinished.connect(self._scaleChanged)

    @property
    def scale(self) -> float:
        return float(self._scaleLE.text())

    @scale.setter
    def scale(self, scale: float):
        if scale != self.scale:
            self._scaleLE.setText(str(scale))
            self._scaleChanged()

    def _scaleChanged(self, *args, **kwargs):
        self.sigScaleChanged.emit(self.scale)

    def updateResultDataset(self, dataset: dtypes.ImageDataset):
        self._update_dataset = dataset
        self.setStack(self._update_dataset)

    def setDataset(self, dataset: dtypes.Dataset):
        self._dataset = dataset.dataset
        self._update_dataset = dataset.dataset
        self.indices = dataset.indices
        self.bg_indices = dataset.bg_indices
        self.bg_dataset = dataset.bg_dataset
        self.setStack()
        if self._display_tooltip_msg:
            self.display_tooltip_msg()

    def display_tooltip_msg(self):
        msg = qt.QMessageBox()
        msg.setIcon(qt.QMessageBox.Information)
        msg.setText(
            "Binning can be used to reduce the computation time of the operations in the workflow.\n"
            + "The scale is the factor to which the images will be rescaled.\n"
            + "After the correct parameters are found, you can remove the binning widget from the workflow"
            + " and execute it either with the GUI or using ewoks.\nBinning should be applied after any"
            + " ROI to have original images size and not the binned one.\n"
        )
        msg.setWindowTitle("Fit succeeded!")
        msg.setStandardButtons(qt.QMessageBox.Ok)
        msg.exec()

    def setStack(self, dataset=None):
        """
        Sets new data to the stack.
        Mantains the current frame showed in the view.

        :param Dataset dataset: if not None, data set to the stack will be from the given dataset.
        """
        if dataset is None:
            dataset = self._dataset
        nframe = self._sv.getFrameNumber()
        self._sv.setStack(dataset.as_array3d())
        self._sv.setFrameNumber(nframe)

    def _startComputation(self):
        self._applyB.setEnabled(False)
        self._okB.setEnabled(False)

    def _endComputation(self):
        self._applyB.setEnabled(True)
        self._okB.setEnabled(True)
        self._abortB.hide()
        self._abortB.setEnabled(True)

    def _applyBinning(self):
        if self._dataset is None:
            missing_dataset_msg()
            return
        self._startComputation()
        self.sigApply.emit()

    def abort(self):
        self._abortB.setEnabled(False)
        self._update_dataset.stop_operation(Operation.BINNING)

    def apply(self):
        self.sigComputed.emit()

    def resetStack(self):
        """
        Restores stack with the dataset data.
        """
        self._update_dataset = self._dataset
        self.setStack(self._dataset)

    def clearStack(self):
        """
        Clears stack.
        """
        self._sv.setStack(None)
