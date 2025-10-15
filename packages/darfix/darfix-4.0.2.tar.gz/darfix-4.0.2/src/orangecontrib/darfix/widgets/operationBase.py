from __future__ import annotations

import copy
import logging

from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread
from silx.gui import qt

from darfix.core.utils import OperationAborted
from darfix.gui.utils.standardButtonBox import StandardButtonBox

_logger = logging.getLogger(__name__)


class OperationWidgetBase(OWEwoksWidgetOneThread, openclass=True):

    def __init__(
        self,
        buttonTypes: qt.QDialogButtonBox.StandardButton = qt.QDialogButtonBox.StandardButton.NoButton,
    ):
        super().__init__()

        self.__inputDataset = None

        # buttons
        self.__buttons = StandardButtonBox(parent=self, additionalButtons=buttonTypes)

        self.__buttons.okButton.clicked.connect(self.onOkClicked)
        self.__buttons.resetButton.clicked.connect(self.onResetClicked)
        self.__buttons.abortButton.clicked.connect(self.onAbortClicked)
        self.__buttons.okButton.setEnabled(False)

        self.task_executor.finished.connect(self.__onFinishTask)

        self.__widget = self.createMainWidget(self.get_default_input_values())
        self.mainArea.layout().addWidget(self.__widget)
        self.mainArea.layout().addWidget(self.__buttons)

    @property
    def buttons(self) -> StandardButtonBox:
        return self.__buttons

    @property
    def mainWidget(self) -> qt.QWidget:
        return self.__widget

    def saveMainWidget(self) -> None:
        """
        inherited class need to override this method.

        Save parameters as default inputs with `set_default_input` here.
        """
        raise NotImplementedError("This is an abstract method.")

    def createMainWidget(self, default_inputs: dict) -> qt.QWidget:
        """
        inherited class need to override this method.

        Instantiate and setup main widget here.

        :param default_inputs: Dictionary containing the default inputs that are set.
        :return : An instance of the created main widget
        """
        raise NotImplementedError("This is an abstract method.")

    def onOkClicked(self) -> None:
        if len(self.get_task_outputs()) == 0:
            # if no output at all this is an unexpected behaviour
            raise RuntimeError("Cannot go to next step because outputs are empty.")
        self.close()
        self.propagate_downstream()

    def onResetClicked(self):
        self.reset()

    def onAbortClicked(self):
        self.cancel_running_task()

    def __onFinishTask(self):
        self.mainWidget.setEnabled(True)
        self.buttons.setIsComputing(False)

    def handleNewSignals(self) -> None:
        # Do not call super().handleNewSignals() to prevent propagation
        self.__inputDataset = self.get_task_input_value("dataset")
        self.set_dynamic_input("dataset", copy.deepcopy(self.__inputDataset))

    def reset(self):
        self.__buttons.okButton.setEnabled(False)
        self.set_dynamic_input("dataset", self.__inputDataset)
        # Re trigger handleNewSignals to reset dataset input
        self.handleNewSignals()

    def task_output_changed(self) -> None:
        if self.task_succeeded:
            self.__buttons.okButton.setEnabled(True)

    def isAborted(self) -> bool:
        return isinstance(self.task_exception, OperationAborted)

    def closeEvent(self, evt) -> None:
        super().closeEvent(evt)
        self.saveMainWidget()

    def execute_ewoks_task_without_propagation(self):
        self.buttons.setIsComputing(True)
        self.mainWidget.setDisabled(True)
        super().execute_ewoks_task_without_propagation()
