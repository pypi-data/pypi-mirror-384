from __future__ import annotations

import h5py
from silx.gui import qt

from darfix.core.datapathfinder import DETECTOR_KEYWORD
from darfix.core.datapathfinder import EXISTING_KEYWORDS
from darfix.core.datapathfinder import FIRST_SCAN_KEYWORD
from darfix.core.datapathfinder import LAST_SCAN_KEYWORD
from darfix.core.datapathfinder import SCAN_KEYWORD
from darfix.core.datapathfinder import get_first_group
from darfix.core.datapathfinder import get_last_group


class _TreeBuilder:
    """Build the tree to be used by the DataPathModel"""

    def __init__(
        self,
        file: str,
        qt_root_node: qt.QStandardItem,
        root_keywords: tuple,
        leaf_keywords: tuple,
    ) -> None:
        assert isinstance(
            qt_root_node, qt.QStandardItem
        ), f"hdf5_root_node should be an instance of {qt.QStandardItem}. Got {type(qt_root_node)}"
        assert isinstance(
            root_keywords, tuple
        ), f"root_keywords should be an instance of tuple. Got {type(root_keywords)}"
        assert isinstance(
            leaf_keywords, tuple
        ), f"leaf_keywords should be an instance of tuple. Got {type(leaf_keywords)}"
        self._qt_root_node = qt_root_node
        self._file = file

        assert DETECTOR_KEYWORD not in root_keywords
        self._root_keywords = root_keywords
        self._leaf_keywords = leaf_keywords
        self._display_dataset = True

    def displayDataset(self) -> bool:
        return self._display_dataset

    def setDisplayDataset(self, display: bool):
        self._display_dataset = display

    @staticmethod
    def addFirstScanKeyword(
        h5f, root_node: qt.QStandardItem
    ) -> tuple[h5py.Group, qt.QStandardItem, bool]:
        first_group = get_first_group(h5f, as_hdf5_item=True)
        qt_root = qt.QStandardItem(FIRST_SCAN_KEYWORD)
        qt_root.setData(FIRST_SCAN_KEYWORD, _DataPathCompleter.ConcatenationRole)
        root_node.appendRow(qt_root)
        return first_group, qt_root, False

    @staticmethod
    def addLastScanKeyword(
        h5f, root_node: qt.QStandardItem
    ) -> tuple[h5py.Group, qt.QStandardItem, bool]:
        last_group = get_last_group(h5f, as_hdf5_item=True)
        qt_root = qt.QStandardItem(LAST_SCAN_KEYWORD)
        qt_root.setData(LAST_SCAN_KEYWORD, _DataPathCompleter.ConcatenationRole)
        root_node.appendRow(qt_root)
        return last_group, qt_root, False

    @staticmethod
    def addScanKeyword(
        h5f, root_node: qt.QStandardItem
    ) -> tuple[h5py.Group, qt.QStandardItem, bool]:
        first_group = get_first_group(h5f, as_hdf5_item=True)
        qt_root = qt.QStandardItem(SCAN_KEYWORD)
        qt_root.setData(SCAN_KEYWORD, _DataPathCompleter.ConcatenationRole)
        root_node.appendRow(qt_root)
        return first_group, qt_root, False

    def buildTree(self):
        """build tree from root"""

        tree_root_mapping = {
            FIRST_SCAN_KEYWORD: self.addFirstScanKeyword,
            LAST_SCAN_KEYWORD: self.addLastScanKeyword,
            SCAN_KEYWORD: self.addScanKeyword,
        }

        with h5py.File(self._file, mode="r") as h5f:
            preprocessing_info: list[tuple[qt.QStandardItem, h5py.Group, bool]] = []

            for keyword in self._root_keywords:
                hdf5_root, qt_root, append_first = tree_root_mapping[keyword](
                    h5f, self._qt_root_node
                )
                preprocessing_info.append((hdf5_root, qt_root, append_first))

            if SCAN_KEYWORD not in self._root_keywords:
                # if {scan} is part of the keywords then we don't want to add the first
                # level groups (1.1...) because they are not 'valid' options in the {scan} context
                preprocessing_info.append((h5f, self._qt_root_node, True))

            for hdf5_root, qt_root, append_first in preprocessing_info:
                self.populateItem(
                    qt_parent_item=qt_root,
                    hdf5_item=hdf5_root,
                    create_first_item=append_first,
                    display_dataset=self.displayDataset(),
                )

    def populateItem(
        self,
        hdf5_item: h5py.Group | h5py.Dataset,
        qt_parent_item: qt.QStandardItem,
        create_first_item: bool = True,
        display_dataset: bool = False,
    ):
        """
        :param create_first_item: if True then create a QStandardItem for the given hdf5_item. else skip it (in the case {scan} keyword it doesn't make sense to display all the 1.1, 2.1... groups)
        :param display_dataset: if False then the h5py.Dataset will not appear. When looking for positioners for example we want to filter those
        """
        if not display_dataset and isinstance(hdf5_item, h5py.Dataset):
            return
        if create_first_item:
            text = hdf5_item.name.split("/")[-1]
            qt_children_item = qt.QStandardItem(text)
            qt_children_item.setData(text, _DataPathCompleter.ConcatenationRole)
            qt_parent_item.appendRow(qt_children_item)
        else:
            qt_children_item = qt_parent_item

        if isinstance(hdf5_item, h5py.Dataset):
            return

        # populate from leaf keywords
        for leaf_keyword in self._leaf_keywords:
            if not self.has_already_keyword(qt_parent_item, leaf_keyword):
                qt_leaf_keyword_item = qt.QStandardItem(leaf_keyword)
                qt_leaf_keyword_item.setData(
                    leaf_keyword, _DataPathCompleter.ConcatenationRole
                )
                qt_parent_item.appendRow(qt_leaf_keyword_item)

        # populate from the hdf5 file
        for key in hdf5_item.keys():
            hdf5_children_item = hdf5_item.get(key)
            self.populateItem(
                hdf5_item=hdf5_children_item,
                qt_parent_item=qt_children_item,
                display_dataset=display_dataset,
                create_first_item=True,
            )

    @staticmethod
    def has_already_keyword(qt_item, keyword):
        for i_row in range(qt_item.rowCount()):
            for i_col in range(qt_item.columnCount()):
                child = qt_item.child(i_row, i_col)
                if child.text() == keyword:
                    return True
        return False


class DataPathModel(qt.QStandardItemModel):
    """
    Model that provide HDF5 file tree combined with some reserved keywords.
    Keywords must be provided as '{my_keyword}'.

    At the moment there is two types of keywords:
    * root keywords ({scan}, {first_scan}, {last_scan}')
    * leaf keywords ('{detector}')
    """

    def __init__(
        self,
        parent: qt.QObject | None = None,
        allowed_keywords: tuple = (),
        display_dataset: bool = True,
    ) -> None:
        self._file = None
        for pattern in allowed_keywords:
            assert (
                pattern in EXISTING_KEYWORDS
            ), f"allowed keywords are {EXISTING_KEYWORDS}"
        self._allowed_keywords = allowed_keywords
        self._display_dataset = display_dataset
        super().__init__(parent)

    def getAllowedKeywords(self) -> tuple:
        return self._allowed_keywords

    def setAllowedKeywords(self, keywords: tuple) -> None:
        self._allowed_keywords = keywords
        self.clear()
        self._build()

    def data(self, index, role):
        return super().data(index, role)

    def setFile(self, hdf5_file: str):
        self._file = hdf5_file
        self.clear()
        self._build()

    def _build(self):
        if self._file is None:
            return

        builder = _TreeBuilder(
            file=self._file,
            qt_root_node=self.invisibleRootItem(),
            root_keywords=tuple(
                filter(lambda a: a != DETECTOR_KEYWORD, self.getAllowedKeywords())
            ),
            leaf_keywords=(
                (DETECTOR_KEYWORD,)
                if DETECTOR_KEYWORD in self.getAllowedKeywords()
                else ()
            ),
        )
        builder.setDisplayDataset(display=self._display_dataset)
        builder.buildTree()


class DataPathLineEditWithCompleter(qt.QLineEdit):
    def __init__(
        self,
        parent=None,
        allowed_keywords: tuple = (),
        completer_display_dataset: bool = False,
    ):
        super().__init__(parent)

        self._completer = _DataPathCompleter(
            allowed_keywords=allowed_keywords, display_dataset=completer_display_dataset
        )
        self.setCompleter(self._completer)
        self.setToolTip("Ctrl+Space will trigger auto-completion")

    def setFile(self, file):
        self._completer.setFile(file)

    def setAllowedKeywords(self, keywords: tuple):
        self._completer.setAllowedKeywords(keywords=keywords)

    def keyPressEvent(self, key_event):
        # add Ctrl + space for completion
        modifiers = key_event.modifiers()
        if qt.Qt.KeyboardModifier.ControlModifier == modifiers:
            if key_event.key() == qt.Qt.Key.Key_Space:
                self._completer.complete(self.rect())

        super().keyPressEvent(key_event)


class _DataPathCompleter(qt.QCompleter):
    ConcatenationRole = qt.Qt.UserRole + 1

    def __init__(
        self,
        parent=None,
        allowed_keywords=EXISTING_KEYWORDS,
        display_dataset: bool = True,
    ):
        super().__init__(parent)
        self._separator = "/"
        self._model = DataPathModel(
            allowed_keywords=allowed_keywords, display_dataset=display_dataset
        )
        self.setModel(self._model)

    def setFile(self, file: str):
        self._model.setFile(file)

    def setAllowedKeywords(self, keywords: tuple):
        self._model.setAllowedKeywords(keywords=keywords)

    def pathFromIndex(self, ix):
        datalist = []
        while ix.isValid():
            datalist.insert(
                0, self._model.data(ix, _DataPathCompleter.ConcatenationRole)
            )
            ix = ix.parent()

        return self._separator.join(datalist)

    def splitPath(self, path):
        return path.split(self._separator)
