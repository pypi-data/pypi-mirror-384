__authors__ = ["J. Garriga"]
__license__ = "MIT"
__date__ = "26/07/2019"


from silx.gui import qt


class OperationThread(qt.QThread):
    """
    Given a function and a set of arguments, it calls it whenever the thread
    is started.
    """

    def __init__(self, parent, function):
        qt.QThread.__init__(self, parent=parent)
        self.func = function
        self.args = []
        self.kwargs = {}
        self.data = None

    def setArgs(self, *args, **kwargs):
        """
        Function to set the arguments of the function

        :param List args:
        """
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.data = self.func(*self.args, **self.kwargs)
