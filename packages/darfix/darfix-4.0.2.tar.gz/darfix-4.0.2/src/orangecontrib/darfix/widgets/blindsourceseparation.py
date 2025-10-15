from typing import Optional

from ewokscore.missing_data import MISSING_DATA
from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread
from ewoksorange.gui.orange_imports import Output
from ewoksorange.gui.orange_imports import Setting

from darfix import dtypes
from darfix.gui.blindSourceSeparationWidget import BSSWidget
from darfix.tasks.blindsourceseparation import BlindSourceSeparation
from darfix.tasks.blindsourceseparation import Method


class BlindSourceSeparationWidgetOW(
    OWEwoksWidgetOneThread, ewokstaskclass=BlindSourceSeparation
):
    """
    Widget to apply blind source separation (BSS) to find grains along the dataset.
    Several techniques can be used like NMF, NNICA, and NMF+NNICA.
    """

    name = "blind source separation"
    icon = "icons/bss.png"
    want_main_area = False

    _ewoks_inputs_to_hide_from_orange = ("method", "n_comp", "processing_order", "save")
    _ewoks_outputs_to_hide_from_orange = ("W", "comp")

    # Settings
    method = Setting(BSSWidget.DEFAULT_METHOD, schema_only=True)
    n_comp = Setting(BSSWidget.DEFAULT_N_COMP, schema_only=True)

    # Outputs
    class Outputs:
        dataset = Output("dataset", dtypes.Dataset)
        comp = Output("comp", object)
        W = Output("W", object)

    def __init__(self):
        super().__init__()
        # backward compatibility
        # if a previous workflow or settings cache contains invalid values, clean them
        self._widget = BSSWidget(parent=self)
        self._widget.sigComputed.connect(self._updateSettings)
        self.controlArea.layout().addWidget(self._widget)

        # set up the gui
        self._widget.setMethod(self.method)
        self._widget.setNComp(self.n_comp)
        # safer: in the case of having invalid settings store updating then will make sure
        # they get valid values
        self._updateSettings(
            method=self._widget.getMethod(),
            n_comp=self._widget.getNComp(),
        )

        # connect signal / slot
        self._widget.computeButton.released.connect(self.execute_ewoks_task)
        self._widget.sigNbComponentsChanged.connect(self._nbComponentChanged)
        self._widget.sigMethodChanged.connect(self._methodChanged)

    def _updateSettings(self, method, n_comp):
        self._nbComponentChanged(n_comp)
        self._methodChanged(method=method)

    def setDataset(self, dataset: Optional[dtypes.Dataset], pop_up=False):
        if dataset in (None, MISSING_DATA):
            return

        if not isinstance(dataset, dtypes.Dataset):
            raise TypeError(
                f"dataset is expected to be an instance of Dataset. Get {type(dataset)}"
            )
        self._widget.setDataset(dataset)

        if pop_up:
            self.open()

    def _updateDataset(self, widget, dataset):
        self._widget._updateDataset(widget, dataset)

    def _nbComponentChanged(self, nb_components: int):
        self.n_comp = nb_components

    def _methodChanged(self, method: str):
        self.method = Method.from_value(method)

    def handleNewSignals(self) -> None:
        """Invoked by the workflow signal propagation manager after all
        signals handlers have been called.

        note: this widget can receive one signal: 'dataset'. The 'dataset' signal is handled by the ewoks task.
              This function will be only triggered when the 'dataset' signal is send
        """
        # update GUI from received dataset
        dataset = self.get_task_input_value("dataset")
        self.setDataset(dataset=dataset, pop_up=True)

        super().handleNewSignals()

    def get_task_inputs(self):
        task_inputs = super().get_task_inputs()

        task_inputs.update(
            {
                "method": self.method,
                "n_comp": self.n_comp,
            }
        )
        return task_inputs

    def task_output_changed(self):
        # once the output is computed we can update the GUI (calling widget._displayComponents)
        comp = self.get_task_output_value("comp", MISSING_DATA)
        W = self.get_task_output_value("W", MISSING_DATA)
        dataset = self.get_task_output_value("dataset", MISSING_DATA)
        if (
            comp is not MISSING_DATA
            and W is not MISSING_DATA
            and dataset is not MISSING_DATA
        ):
            if not isinstance(dataset, dtypes.Dataset):
                raise dtypes.DatasetTypeError(dataset)
            self._widget._displayComponents(
                dataset=dataset.dataset,
                indices=dataset.indices,
                bg_indices=dataset.bg_indices,
                comp=comp,
                W=W,
            )
        super().task_output_changed()
