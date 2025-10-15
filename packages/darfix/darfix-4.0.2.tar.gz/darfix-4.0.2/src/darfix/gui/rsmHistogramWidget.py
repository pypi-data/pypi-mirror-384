from __future__ import annotations

from typing import List

import numpy
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot import Plot2D
from silx.io.dictdump import dicttonx

from ..dtypes import Dataset
from ..io.utils import create_nxdata_dict
from ..pixel_sizes import PixelSize
from .utils.utils import select_output_hdf5_file_with_dialog


class _LineEditsWidget(qt.QWidget):
    def __init__(self, parent, dims=1, validator=None, placeholder=None):
        qt.QWidget.__init__(self, parent)
        layout = qt.QHBoxLayout()
        if placeholder:
            assert len(placeholder) == dims
        self._lineEdits = []
        for i in range(dims):
            lineEdit = qt.QLineEdit(parent=self)
            if placeholder:
                lineEdit.setPlaceholderText(placeholder[i])
            if validator:
                lineEdit.setValidator(validator)
            self._lineEdits.append(lineEdit)
            layout.addWidget(lineEdit)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @property
    def value(self):
        values = []
        for le in self._lineEdits:
            values += [le.text() if le.text() != "" else None]
        return values

    def setValue(self, values: List[int]):
        assert type(values) is list

        for i, value in enumerate(values):
            self._lineEdits[i].setText(str(value))
            self._lineEdits[i].setCursorPosition(0)


class RSMHistogramWidget(qt.QWidget):
    """
    Widget to compute Reciprocal Space Map
    """

    sigComputeClicked = qt.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.dataset: Dataset | None = None

        self._idx = [(2, 1), (2, 0), (1, 0)]

        layout = qt.QGridLayout()
        label = qt.QLabel("Q:")
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label, 0, 0, 1, 1)
        self._q = _LineEditsWidget(self, 3, qt.QIntValidator(), ["h", "k", "l"])
        self._q.setValue([1, 0, 1])
        layout.addWidget(self._q, 0, 1, 1, 2)
        label = qt.QLabel("Pseudocubic lattice:")
        label.setFont(font)
        layout.addWidget(label, 1, 0, 1, 2)
        self._a = qt.QLineEdit()
        self._a.setValidator(qt.QDoubleValidator())
        self.a = 4.08
        layout.addWidget(self._a, 1, 1, 1, 2)
        label = qt.QLabel("Map range:")
        label.setFont(font)
        layout.addWidget(label, 2, 0, 1, 2)
        self._map_range = qt.QLineEdit()
        self._map_range.setValidator(qt.QDoubleValidator())
        self.map_range = 0.008
        layout.addWidget(self._map_range, 2, 1, 1, 2)
        label = qt.QLabel("Detector:")
        label.setFont(font)
        layout.addWidget(label, 3, 0, 1, 2)
        self._detector = qt.QComboBox()
        self._detector.addItems(PixelSize.names())
        layout.addWidget(self._detector, 3, 1, 1, 2)
        label = qt.QLabel("Units:")
        label.setFont(font)
        layout.addWidget(label, 4, 0, 1, 2)
        self._units = qt.QComboBox()
        self._units.addItems(["Poulsen", "Gorfman"])
        layout.addWidget(self._units, 4, 1, 1, 2)
        label = qt.QLabel("n:")
        label.setFont(font)
        layout.addWidget(label, 5, 0, 1, 1)
        self._n = _LineEditsWidget(self, 3, qt.QIntValidator(), ["h", "k", "l"])
        self._n.setValue([0, 1, 0])
        layout.addWidget(self._n, 5, 1, 1, 2)
        label = qt.QLabel("Map shape:")
        label.setFont(font)
        layout.addWidget(label, 6, 0, 1, 1)
        self._map_shape = _LineEditsWidget(self, 3, qt.QIntValidator(), ["x", "y", "z"])
        self._map_shape.setValue([200, 200, 200])
        layout.addWidget(self._map_shape, 6, 1, 1, 2)
        label = qt.QLabel("Energy:")
        label.setFont(font)
        layout.addWidget(label, 7, 0, 1, 2)
        self._energy = qt.QLineEdit()
        self._energy.setValidator(qt.QDoubleValidator())
        self.energy = 17
        layout.addWidget(self._energy, 7, 1, 1, 2)
        self._computeB = qt.QPushButton("Compute")
        layout.addWidget(self._computeB, 8, 2, 1, 1)
        self._computeB.clicked.connect(self.sigComputeClicked.emit)
        self._plotWidget = qt.QWidget()
        self._plotWidget.setLayout(qt.QHBoxLayout())
        layout.addWidget(self._plotWidget, 9, 0, 1, 3)
        self._plotWidget.hide()
        self._exportButton = qt.QPushButton("Export maps")
        self._exportButton.hide()
        layout.addWidget(self._exportButton, 10, 2, 1, 1)
        self._exportButton.clicked.connect(self.exportMaps)

        self.setLayout(layout)
        self.setMinimumWidth(650)

    def setDataset(self, dataset: Dataset):
        self.dataset = dataset
        for i in reversed(range(self._plotWidget.layout().count())):
            self._plotWidget.layout().itemAt(i).widget().setParent(None)

        self._plotWidget.hide()
        self._exportButton.hide()

        self._plots = []
        for i in range(len(self._idx)):
            self._plots += [Plot2D(parent=self)]
            self._plots[-1].setDefaultColormap(Colormap(name="viridis"))
            self._plotWidget.layout().addWidget(self._plots[-1])

    def _toFloat(self, text: str) -> float:
        value, ok = self.locale().toFloat(text)
        if not ok:
            raise ValueError(f"Could not convert string to float: '{text}'")
        return value

    def _toStr(self, value: float) -> str:
        return self.locale().toString(value)

    @property
    def q(self):
        return numpy.array(self._q.value, dtype=int)

    @q.setter
    def q(self, q: List[int]):
        self._q.setValue(q)

    @property
    def a(self):
        return self._toFloat(self._a.text())

    @a.setter
    def a(self, a: float):
        self._a.setText(self._toStr(a))

    @property
    def map_range(self):
        return self._toFloat(self._map_range.text())

    @map_range.setter
    def map_range(self, map_range: float):
        self._map_range.setText(self._toStr(map_range))

    @property
    def detector(self):
        return self._detector.currentText()

    @detector.setter
    def detector(self, detector: str):
        self._detector.setCurrentText(detector)

    @property
    def units(self):
        return self._units.currentText()

    @units.setter
    def units(self, units: str):
        self._units.setCurrentText(units)

    @property
    def n(self):
        return numpy.array(self._n.value, dtype=int)

    @n.setter
    def n(self, n: List[int]):
        self._n.setValue(n)

    @property
    def map_shape(self):
        return numpy.array(self._map_shape.value, dtype=int)

    @map_shape.setter
    def map_shape(self, map_shape: List[int]):
        self._map_shape.setValue(map_shape)

    @property
    def energy(self):
        return self._toFloat(self._energy.text())

    @energy.setter
    def energy(self, energy: float):
        self._energy.setText(self._toStr(energy))

    def updatePlot(self, arr: numpy.ndarray, edges: numpy.ndarray):
        arr = numpy.nan_to_num(arr)

        self._projections = []

        if self._units.currentText().lower() == "poulsen":
            self.labels = [r"$q_{rock}$", r"$q_{\perp}$", r"$q_{||}$"]
        else:
            self.labels = ["h", "k", "l"]

        for idx, (i, j) in enumerate(self._idx):
            self._projections += [numpy.sum(arr, axis=idx)]
            xscale = (edges[i][-1] - edges[i][0]) / len(edges[i])
            yscale = (edges[j][-1] - edges[j][0]) / len(edges[j])
            self._plots[idx].addImage(
                self._projections[-1],
                scale=(xscale, yscale),
                origin=(edges[i][0], edges[j][0]),
                xlabel=self.labels[i],
                ylabel=self.labels[j],
            )

        self._edges = edges

        self._plotWidget.show()
        self._exportButton.show()

    def exportMaps(self):
        """
        Creates dictionary with maps information and exports it to a nexus file
        """
        entry = "entry"

        nx = {
            entry: {"@NX_class": "NXentry"},
            "@NX_class": "NXroot",
            "@default": "entry",
        }

        for idx, (j, i) in enumerate(self._idx):
            axis = [self._edges[i][:-1], self._edges[j][:-1]]
            nx["entry"][str(idx)] = create_nxdata_dict(
                self._projections[idx],
                self.labels[i] + "_" + self.labels[j],
                axis,
                axes_names=[self.labels[i], self.labels[j]],
            )

        filename = select_output_hdf5_file_with_dialog()
        if filename:
            dicttonx(nx, filename)
