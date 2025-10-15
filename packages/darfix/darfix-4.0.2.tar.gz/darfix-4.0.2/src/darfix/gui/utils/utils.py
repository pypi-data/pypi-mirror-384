from __future__ import annotations

from silx.gui import qt


def create_completer(filters=None) -> qt.QCompleter:
    completer = qt.QCompleter()
    if qt.BINDING in ("PyQt5", "PySide2"):
        # note: should work with PyQt5 but we get some troubles with it on esrf deployment
        # see https://gitlab.esrf.fr/XRD/darfix/-/issues/174
        model = qt.QDirModel(completer)
    else:
        completer.setCompletionRole(qt.QFileSystemModel.FilePathRole)
        model = qt.QFileSystemModel(completer)
        model.setRootPath(qt.QDir.currentPath())
        model.setOption(qt.QFileSystemModel.DontWatchForChanges)
    if filters is not None:
        model.setFilter(filters)
    completer.setModel(model)

    return completer


def select_output_hdf5_file_with_dialog() -> str | None:
    fileDialog = qt.QFileDialog()

    fileDialog.setFileMode(qt.QFileDialog.FileMode.AnyFile)
    fileDialog.setAcceptMode(qt.QFileDialog.AcceptMode.AcceptSave)
    fileDialog.setOption(qt.QFileDialog.Option.DontUseNativeDialog)
    fileDialog.setDefaultSuffix(".h5")
    if fileDialog.exec():
        return fileDialog.selectedFiles()[0]
    else:
        return None
