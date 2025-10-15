from silx.gui import qt


def show_error_msg(txt: str):
    """
    Show a dialog with an error message and a OK button
    """
    qt.QMessageBox.critical(
        None, "Error", txt, buttons=qt.QMessageBox.StandardButton.Ok
    )


def missing_dataset_msg():
    """
    show a dialog to the user notifying that the current widget has no dataset
    (and as a consequence cannot process)
    """
    msg = qt.QMessageBox()
    msg.setIcon(qt.QMessageBox.Critical)
    msg.setText("No dataset defined. Unable to process")
    msg.setWindowTitle("Missing dataset")
    msg.exec()


def unable_to_search_inside_hdf5_file(err_msg: str):
    """
    Show dialog to the user to notifying that we cannot search inside a HDF5 file.
    The issue is described in the 'err_msg'
    """
    msg = qt.QMessageBox()
    msg.setIcon(qt.QMessageBox.Critical)
    msg.setText(err_msg)
    msg.setWindowTitle("Fail HDF5 group / dataset search")
    msg.setStandardButtons(qt.QMessageBox.Ok)
    msg.exec()
