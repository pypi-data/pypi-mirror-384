__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "22/12/2020"

import numpy
from silx.gui import qt

from darfix import dtypes
from darfix.tasks.blindsourceseparation import Method

from .displayComponentsWidget import DisplayComponentsWidget
from .operationThread import OperationThread


class BSSWidget(qt.QMainWindow):
    """
    Widget to apply blind source separation.
    """

    sigComputed = qt.Signal(Method, int)

    sigNbComponentsChanged = qt.Signal(int)
    """emit when the number of component has been changed"""

    sigMethodChanged = qt.Signal(str)
    """emit when the method (PCA, NICA...) changed"""

    DEFAULT_METHOD = Method.PCA.value

    DEFAULT_N_COMP = 1

    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        # Method widget
        methodLabel = qt.QLabel("Method: ")
        self.methodCB = qt.QComboBox()
        for member in Method.members():
            self.methodCB.addItem(member.name)
            self.methodCB.setItemData(
                self.methodCB.count() - 1,
                Method.get_description(member),
                qt.Qt.ToolTipRole,
            )
        self.methodCB.setCurrentText(self.DEFAULT_METHOD)
        self.methodCB.currentTextChanged.connect(self.sigMethodChanged)
        # Number of components
        nComponentsLabel = qt.QLabel("Num comp:")
        self.nComponentsLE = qt.QLineEdit(str(self.DEFAULT_N_COMP))
        self.nComponentsLE.setValidator(qt.QIntValidator())
        self.nComponentsLE.editingFinished.connect(self._nbComponentEdited)
        # Compute BSS with the number of components
        self.computeButton = qt.QPushButton("Compute")
        self.computeButton.setEnabled(False)
        # Detect optimal number of components
        self.detectButton = qt.QPushButton("Detect number of components")
        self.detectButton.setEnabled(False)
        self.detectButton.clicked.connect(self._detectComp)

        # Add widgets to layout
        layout = qt.QGridLayout()
        layout.addWidget(methodLabel, 0, 0, 1, 1)
        layout.addWidget(self.methodCB, 0, 1, 1, 1)
        layout.addWidget(nComponentsLabel, 0, 2, 1, 1)
        layout.addWidget(self.nComponentsLE, 0, 3, 1, 1)
        layout.addWidget(self.computeButton, 0, 4, 1, 1)
        layout.addWidget(self.detectButton, 1, 4, 1, 1)
        # Top Widget with the type of bss and the number of components to compute
        top_widget = qt.QWidget(self)
        top_widget.setLayout(layout)

        # Widget to display the components
        self._displayComponentsWidget = DisplayComponentsWidget()
        self._displayComponentsWidget.hide()

        # Main widget is a Splitter with the top widget and the displayComponentsWidget
        self.splitter = qt.QSplitter(qt.Qt.Vertical)
        self.splitter.addWidget(top_widget)
        self.splitter.addWidget(self._displayComponentsWidget)
        self.setCentralWidget(self.splitter)

    def setMethod(self, method: Method):
        if method in (None, ""):
            method = self.DEFAULT_METHOD
        method = Method.from_value(method)
        self.methodCB.setCurrentText(method.value)

    def getMethod(self) -> Method:
        return Method.from_value(self.methodCB.currentText())

    def setNComp(self, n_comp: int):
        if n_comp in ("0", 0):
            n_comp = self.DEFAULT_N_COMP
        self.nComponentsLE.setText(str(n_comp))

    def getNComp(self) -> int:
        return int(self.nComponentsLE.text())

    def hideButton(self):
        self._computeB.hide()

    def showButton(self):
        self._computeB.show()

    def setDataset(self, dataset: dtypes.Dataset):
        self.dataset = dataset.dataset
        self.indices = dataset.indices
        self.bg_indices = dataset.bg_indices
        self.bg_dataset = dataset.bg_dataset
        self.computeButton.setEnabled(True)
        self.detectButton.setEnabled(True)

    def _nbComponentEdited(self, *args, **kwargs):
        self.sigNbComponentsChanged.emit(int(self.nComponentsLE.text()))

    def _displayComponents(
        self, dataset: dtypes.ImageDataset, indices, bg_indices, comp, W
    ):
        """
        :param dataset: dataset for which we want to display the components
        :param indices: dataset indices
        :param bg_indices: background indices
        :param comp: components
        :param W: Matrix with the rocking curves values
        """
        if not isinstance(dataset, dtypes.ImageDataset):
            raise TypeError(
                f"dataset is expected to be an instance of {dtypes.ImageDataset}. Got {type(dataset)}."
            )
        # self._thread.finished.disconnect(self._displayComponents)
        # comp, self.W = self._thread.data
        n_comp = int(self.nComponentsLE.text())
        if comp.shape[0] < n_comp:
            n_comp = comp.shape[0]
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Information)
            msg.setText("Found only {0} components".format(n_comp))
            msg.setStandardButtons(qt.QMessageBox.Ok)
            msg.exec()
        shape = dataset.frame_shape
        comp = comp.reshape(n_comp, shape[0], shape[1])
        self._displayComponentsWidget.show()
        self.computeButton.setEnabled(True)
        self.nComponentsLE.setEnabled(True)
        self.detectButton.setEnabled(True)
        if bg_indices is not None:
            # If filter data is activated, the matrix W has reduced dimensionality, so reshaping is not possible
            # Create empty array with shape the total number of frames
            W = numpy.zeros((dataset.nframes, n_comp))
            # Set actual values of W where threshold of filter is True
            W[indices] = W
        self._displayComponentsWidget.setComponents(
            comp,
            W,
            dataset.dims,
            dataset.get_dimensions_values(),
            dataset.title,
        )

    def _detectComp(self):
        self.detectButton.setEnabled(False)
        self.computeButton.setEnabled(False)
        self._thread = OperationThread(self, self.dataset.pca)
        self._thread.setArgs(return_vals=True)
        self._thread.finished.connect(self._setNumComp)
        self._thread.start()

    def _setNumComp(self):
        self._thread.finished.disconnect(self._setNumComp)
        vals = self._thread.data
        vals /= numpy.sum(vals)
        components = len(vals[vals > 0.01])
        self.detectButton.setEnabled(True)
        self.computeButton.setEnabled(True)
        self.nComponentsLE.setText(str(components))
        self.sigNbComponentsChanged.emit(components)

    def getDisplayComponentsWidget(self):
        return self._displayComponentsWidget
