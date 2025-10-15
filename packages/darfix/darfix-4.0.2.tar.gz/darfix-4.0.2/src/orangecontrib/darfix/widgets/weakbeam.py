import logging
from typing import Optional

from ewokscore.missing_data import MISSING_DATA
from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread
from ewoksorange.gui.parameterform import block_signals

from darfix import dtypes
from darfix.gui.operationThread import OperationThread
from darfix.gui.utils.message import missing_dataset_msg
from darfix.gui.weakBeamWidget import WeakBeamWidget
from darfix.tasks.weakbeam import WeakBeam

_logger = logging.getLogger(__name__)


class WeakBeamWidgetOW(
    OWEwoksWidgetOneThread,
    ewokstaskclass=WeakBeam,
):
    """
    Widget that computes dataset with filtered weak beam and recover its Center of Mass.
    """

    name = "weak beam"
    icon = "icons/gaussian.png"
    want_main_area = True
    want_control_area = False

    _ewoks_inputs_to_hide_from_orange = ("nvalue", "indices", "title")

    def __init__(self):
        super().__init__()
        self._thread = None

        self._widget = WeakBeamWidget(parent=self)
        self.mainArea.layout().addWidget(self._widget)
        nvalue = self.get_default_input_value("nvalue", MISSING_DATA)
        if nvalue is not MISSING_DATA:
            with block_signals(self._widget):
                self._widget.nvalue = nvalue
        else:
            self.set_default_input("nvalue", self._widget.nvalue)

        # connect signal / slot
        self._widget.sigValidate.connect(self.execute_ewoks_task)
        self._widget.sigApplyThreshold.connect(self._launch_recover_weak_beam)
        self._widget.sigNValueChanged.connect(self._nValueChanged)

    def setDataset(self, dataset: Optional[dtypes.Dataset], pop_up: bool = False):
        if dataset is None:
            return
        if pop_up:
            self.open()
        self.set_dynamic_input("dataset", dataset=dataset)
        # if some processing on-going with the previous dataset stop it.
        self._stop_thread()

    def _nValueChanged(self):
        self.set_default_input("nvalue", self._widget.nvalue)

    def handleNewSignals(self) -> None:
        dataset = self.get_task_input_value("dataset", None)
        if dataset is None:
            return

        self.setDataset(dataset=dataset, pop_up=True)

        if isinstance(dataset, dtypes.Dataset):
            self.set_dynamic_input("indices", dataset.indices)
            title = dataset.dataset.title
            self.set_default_input(
                "title",
                title if title is not None else MISSING_DATA,
            )

        # warning: do not call to make sure the processing is not triggered
        # return super().handleNewSignals()

    def task_output_changed(self) -> None:
        dataset = self.get_task_output_value("dataset", MISSING_DATA)
        self.setDataset(dataset)

    def _launch_recover_weak_beam(self):
        """callback when the user modify the 'nvalue'"""
        if self._thread is not None:
            _logger.warning("recover weak beam already on going")

        dataset = self.get_task_input_value("dataset", None)
        if dataset is None:
            missing_dataset_msg()
            return
        if not isinstance(dataset, dtypes.Dataset):
            raise dtypes.DatasetTypeError(dataset)

        self._widget.setProcessingButtonsEnabled(False)
        nvalue = self.get_task_input_value("nvalue", MISSING_DATA)
        # FIXME: all processing should be in done in a ewoks task. See https://gitlab.esrf.fr/XRD/darfix/-/issues/130
        self._thread = OperationThread(self, dataset.dataset.recover_weak_beam)
        self._thread.setArgs(
            n=nvalue,
            indices=dataset.indices,
        )
        self._thread.finished.connect(self._recover_weak_beam_finished)
        self._thread.start()

    def _stop_thread(self):
        if self._thread is not None:
            self._thread.finished.disconnect(self._recover_weak_beam_finished)
        self._thread = None
        self._widget.setProcessingButtonsEnabled(True)

    def _recover_weak_beam_finished(self):
        sender = self.sender()
        dataset = self._thread.data
        self._stop_thread()

        if dataset in (None, MISSING_DATA):
            return
        assert isinstance(
            dataset, dtypes.ImageDataset
        ), f"dataset is expected to be an instance of {dtypes.ImageDataset}. Get {type(dataset)}"
        self._widget.setResult(
            center_of_mass=dataset.apply_moments(indices=sender.kwargs["indices"])[0][
                0
            ],
            transformation=dataset.transformation,
        )
        self._stop_thread()
