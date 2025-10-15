__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "08/04/2020"


from silx.gui import qt

from darfix import dtypes
from darfix.gui.utils.message import missing_dataset_msg


class MetadataWidget(qt.QMainWindow):
    def __init__(self, parent=None):
        """
        Widget used to show the metadata in a table.
        """
        super(MetadataWidget, self).__init__(parent)
        self._dataset = None
        self.setWindowTitle("Metadata")
        self._dataset = None

        self._table = qt.QTableWidget()

        mainWidget = qt.QWidget(self)
        mainWidget.setLayout(qt.QVBoxLayout())
        mainWidget.layout().addWidget(self._table)

        self.mainWidget = mainWidget
        self.setCentralWidget(mainWidget)

    def setDataset(self, dataset: dtypes.Dataset):
        self._dataset = dataset.dataset
        self._updateView()

    def clearTable(self):
        self._table.clear()

    def _updateView(self):
        """
        Updates the view to show the correponding metadata.

        """
        if self._dataset is None:
            missing_dataset_msg()
            return

        self._table.clear()
        metadata = self._dataset.metadata_dict

        self._table.setColumnCount(len(metadata))
        self._table.setHorizontalHeaderLabels(metadata.keys())

        row_count = 0

        for column, (key, values) in enumerate(metadata.items()):
            if row_count < len(values):
                row_count = len(values)
                self._table.setRowCount(row_count)

            for row, value in enumerate(values):
                _item = qt.QTableWidgetItem()
                _item.setText(str(value))
                _item.setFlags(qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable)
                self._table.setItem(row, column, _item)
