from __future__ import annotations

from ewokscore.missing_data import MISSING_DATA
from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread

from darfix.gui.zSumWidget import ZSumWidget
from darfix.tasks.zsum import ZSum


class ZSumWidgetOW(OWEwoksWidgetOneThread, ewokstaskclass=ZSum):
    """
    Widget that compute and display the Z-sum of a dataset
    """

    name = "z sum"
    icon = "icons/zsum.svg"
    want_main_area = True
    want_control_area = False

    _ewoks_inputs_to_hide_from_orange = ("indices", "selected_axis")

    def __init__(self):
        super().__init__()

        self._widget = ZSumWidget(parent=self)
        self.mainArea.layout().addWidget(self._widget)
        # connect signal / slot
        self._widget.sigAxisChanged.connect(self._onAxisChanged)
        self._widget.sigResetFiltering.connect(self._onUncheckFiltering)

    def handleNewSignals(self) -> None:
        dataset = self.get_task_input_value("dataset", None)
        if dataset is None:
            return super().handleNewSignals()

        self._widget.setDataset(dataset)
        self.set_dynamic_input("selected_axis", None)
        self.open()
        return super().handleNewSignals()

    def task_output_changed(self):
        self._widget.setEnabled(True)
        z_sum = self.get_task_output_value("zsum", MISSING_DATA)
        if z_sum is not MISSING_DATA:
            self._widget.setZSum(z_sum)

    def _onAxisChanged(self, selectedAxis: int):
        self.set_default_input("indices", self._widget.indices)
        self.set_dynamic_input("selected_axis", selectedAxis)
        self.execute_ewoks_task_without_propagation()
        self._widget.setDisabled(True)

    def _onUncheckFiltering(self):
        self.set_default_input("indices", None)
        self.set_dynamic_input("selected_axis", None)
        self.execute_ewoks_task_without_propagation()
        self._widget.setDisabled(True)
