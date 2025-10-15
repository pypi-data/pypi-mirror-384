from __future__ import annotations

from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread

from darfix import dtypes
from darfix.gui.metadataWidget import MetadataWidget
from darfix.tasks.metadata import MetadataTask


class MetadataWidgetOW(OWEwoksWidgetOneThread, ewokstaskclass=MetadataTask):
    """Widget used to show the metadata in a table."""

    name = "metadata"
    icon = "icons/metadata.svg"
    want_control_area = False
    want_main_area = True

    def __init__(self):
        super().__init__()

        self._widget = MetadataWidget()
        self.mainArea.layout().addWidget(self._widget)

    def setDataset(self, dataset: dtypes.Dataset | None):
        if dataset is None:
            self._widget.clearTable()
        else:
            self._widget.setDataset(dataset)

    def handleNewSignals(self) -> None:
        dataset = self.get_task_input_value("dataset", None)
        if dataset is None:
            return
        self.setDataset(dataset)
        # This is a task only displaying metadata. there is no real processing.
