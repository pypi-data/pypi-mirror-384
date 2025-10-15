from __future__ import annotations

from typing import Any
from typing import Dict

from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread
from ewoksorange.gui.parameterform import block_signals
from silx.gui import qt

from darfix import dtypes
from darfix.gui.magnificationWidget import MagnificationWidget
from darfix.gui.rsmWidget import RSMWidget
from darfix.tasks.transformation import TransformationMatrixComputation


class TransformationWidgetOW(
    OWEwoksWidgetOneThread, ewokstaskclass=TransformationMatrixComputation
):
    """
    Widget to computes transformation matrix.
    """

    name = "transformation"
    icon = "icons/axes.png"
    want_main_area = False

    _ewoks_inputs_to_hide_from_orange = (
        "kind",
        "orientation",
        "magnification",
        "pixelSize",
        "rotate",
    )

    def __init__(self):
        super().__init__()
        self._magWidget = MagnificationWidget(self)
        magnification = self.get_default_input_value("magnification", None)
        if magnification:
            self._magWidget.magnification = magnification
        orientation = self.get_default_input_value("orientation", None)
        if orientation:
            self._magWidget.orientation = orientation

        self._rsmWidget = RSMWidget(self)
        pixelSize = self.get_default_input_value("pixelSize", None)
        if pixelSize:
            self._rsmWidget.pixelSize = pixelSize
        rotate = self.get_default_input_value("rotate", None)
        if rotate:
            self._rsmWidget.rotate = rotate
        self._stackedWidget = qt.QStackedWidget(self)
        self._stackedWidget.addWidget(self._magWidget)
        self._stackedWidget.addWidget(self._rsmWidget)

        self._methodCB = qt.QComboBox(self)
        self._methodCB.currentTextChanged.connect(self._changeTransformationWidget)

        self._okButton = qt.QPushButton(self, text="Ok")
        self._okButton.clicked.connect(self._execute_task)
        self._okButton.setEnabled(False)

        layout = self._get_control_layout()
        layout.addWidget(self._methodCB)
        layout.addWidget(self._stackedWidget)
        layout.addWidget(self._okButton)

    def handleNewSignals(self):
        dataset = self.get_task_input_value("dataset", None)
        if dataset is not None:
            self.setDataset(dataset)

        # Do not call super().handleNewSignals() to prevent propagation

    def setDataset(self, _input: dtypes.Dataset):
        if not isinstance(_input, dtypes.Dataset):
            raise TypeError(
                f"_input is expected to be an instance of {dtypes.Dataset}. Got {type(_input)}."
            )

        darfix_dataset = _input.dataset

        ndim = darfix_dataset.dims.ndim
        if ndim == 0:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setText(
                "This widget has to be used before selecting any region of \
                            interest and after selecting the dimensions"
            )
            msg.exec()
            return

        self._dataset = _input
        self._changeDimensions(ndim)
        self._okButton.setEnabled(True)

    def _changeDimensions(self, ndim: int) -> None:
        """The possible transformations depend on the number of dimensions (one or two)."""
        if ndim == 1:
            transformations = ["Magnification", "RSM"]
        elif ndim == 2:
            transformations = ["Magnification"]
        else:
            raise ValueError(
                f"The Transformation Widget only works with 1D or 2D datasets. Not {ndim}D."
            )

        current_items = [
            self._methodCB.itemText(i) for i in range(self._methodCB.count())
        ]
        if transformations == current_items:
            return

        with block_signals(self._methodCB):
            old_method = self._methodCB.currentText()
            self._methodCB.clear()
            self._methodCB.addItems(transformations)
            try:
                idx = transformations.index(old_method)
            except ValueError:
                idx = 0
            self._methodCB.setCurrentIndex(idx)

    def _changeTransformationWidget(self, method: str) -> None:
        """
        Change the widget displayed on the window
        """

        if method == "RSM":
            self._stackedWidget.setCurrentWidget(self._rsmWidget)
        elif method == "Magnification":
            self._stackedWidget.setCurrentWidget(self._magWidget)
        else:
            return

    def _execute_task(self) -> None:
        method = self._methodCB.currentText()

        args: Dict[str, Any] = {"dataset": self._dataset}
        if method == "Magnification":
            args["magnification"] = self._magWidget.magnification
            args["kind"] = "magnification"
            args["orientation"] = self._magWidget.orientation
        elif method == "RSM":
            args["pixelSize"] = self._rsmWidget.pixelSize
            args["rotate"] = self._rsmWidget.rotate
            args["kind"] = "rsm"
        self.close()

        for name, value in args.items():
            self.set_default_input(name, value)

        self.execute_ewoks_task()
