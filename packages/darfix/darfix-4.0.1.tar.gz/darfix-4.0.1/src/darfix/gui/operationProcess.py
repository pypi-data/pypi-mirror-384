import logging
import multiprocessing as mp
from multiprocessing.connection import Connection

from silx.gui import qt

_logger = logging.getLogger(__name__)


class OperationProcess(qt.QThread):
    """
    A QThread that run an async operation process and emit `finished` signal with the result of the `function` callback as an argument.
    Process can be aborted by calling `kill`. In this case the `finished` argument is None.
    """

    finished = qt.Signal(object)  # emits result or None if aborted

    def __init__(self, parent, function, *args, **kwargs):
        super().__init__(parent)
        self.__parent_conn, self.__child_conn = mp.Pipe(False)
        self.__process = mp.Process(
            target=self._target,
            args=(self.__child_conn, function, args, kwargs),
        )

    def _target(self, conn: Connection, func, args, kwargs):
        """Run function in child process and put result in queue."""
        try:
            res = func(*args, **kwargs)
        except Exception as e:
            res = e
        conn.send(res)

    def run(self):
        self.__process.start()
        self.__process.join()
        result = None
        if self.__parent_conn.poll():
            result = self.__parent_conn.recv()
            if isinstance(result, Exception):
                _logger.error(result, exc_info=True)
                result = None
        self.finished.emit(result)

    def kill(self):
        """Forcefully terminate the process and emit None."""
        self.__process.terminate()
