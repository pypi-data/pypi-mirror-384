from __future__ import annotations

from ewokscore.missing_data import MISSING_DATA
from ewokscore.missing_data import is_missing_data
from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread
from ewoksorange.gui.parameterform import block_signals

from darfix import dtypes
from darfix.gui.binningWidget import BinningWidget
from darfix.tasks.binning import Binning


class BinningWidgetOW(OWEwoksWidgetOneThread, ewokstaskclass=Binning):
    """
    Widget that computes dataset binning
    """

    name = "binning"
    icon = "icons/resize.png"
    want_main_area = True

    _ewoks_inputs_to_hide_from_orange = ("scale", "output_dir")

    def __init__(self):
        super().__init__()

        self._widget = BinningWidget(parent=self)
        self.mainArea.layout().addWidget(self._widget)

        # connect signal / slot
        self._widget.sigScaleChanged.connect(self._scaleChanged)
        self._widget.sigApply.connect(self._apply)
        self._widget.sigAbort.connect(self.cancel_running_task)
        self._widget.sigComputed.connect(self.propagate_downstream)

        # set up
        scale = self.get_default_input_value("scale", MISSING_DATA)
        if scale not in (None, MISSING_DATA):
            with block_signals(self._widget):
                self._widget.scale = scale
        else:
            self._scaleChanged(self._widget.scale)

    def _scaleChanged(self, scale: float):
        self.set_default_input("scale", scale)

    def setDataset(
        self,
        dataset: dtypes.Dataset | None,
        pop_up=False,
    ):
        if dataset is None or is_missing_data(dataset):
            return

        if not isinstance(dataset, dtypes.Dataset):
            raise dtypes.DatasetTypeError(dataset)

        self._widget.setDataset(dataset)

        if pop_up:
            # raise the QDialog
            self.open()

    def handleNewSignals(self) -> None:
        """Invoked by the workflow signal propagation manager after all
        signals handlers have been called.

        note: this widget can receive one signal: 'dataset'. The 'dataset' signal is handled by the ewoks task.
              This function will be only triggered when the 'dataset' signal is send
        """
        # update GUI from received dataset
        dataset = self.get_task_input_value("dataset")
        self.setDataset(dataset=dataset, pop_up=True)
        # avoid computing and propagation: waiting for apply to be pressed for now
        # super().handleNewSignals()

    def task_output_changed(self):
        # once the output is computed we can update the GUI (calling widget._displayComponents)
        dataset = self.get_task_output_value("dataset")
        self._widget._endComputation()
        if dataset not in (None, MISSING_DATA):
            self._widget.updateResultDataset(dataset.dataset)
        super().task_output_changed()

    def _apply(self):
        # in this case we only want to have the output of the task and avoid propagating until user press 'ok'
        self.execute_ewoks_task_without_propagation()
