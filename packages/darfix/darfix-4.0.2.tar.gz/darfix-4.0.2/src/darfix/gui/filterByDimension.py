from __future__ import annotations

from ewoksorange.gui.parameterform import block_signals
from silx.gui import qt

from darfix.core.dimension import AcquisitionDims


class FilterByDimensionWidget(qt.QWidget):
    """
    Widget to choose a dimension from a dict and choose the value to filter
    the data. It can be included in other widget like StackView to filter the
    stack.
    """

    axisChanged = qt.Signal(int)
    filterChanged = qt.Signal(tuple)
    stateDisabled = qt.Signal()

    def __init__(self, parent=None, vertical=True):

        qt.QWidget.__init__(self, parent)

        if vertical:
            self.setLayout(qt.QVBoxLayout())
        else:
            self.setLayout(qt.QHBoxLayout())

        self.dimensions: AcquisitionDims | None = None

        self._axisComboBox = qt.QComboBox()
        self._axisComboBox.setDisabled(True)
        self._filter_by_dimension_checkbox = qt.QCheckBox("Filter by dimension", None)
        self._filter_by_dimension_checkbox.setDisabled(True)

        self.layout().addWidget(self._axisComboBox)
        self.layout().addWidget(self._filter_by_dimension_checkbox)

        self._axisComboBox.currentIndexChanged.connect(self.axisChanged)
        self._filter_by_dimension_checkbox.toggled.connect(self._updateState)

    def isFilteredByDim(self) -> bool:
        return self._filter_by_dimension_checkbox.isChecked()

    def setFilterByDim(self, filter: bool):
        return self._filter_by_dimension_checkbox.setChecked(filter)

    def getCurrentAxisName(self) -> str:
        """Axis name"""
        return self._axisComboBox.currentText()

    def getCurrentDatasetAxis(self) -> int:
        """Axis according to darfix dataset convention"""
        return self._axisComboBox.currentIndex()

    def getCurrentDimensionAxis(self) -> int:
        """Axis according to darfix dimension convention"""
        return self.dimensions.ndim - 1 - self._axisComboBox.currentIndex()

    def setDimensions(self, dimensions: AcquisitionDims) -> None:
        """Initialize widget with AcquisitionDims instance"""
        with block_signals(
            self._axisComboBox
        ):  # Do not fire valueChanged or filterChanged when setting up the widget
            self.dimensions = dimensions
            self._axisComboBox.clear()
            self._axisComboBox.addItems(self.dimensions.get_names()[::-1])
            self._axisComboBox.setDisabled(True)
            self._filter_by_dimension_checkbox.setChecked(False)
            self._filter_by_dimension_checkbox.setEnabled(self.dimensions.ndim > 1)

    def _updateState(self, checked: bool) -> None:
        """
        Updates the state of the widget.

        :param checked: If True, the widget emit signal with the current value of combo box / sliders. Else,
                    a disabled signal is emitted.

        """
        self._axisComboBox.setEnabled(checked)

        if checked:
            self.axisChanged.emit(self._axisComboBox.currentIndex())
        else:
            self.stateDisabled.emit()
