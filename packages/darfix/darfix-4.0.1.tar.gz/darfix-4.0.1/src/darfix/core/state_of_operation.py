from __future__ import annotations

from contextlib import contextmanager
from enum import IntEnum
from typing import Optional


class Operation(IntEnum):
    """
    Flags for different operations in Dataset
    """

    PARTITION = 0
    BS = 1
    HP = 2
    THRESHOLD = 3
    SHIFT = 4
    ROI = 5
    MOMENTS = 6
    FIT = 7
    BINNING = 8
    MASK = 9


class StateOfOperations:
    def __init__(self):
        self._is_running = [False] * len(Operation)

    def _start(self, operation: Optional[Operation]) -> None:
        if operation is None:
            return
        self._is_running[operation] = True

    def stop(self, operation: Optional[Operation]) -> None:
        if operation is None:
            return
        self._is_running[operation] = False

    @contextmanager
    def run_context(self, operation: Optional[Operation]):
        self._start(operation)
        try:
            yield
        finally:
            self.stop(operation)

    def is_running(self, operation: Operation) -> bool:
        return self._is_running[operation]
