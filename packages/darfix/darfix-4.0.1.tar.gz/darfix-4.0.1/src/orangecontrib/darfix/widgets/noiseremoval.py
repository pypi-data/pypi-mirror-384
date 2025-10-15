from __future__ import annotations

from ewokscore.missing_data import is_missing_data
from silx.gui import qt

from darfix import dtypes
from darfix.core.noiseremoval import NoiseRemovalOperation
from darfix.gui.noiseremoval.noiseRemovalWidget import NoiseRemovalWidget
from darfix.tasks.noiseremoval import NoiseRemoval
from orangecontrib.darfix.widgets.operationBase import OperationWidgetBase


class NoiseRemovalWidgetOW(OperationWidgetBase, ewokstaskclass=NoiseRemoval):
    name = "noise removal"
    description = "A widget to perform various noise removal operations"
    icon = "icons/noise_removal.png"
    want_main_area = True
    want_control_area = False

    _ewoks_inputs_to_hide_from_orange = ("operations",)

    def __init__(self):
        super().__init__()

    def createMainWidget(self, inputs: dict) -> NoiseRemovalWidget:
        widget = NoiseRemovalWidget()
        widget.sigLaunchOperation.connect(self._execute_noise_removal_operation)
        incomingOperations = inputs.get("operations", [])
        widget.setIncomingOperations(incomingOperations)
        widget.setDefaultParameters(incomingOperations)
        return widget

    def saveMainWidget(self):
        self.set_default_input(
            "operations",
            list(
                filter(
                    lambda op: not op.get("aborted", False),
                    self.mainWidget.getOperationHistory(),
                )
            ),
        )

    @property
    def mainWidget(self) -> NoiseRemovalWidget:
        return super().mainWidget

    def handleNewSignals(self) -> None:
        super().handleNewSignals()
        dataset = self.get_task_input_value("dataset")
        self.setDataset(dataset, pop_up=True)

    def setDataset(self, dataset: dtypes.Dataset | None, pop_up=True):
        if dataset is None:
            return
        self.mainWidget.setDataset(dataset)

        if self.mainWidget.hasIncomingOperations() and not is_missing_data(
            self.get_task_input_value("dataset")
        ):
            messagebox = qt.QMessageBox(
                qt.QMessageBox.Icon.Question,
                "Replay Operations ?",
                "Do you want to apply the following operations from last save now ?\n IF NOT, the history of operations will be cleared.\n\n"
                + "\n\n".join(
                    [
                        f"{i} - {str(ope)}"
                        for i, ope in enumerate(self.mainWidget.getIncomingOperations())
                    ]
                ),
                buttons=qt.QMessageBox.StandardButton.Yes
                | qt.QMessageBox.StandardButton.No,
            )
            ret = messagebox.exec()
            if ret == qt.QMessageBox.StandardButton.Yes:
                self.execute_ewoks_task_without_propagation()

        if pop_up:
            self.open()

    def _execute_noise_removal_operation(
        self, operation: NoiseRemovalOperation
    ) -> None:
        incomingOperations = [operation]
        self.mainWidget.setIncomingOperations(incomingOperations)
        self.set_dynamic_input("operations", incomingOperations)

        self.execute_ewoks_task_without_propagation()

    def task_output_changed(self):
        if self.isAborted() and self.replayAfterAbort():
            return
        if self.isAborted():
            self.mainWidget.abortIncomingOperations()
        else:
            self.mainWidget.extendOperationHistory()

        super().task_output_changed()
        self.mainWidget.refreshPlot()

    def replayAfterAbort(self) -> bool:
        """Create a messagebox to ask user if he wants to replay after abort. Return True if Yes."""
        messagebox = qt.QMessageBox(
            qt.QMessageBox.Icon.Question,
            "Operation aborted !",
            "Operation(s) was not applied to the whole stack.\n"
            "Do you want to replay all previous operations to recover last state ?\n"
            "If not, the stack will stay in a partially modified state. You can still reset dataset if you want to restart the noise removal process.\n",
            buttons=qt.QMessageBox.StandardButton.Yes
            | qt.QMessageBox.StandardButton.No,
        )

        replay = messagebox.exec() == qt.QMessageBox.StandardButton.Yes

        if replay:
            ops = self.mainWidget.getOperationHistory()
            self.reset()
            self.mainWidget.setIncomingOperations(ops, clear=True)
            self.set_dynamic_input("operations", ops)
            self.execute_ewoks_task_without_propagation()

        return replay
