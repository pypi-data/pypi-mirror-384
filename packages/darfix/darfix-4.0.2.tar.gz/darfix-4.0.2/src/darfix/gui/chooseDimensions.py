from __future__ import annotations

from typing import Callable

from ewoksorange.gui.parameterform import block_signals
from silx.gui import qt

from darfix.core.dimension import AcquisitionDims

from ..dtypes import AxisAndValueIndices


class _DimensionWidget(qt.QWidget):
    def __init__(
        self,
        parent,
        value_callback: Callable,
        show_values: bool | None = None,
    ) -> None:
        super().__init__(parent)
        layout = qt.QGridLayout()
        self.dimensionCB = qt.QComboBox()
        self.valueCB = None
        if show_values:
            dimensionLabel = qt.QLabel("Dimension: ")
            layout.addWidget(dimensionLabel, 0, 0)
            layout.addWidget(self.dimensionCB, 0, 1)
            valueLabel = qt.QLabel("Value: ")
            self.valueCB = qt.QComboBox()
            layout.addWidget(valueLabel, 1, 0)
            layout.addWidget(self.valueCB, 1, 1)
            self.valueCB.currentIndexChanged.connect(value_callback)
        else:
            layout.addWidget(self.dimensionCB, 0, 0)
        self.setLayout(layout)
        self.setEnabled(False)

    @property
    def dimensionComboBox(self):
        return self.dimensionCB

    @property
    def valueComboBox(self):
        return self.valueCB


class ChooseDimensionDock(qt.QDockWidget):
    def __init__(self, parent=None, vertical=True, values=True, _filter=True):
        """
        Dock widget containing the ChooseDimensionWidget.
        """
        qt.QDockWidget.__init__(self, parent)
        self.setWidget(ChooseDimensionWidget(self, vertical, values, _filter))

    def widget(self) -> ChooseDimensionWidget:
        child = super().widget()
        assert isinstance(child, ChooseDimensionWidget), type(child)
        return child


class ChooseDimensionWidget(qt.QWidget):
    """
    Widget to choose a dimension from a dict and choose the value to filter
    the data. It can be included in other widget like StackView to filter the
    stack.
    """

    valueChanged = qt.Signal()
    filterChanged = qt.Signal(list, list)
    """ Signal sending the new filter dimension and value. Only emitted if filter is true."""
    stateDisabled = qt.Signal()

    def __init__(self, parent=None, vertical=True, values=True, _filter=True):
        qt.QWidget.__init__(self, parent)

        if vertical:
            self.setLayout(qt.QVBoxLayout())
        else:
            self.setLayout(qt.QHBoxLayout())
        self.value: list[int] = []
        self.show_values: bool = values
        self.dimensionWidgets: list[_DimensionWidget] = []
        self.dimension: list[int] = []
        self.dimensions: AcquisitionDims | None = None
        self.filter = _filter
        if _filter:
            self._checkbox = qt.QCheckBox("Filter by dimension", self)
            self._checkbox.toggled.connect(self._updateState)

    def isFilteredByDim(self) -> bool:
        return self._checkbox.isChecked()

    def setFilterByDim(self, filter: bool):
        return self._checkbox.setChecked(filter)

    def setDimensions(
        self,
        dimensions: AcquisitionDims,
        selectedDimAxis: int = 0,
        seletedDimIndex: int = 0,
    ):
        """
        Function that fills the corresponding comboboxes with the dimension's
        name and possible values.

        :param array_like dimensions: List of `darfix.core.dataset.Dimension`
                                      elements.
        """
        with block_signals(
            self
        ):  # Do not fire valueChanged or filterChanged when setting up the widget
            self.dimensionWidgets = []
            for i in reversed(range(self.layout().count())):
                self.layout().itemAt(i).widget().setParent(None)
            self.dimensions = dimensions
            self.dimension = []
            self.value = [0 for i in range(self.dimensions.ndim - 1)]
            for i in range(dimensions.ndim - 1):
                self._addDimensionWidget()
                self.dimension.append(i)
                self.dimensionWidgets[-1].dimensionComboBox.setCurrentIndex(i)

            self._updateDimension(selectedDimAxis, seletedDimIndex)
            if self.filter:
                self._updateState(self._checkbox.isChecked())
                self.layout().addWidget(self._checkbox)

    def _addDimensionWidget(self):
        """
        Add new widget to choose between different dimensions and values.
        """

        widget = _DimensionWidget(self, self._updateValue, self.show_values)
        dimensionCB = widget.dimensionComboBox

        assert self.dimensions is not None
        for axis, dimension in self.dimensions.items():
            dimensionCB.insertItem(axis, dimension.name)
        dimensionCB.currentIndexChanged.connect(self._updateDimension)

        self.layout().addWidget(widget)
        self.dimensionWidgets.append(widget)

    def _updateDimension(self, current_axis=-1, seletedDimIndex: int = 0):
        """
        Updates the selected dimension and set's the corresponding possible values.

        :param int axis: selected dimension's axis, only used to check valid call
            of the method.
        """
        if current_axis == -1 or current_axis is None:
            return

        assert self.dimensions is not None
        self.dimension = []
        # Init values to 0
        self.value = [0 for i in range(self.dimensions.ndim - 1)]
        # Reset all dimensions
        for dimWidget in self.dimensionWidgets:
            # Prevent signals
            dimCB = dimWidget.dimensionComboBox
            with block_signals(dimCB):
                current_axis = dimCB.currentIndex()
                # Enable / disable items in combobox
                for axis in self.dimensions.keys():
                    if axis in self.dimension:
                        dimCB.model().item(axis).setEnabled(False)
                        # If axis is already in the dimensions list, set it to
                        # next available axis.
                        if current_axis == axis:
                            current_axis = (current_axis + 1) % self.dimensions.ndim
                            dimCB.setCurrentIndex(current_axis)
                    else:
                        dimCB.model().item(axis).setEnabled(True)
            if dimCB.currentText() != "None":
                self.dimension.append(current_axis)
            valueCB = dimWidget.valueComboBox
            if valueCB is not None:
                # Set values from new dimension
                valueCB.clear()
                valueCB.addItems(
                    map(str, self.dimensions.get(current_axis).compute_unique_values())
                )
                valueCB.setCurrentIndex(seletedDimIndex)

        self.valueChanged.emit()
        if self.filter:
            self.filterChanged.emit(self.dimension, self.value)

    def _updateValue(self, index=None):
        """
        Updates the selected value.

        :param int index: selected value's index.
        """
        if self.show_values and (index is not None or index != -1):
            self.value = []
            for dimWidget in self.dimensionWidgets:
                axis = dimWidget.valueComboBox.currentIndex()
                self.value.append(axis)

            self.valueChanged.emit()
            if self.filter:
                self.filterChanged.emit(self.dimension, self.value)

    def _updateState(self, checked: bool):
        """
        Updates the state of the widget.

        :param checked: If True, the widget emits a signal
                    with the selected dimension and value. Else,
                    a disabled signal is emitted.

        """
        for dimWidget in self.dimensionWidgets:
            dimWidget.setEnabled(checked)

        if checked:
            self.filterChanged.emit(self.dimension, self.value)
        else:
            self.stateDisabled.emit()

    def setDimension(self, dimension: AxisAndValueIndices):
        axis_indices, value_indices = dimension
        for dimWidget, axis_idx, value_idx in zip(
            self.dimensionWidgets, axis_indices, value_indices
        ):

            # Do not fire signals to avoid multiple computation triggers
            # See https://gitlab.esrf.fr/XRD/darfix/-/merge_requests/446
            with block_signals(dimWidget):
                dimWidget.dimensionComboBox.setCurrentIndex(axis_idx)
                if dimWidget.valueComboBox is not None:
                    dimWidget.valueComboBox.setCurrentIndex(value_idx)

        self._checkbox.setChecked(True)
