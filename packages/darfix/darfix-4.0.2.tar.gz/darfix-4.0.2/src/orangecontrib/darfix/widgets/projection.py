from __future__ import annotations

from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread

from darfix.dtypes import Dataset
from darfix.gui.projectionWidget import ProjectionWidget
from darfix.tasks.projection import Projection


class ProjectionWidgetOW(OWEwoksWidgetOneThread, ewokstaskclass=Projection):
    """
    Removes one dimension by projecting (summing) all images in this dimension.

    Details in https://gitlab.esrf.fr/XRD/darfix/-/issues/37
    """

    name = "projection"
    # icon = "icons/projection.png"
    want_main_area = False

    _ewoks_inputs_to_hide_from_orange = ("dimension",)

    def __init__(self):
        super().__init__()

        self._widget = ProjectionWidget(parent=self)
        self._widget.sigProjectButtonClicked.connect(
            self.execute_ewoks_task_without_propagation
        )
        self._widget.sigDimensionsChanged.connect(self._update_dimension)
        self._widget.sigOkClicked.connect(self._accept_result)
        self._get_control_layout().addWidget(self._widget)

        dataset: Dataset = self.get_default_input_value("dataset", None)
        if dataset is not None:
            self._widget.setDataset(dataset.dataset)
        # TODO: Deal with dimension default input??

    def _update_dimension(self):
        self.set_default_input("dimension", self._widget.getDimension())

    def _accept_result(self):
        self.propagate_downstream()
        self.close()

    def handleNewSignals(self) -> None:
        dataset: Dataset = self.get_task_input_value("dataset", None)
        if dataset is None:
            return
        self._widget.setDataset(dataset.dataset)
        self.open()

        # Do not call super().handleNewSignals() to prevent propagation

    def task_output_changed(self):
        send_dataset = self.get_task_output_value("dataset", None)
        if send_dataset is None:
            return
        assert isinstance(send_dataset, Dataset)
        self._widget.updatePlot(send_dataset.dataset)
