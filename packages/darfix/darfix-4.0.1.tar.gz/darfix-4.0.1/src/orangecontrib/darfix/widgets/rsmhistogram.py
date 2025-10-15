from __future__ import annotations

import numpy
from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread

from darfix.dtypes import Dataset
from darfix.gui.rsmHistogramWidget import RSMHistogramWidget
from darfix.tasks.rsm_histogram import RSMHistogram


class RSMHistogramWidgetOW(OWEwoksWidgetOneThread, ewokstaskclass=RSMHistogram):
    """
    Widget to compute Reciprocal Space Map
    """

    name = "rsm histogram"
    icon = "icons/category.svg"
    want_main_area = False

    _ewoks_inputs_to_hide_from_orange = (
        "Q",
        "a",
        "map_range",
        "detector",
        "units",
        "n",
        "map_shape",
        "energy",
    )

    def __init__(self):
        super().__init__()

        self._widget = RSMHistogramWidget(parent=self)
        self._widget.sigComputeClicked.connect(self._compute)
        self.controlArea.layout().addWidget(self._widget)
        q = self.get_default_input_value("Q")
        if q:
            self._widget.q = q
        a = self.get_default_input_value("a")
        if a:
            self._widget.a = a
        map_range = self.get_default_input_value("map_range")
        if map_range:
            self._widget.map_range = map_range
        detector = self.get_default_input_value("detector")
        if detector:
            self._widget.detector = detector
        units = self.get_default_input_value("units")
        if units:
            self._widget.units = units
        n = self.get_default_input_value("n")
        if n:
            self._widget.n = n
        map_shape = self.get_default_input_value("map_shape")
        if map_shape:
            self._widget.map_shape = map_shape
        energy = self.get_default_input_value("energy")
        if energy:
            self._widget.energy = energy

    def handleNewSignals(self):
        dataset: Dataset | None = self.get_task_input_value("dataset", None)
        if dataset is None:
            return
        self.setDataset(dataset)

        # Do not call super().handleNewSignals() to prevent propagation

    def setDataset(self, dataset: Dataset):
        self._widget.setDataset(dataset)
        self.open()

    def _compute(self):
        self.set_dynamic_input("dataset", self._widget.dataset)
        self.set_default_input("Q", self._widget.q.tolist())
        self.set_default_input("a", self._widget.a)
        self.set_default_input("map_range", self._widget.map_range)
        self.set_default_input("detector", self._widget.detector)
        self.set_default_input("units", self._widget.units)
        self.set_default_input("n", self._widget.n.tolist())
        self.set_default_input("map_shape", self._widget.map_shape.tolist())
        self.set_default_input("energy", self._widget.energy)

        self.execute_ewoks_task_without_propagation()

    def task_output_changed(self) -> None:
        arr: numpy.ndarray | None = self.get_task_output_value("hist_values", None)
        edges: numpy.ndarray | None = self.get_task_output_value("hist_edges", None)

        if arr is None or edges is None:
            return
        self._widget.updatePlot(arr, edges)
