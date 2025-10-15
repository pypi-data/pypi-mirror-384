from __future__ import annotations

import numpy
from silx.gui import qt

from darfix import dtypes
from darfix.gui.shiftcorrection.shiftCorrectionWidget import ShiftCorrectionWidget
from darfix.tasks.shiftcorrection import ShiftCorrection
from orangecontrib.darfix.widgets.operationBase import OperationWidgetBase


class ShiftCorrectionWidgetOW(OperationWidgetBase, ewokstaskclass=ShiftCorrection):
    """
    Widget to make the shift correction of a dataset.
    """

    name = "shift correction"
    description = "A widget to perform shift correction"
    icon = "icons/shift_correction.svg"
    want_main_area = True
    want_control_area = False

    _ewoks_inputs_to_hide_from_orange = ("shift", "selected_axis", "selected_index")

    def __init__(self):
        super().__init__()
        qt.QLocale.setDefault(qt.QLocale("en_US"))

    def createMainWidget(self, default_inputs: dict) -> ShiftCorrectionWidget:
        widget = ShiftCorrectionWidget()
        widget.correctSignal.connect(self.execute_shift_correction)
        widget.setCorrectionInputs(
            default_inputs.get("shift", (0, 0)),
            default_inputs.get("selected_axis", None),
        )
        return widget

    def saveMainWidget(self) -> dict:
        inputs = self.mainWidget.getCorrectionInputs()
        for key, value in inputs.items():
            if isinstance(value, numpy.ndarray):
                value = value.tolist()
            self.set_default_input(key, value)

    @property
    def mainWidget(self) -> ShiftCorrectionWidget:
        return super().mainWidget

    def handleNewSignals(self) -> None:
        super().handleNewSignals()
        dataset = self.get_task_input_value("dataset", None)
        if dataset is not None:
            self.setDataset(dataset, pop_up=True)

    def setDataset(self, dataset: dtypes.Dataset, pop_up=True):
        self.mainWidget.setDataset(dataset)
        if pop_up:
            self.open()

    def execute_shift_correction(self):
        self.saveMainWidget()
        self.execute_ewoks_task_without_propagation()

    def task_output_changed(self) -> None:
        super().task_output_changed()
        self.mainWidget.refreshPlot()
