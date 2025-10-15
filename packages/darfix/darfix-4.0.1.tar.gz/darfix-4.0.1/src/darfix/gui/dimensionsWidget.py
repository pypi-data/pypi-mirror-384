from __future__ import annotations

import logging

import numpy
from silx.gui import qt

from darfix.core.dimension import Dimension
from darfix.tasks.dimensiondefinition import DimensionDefinition

_logger = logging.getLogger(__file__)


class DimensionTable(qt.QTableWidget):
    """
    Widget used to define the number of dimension and with which values they are
    mapped
    """

    sigUpdateDims = qt.Signal()
    """
    If dim added, removed or size modified
    """

    _V_HEADERS = ["Axis", "Name", "Size", "Start", "Stop", ""]

    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__(parent)

        self.setColumnCount(len(self._V_HEADERS))
        self.setHorizontalHeaderLabels(self._V_HEADERS)
        header = self.horizontalHeader()
        header.setMinimumSectionSize(50)
        for iColumn in range(len(self._V_HEADERS)):
            header.setSectionResizeMode(iColumn, qt.QHeaderView.Stretch)
        self.verticalHeader().hide()
        self._dims: dict[int, DimensionItem] = {}

    def clear(self):
        self._dims = {}
        self.clearContents()
        self.setRowCount(0)

    @property
    def ndim(self) -> int:
        return len(self._dims)

    @property
    def dims(self) -> dict[int, DimensionItem]:
        return self._dims

    def getShape(self) -> tuple[int, ...]:
        return tuple(dimItem.size for dimItem in self.dims.values())

    def _addDim(self, axis: int, dim: Dimension, decimals: int):
        """

        :param axis: which axis is defining this dimension
        :param `Dimension` dim: definition of the dimension to add
        """
        axis = self._getNextFreeAxis()
        row = self.rowCount()
        self.setRowCount(row + 1)
        widget = DimensionItem(parent=self, table=self, row=row)
        widget.setStartStopDecimals(decimals)
        widget.sigRemoved.connect(self.onRemoveDim)
        widget.sigDimChanged.connect(self.sigUpdateDims)
        widget.fromDimension(axis, dim)
        self._dims[row] = widget
        return widget

    def setDims(self, dims: dict[int, Dimension], decimals: int):
        """

        :param dict dims: axis as key and `Dimension` as value.
        """
        self.clear()
        if not isinstance(dims, dict):
            raise TypeError(f"dims should be a dict. Got {type(dims)}")

        for axis, dim in dims.items():
            assert type(axis) is int
            assert isinstance(dim, Dimension)
            self._addDim(axis, dim, decimals)

        self.sigUpdateDims.emit()

    def onRemoveDim(self, iRow: int):
        """
        Remove dimension.

        :param Union[int,`DimensionItem`]: row or item to remove
        """
        # remove the widget
        self.removeRow(iRow)
        self._dims[iRow].sigRemoved.disconnect(self.onRemoveDim)
        self._dims[iRow].sigDimChanged.disconnect(self.sigUpdateDims)
        self._dims[iRow].setAttribute(qt.Qt.WA_DeleteOnClose)
        self._dims[iRow].close()
        del self._dims[iRow]
        # reorder existing widgets
        ini_rows = sorted(list(self._dims.keys()))
        for row in ini_rows:
            if row <= iRow:
                continue
            widget = self._dims[row]
            new_row = row - 1
            assert new_row >= 0
            widget.embedInTable(table=self, row=new_row)
            widget.axis = self._getNextFreeAxis()
            self._dims[new_row] = widget
            del self._dims[row]
        self.sigUpdateDims.emit()

    def getDim(self, iRow: int):
        """return the instance of DimensionItem for the iRow"""
        return self._dims.get(iRow, None)

    def _getNextFreeAxis(self):
        """
        :return int: next unused axis
        """
        res = 0
        usedAxis = []
        [usedAxis.append(_dim.axis) for _dim in self._dims.values()]
        while res in usedAxis:
            res = res + 1
        return res


class DimensionWidget(qt.QWidget):
    """
    Widget to define dimensions and try to fit those with dataset
    """

    sigUpdateDimensions = qt.Signal()
    """Emitted when user inputs in the dimension table changed."""
    sigFindDimensions = qt.Signal()
    """Emit when user want to find dimensions"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ============ SCAN SETTINGS ============
        zigzagModeLabel = qt.QLabel("Zigzag Mode: ")
        self._isZigzagCB = qt.QCheckBox()
        self._isZigzagCB.setToolTip(
            "Checked if acquisition of scan with bliss is in zig zag mode.\n Fill by 'find dimensions' button."
        )

        # ============ FIND DIMS ============

        toleranceLabel = qt.QLabel("Tolerance = 1e-")
        self._toleranceSB = qt.QSpinBox()
        self._toleranceSB.valueChanged.connect(self.onToleranceChanged)

        self._toleranceSB.setToolTip(
            "Tolerance for which the values in the dimensions will be considered unique"
        )

        self._findDimsButton = qt.QPushButton("Find dimensions")
        self._findDimsButton.setToolTip(
            "Automatically find all dimensions that "
            "change through the dataset. \n"
            "It is considered that a dimension changes "
            "if the number of unique values is greater "
            "than one.\nThe metadata type is needed to "
            "choose which values to compare, and the "
            "threshold to know when two values are "
            "considered to be different.\nThe threshold"
            " is only used in values that are numbers."
        )

        # ============ DIMS TABLE ============

        self._dimensionTable = DimensionTable(self)
        self._dimensionTable.sigUpdateDims.connect(self.sigUpdateDimensions)

        # ============ TIPS LABEL ============

        self._tipsLabel = qt.QLabel(self)

        # ============ LAYOUT EVERYTHING ============

        detection_layout = qt.QHBoxLayout()
        detection_layout.setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignTop
        )
        detection_layout.addWidget(toleranceLabel)
        detection_layout.addWidget(self._toleranceSB)
        detection_layout.addWidget(self._findDimsButton)

        dimensions_definition_group = qt.QGroupBox("Dimensions definition")
        dimensions_definition_group.setLayout(qt.QVBoxLayout())
        dimensions_definition_group.layout().addWidget(self._dimensionTable)
        dimensions_definition_group.layout().addLayout(detection_layout)

        scan_settings_group = qt.QGroupBox("Scan settings")
        scan_settings_group.setLayout(qt.QHBoxLayout())
        scan_settings_group.layout().setAlignment(
            qt.Qt.AlignmentFlag.AlignLeft | qt.Qt.AlignmentFlag.AlignTop
        )
        scan_settings_group.layout().addWidget(zigzagModeLabel)
        scan_settings_group.layout().addWidget(self._isZigzagCB)

        main_layout = qt.QVBoxLayout()
        main_layout.addWidget(scan_settings_group)
        main_layout.addWidget(dimensions_definition_group)
        main_layout.addWidget(self._tipsLabel)

        self.setLayout(main_layout)

        # connect Signal/SLOT
        self._findDimsButton.pressed.connect(self._findDimensions)
        self.setTolerance(DimensionDefinition.DEFAULT_TOLERANCE)

    def getTolerance(self) -> float:
        # From N to 1e-N
        return 10 ** (-self._toleranceSB.value())

    def setTolerance(self, tolerance: float):
        # From 1e-N to N
        self._toleranceSB.setValue(-int(numpy.log10(tolerance)))

    def onToleranceChanged(self, val: int):
        for item in self._dimensionTable.dims.values():
            item.setStartStopDecimals(val)

    def _findDimensions(self):
        """
        Try to find dimensions
        """
        self.sigFindDimensions.emit()

    def setTipsLabelText(self, txt: str):
        self._tipsLabel.setText(txt)

    def setDims(self, dims: dict[int, Dimension]):
        self._dimensionTable.setDims(dims, self._toleranceSB.value())

    @property
    def ndim(self) -> int:
        return self._dimensionTable.ndim

    @property
    def dims(self) -> dict[int, DimensionItem]:
        return self._dimensionTable.dims

    @property
    def isZigzagMode(self):
        return self._isZigzagCB.isChecked()

    def setZigzagMode(self, isZigzag: bool):
        return self._isZigzagCB.setChecked(isZigzag)

    def setEnableInputs(self, enabled: bool):
        """Enable/disable controls"""
        self._isZigzagCB.setEnabled(enabled)
        self._findDimsButton.setEnabled(enabled)
        self._toleranceSB.setEnabled(enabled)
        for dimItem in self._dimensionTable.dims.values():
            dimItem.setEnabledInputs(enabled)


class DimensionItem(qt.QWidget):
    """Widget use to define a dimension"""

    sigRemoved = qt.Signal(int)
    """Signal emitted when the Item should be removed"""

    sigDimChanged = qt.Signal()
    """Signal emitted when dim changed"""

    def __init__(self, parent, table, row):
        """

        :param QTableWidget table: if has to be embed in a table the
                                           parent table
        :param int row: row position in the QTableWidget. Also used as ID
        """
        qt.QWidget.__init__(self, parent)

        # axis
        self._axisLabel = qt.QLabel(parent=self)
        self._axisLabel.setAlignment(
            qt.QtCore.Qt.AlignCenter | qt.QtCore.Qt.AlignHCenter
        )
        # name
        self._nameLabel = qt.QLabel(parent=self)
        self._nameLabel.setAlignment(
            qt.QtCore.Qt.AlignCenter | qt.QtCore.Qt.AlignHCenter
        )
        # size
        self._sizeWidget = qt.QSpinBox(self)
        self._sizeWidget.setMinimum(0)
        self._sizeWidget.setMaximum(9999)
        self._sizeWidget.valueChanged.connect(self.sigDimChanged)
        # start
        self._startWidget = qt.QDoubleSpinBox(self)
        self._startWidget.setMinimum(float("-inf"))
        self._startWidget.setDecimals(5)
        self._startWidget.valueChanged.connect(self.sigDimChanged)
        # end
        self._stopWidget = qt.QDoubleSpinBox(self)
        self._stopWidget.setMinimum(float("-inf"))
        self._stopWidget.setDecimals(5)
        self._stopWidget.valueChanged.connect(self.sigDimChanged)
        # rm button
        style = qt.QApplication.style()
        icon = style.standardIcon(qt.QStyle.SP_BrowserStop)
        self._rmButton = qt.QPushButton(icon=icon, parent=self)

        # connect Signal/slot
        self._rmButton.pressed.connect(self.remove)

        self.embedInTable(table=table, row=row)
        self.__row = row

    def setEnabledInputs(self, enabled: bool):
        self._sizeWidget.setEnabled(enabled)
        self._startWidget.setEnabled(enabled)
        self._stopWidget.setEnabled(enabled)
        self._rmButton.setEnabled(enabled)

    def remove(self):
        self.sigRemoved.emit(self._row)

    def setStartStopDecimals(self, decimals: int):
        self._startWidget.setDecimals(decimals)
        self._stopWidget.setDecimals(decimals)

    @property
    def _row(self):
        return self.__row

    @property
    def axis(self):
        return int(self._axisLabel.text())

    @axis.setter
    def axis(self, axis: int):
        self._axisLabel.setText(str(axis))

    @property
    def size(self):
        return self._sizeWidget.value()

    @property
    def start(self):
        return self._startWidget.value()

    @property
    def stop(self):
        return self._stopWidget.value()

    @property
    def name(self):
        return self._nameLabel.text()

    def toDimension(self) -> Dimension:
        return Dimension(self.name, self.size, self.start, self.stop)

    def fromDimension(self, axis: int, dim: Dimension):
        self.axis = axis
        self._nameLabel.setText(dim.name)
        self._sizeWidget.setValue(dim.size)
        self._startWidget.setValue(dim.start)
        self._stopWidget.setValue(dim.stop)

    def embedInTable(self, table, row):
        self.__row = row
        for column, widget in enumerate(
            (
                self._axisLabel,
                self._nameLabel,
                self._sizeWidget,
                self._startWidget,
                self._stopWidget,
                self._rmButton,
            )
        ):
            table.setCellWidget(row, column, widget)
