import functools
from typing import Optional

from ewokscore.missing_data import MISSING_DATA
from ewoksorange.bindings.owwidgets import OWEwoksWidgetOneThread

from darfix import dtypes
from darfix.gui.dataPartitionWidget import DataPartitionWidget
from darfix.gui.operationThread import OperationThread
from darfix.gui.utils.message import missing_dataset_msg
from darfix.tasks.datapartition import DataPartition


class DataPartitionWidgetOW(OWEwoksWidgetOneThread, ewokstaskclass=DataPartition):
    """
    In cases with a large number of images you may want to omit the images with low intensity.
    This widget allows you to see an intensity curve of the images and to choose how many images you want to keep.
    At the next steps of the workflow only the images with higher intensity will be used for the analysis.
    """

    name = "partition data"
    icon = "icons/filter.png"
    want_main_area = False

    _ewoks_inputs_to_hide_from_orange = (
        "bins",
        "filter_bottom_bin_idx",
        "filter_top_bin_idx",
    )

    def __init__(self):
        super().__init__()
        self._threadComputeHistogram = None

        self._widget = DataPartitionWidget(parent=self)
        self.controlArea.layout().addWidget(self._widget)

        # update gui from default input value
        bins = self.get_default_input_value("bins", None)
        if bins is not None:
            self._widget.setBins(bins)

        filter_bottom_bin_idx = self.get_default_input_value(
            "filter_bottom_bin_idx", None
        )
        if filter_bottom_bin_idx is not None:
            self._widget.setBottomBin(filter_bottom_bin_idx)

        filter_top_bin_idx = self.get_default_input_value("filter_top_bin_idx", None)
        if filter_top_bin_idx is not None:
            self._widget.setTopBin(filter_top_bin_idx)

        # connect signal / slot
        self._widget.sigAbort.connect(self._abort_processing)
        self._widget.sigComputeHistogram.connect(self._computeHistogram)
        self._widget.sigPartitionData.connect(self.execute_ewoks_task)
        # keep ewoks default input value up to date.
        self._widget.sigNbBinsChanged.connect(self._nbBinsHasChanged)
        self._widget.sigBottomBinChanged.connect(self._bottomBinHasChanged)
        self._widget.sigTopBinChanged.connect(self._topBinHasChanged)

    def setDataset(self, dataset: Optional[dtypes.Dataset], pop_up=False):
        if dataset is None:
            return
        if not isinstance(dataset, dtypes.Dataset):
            raise dtypes.DatasetTypeError(dataset)
        self.set_dynamic_input("dataset", dataset)

        self._widget.setDataset(dataset)
        if pop_up:
            self.open()

    def handleNewSignals(self) -> None:
        """
        Today the DataPartitionWidget is not processing automatically a dataset when it receive it.
        It wait the user to press 'filter' in this case to process and move to the next widget.
        """
        dataset = self.get_task_input_value("dataset", MISSING_DATA)
        if dataset not in (MISSING_DATA, None):
            self.setDataset(dataset=dataset, pop_up=True)
        # note: we only want to execute the ewows task when 'ok' is pressed and not when a new dataset is set
        # return super().handleNewSignals() do not call to make sure the processing is not triggered

    def _computeHistogram(self):
        """
        compute the histogram and display it.
        It will help user select the bottom and top bins values.
        """
        dataset = self.get_task_input_value("dataset", MISSING_DATA)
        if dataset in (None, MISSING_DATA):
            missing_dataset_msg()
            return
        if not isinstance(dataset, dtypes.Dataset):
            raise dtypes.DatasetTypeError(dataset)
        self._threadComputeHistogram = OperationThread(
            self, dataset.dataset.compute_frames_intensity
        )
        self._widget.setProcessingButtonsEnabled(False)
        self._threadComputeHistogram.finished.connect(
            self._widget._showHistogramCallback
        )
        self._threadComputeHistogram.finished.connect(
            functools.partial(
                self._threadComputeHistogram.finished.disconnect,
                self._widget._showHistogramCallback,
            )
        )
        self._threadComputeHistogram.start()

    def _abort_processing(self):
        "stop all processing associated to the task or the widget"
        self.cancel_running_task()
        if self._threadComputeHistogram and self._threadComputeHistogram.isRunning():
            self._threadComputeHistogram.quit()

    def _nbBinsHasChanged(self, nb_bins):
        self.set_default_input("bins", nb_bins)

    def _bottomBinHasChanged(self, value):
        self.set_default_input("filter_bottom_bin_idx", value)

    def _topBinHasChanged(self, value):
        self.set_default_input("filter_top_bin_idx", value)
