from __future__ import annotations

from silx.gui import qt

from ...core.noiseremoval import NoiseRemovalOperation
from ...core.noiseremoval import operation_to_str


class OperationHistoryWidget(qt.QWidget):
    """Keeps the history of noise removal operations and displays them in a QListWidget"""

    def __init__(self, parent: qt.QWidget | None = None) -> None:
        super().__init__(parent)

        layout = qt.QVBoxLayout()
        assert layout is not None
        self._listWidget = qt.QListWidget()
        self._listWidget.setSelectionMode(
            qt.QAbstractItemView.SelectionMode.NoSelection
        )
        self._listWidget.hide()
        self._checkbox = qt.QCheckBox("Show history")

        layout.addWidget(self._checkbox)
        layout.addWidget(self._listWidget)
        self.setLayout(layout)

        self._checkbox.toggled.connect(self._listWidget.setVisible)
        self._checkbox.setChecked(True)

        self._operations: list[NoiseRemovalOperation] = []

    def append(self, operation: NoiseRemovalOperation):
        self._operations.append(operation)
        operation_order = len(self._operations)
        self._listWidget.addItem(
            qt.QListWidgetItem(f"{operation_order}: {str(operation)}")
        )

    def pop(self):
        self._operations.pop()
        self._listWidget.takeItem(self._listWidget.count() - 1)

    def clear(self):
        self._operations.clear()
        self._listWidget.clear()

    def getOperations(self) -> list[NoiseRemovalOperation]:
        return list(self._operations)

    def extend(self, operations: list[NoiseRemovalOperation]):
        existing_count = len(self._operations)
        self._operations.extend(operations)
        for i_new_op, operation in enumerate(operations):
            self._listWidget.addItem(
                qt.QListWidgetItem(
                    f"{existing_count + i_new_op}: {operation_to_str(operation)}"
                )
            )
