from silx.gui import qt

if qt.BINDING == "PyQt5":
    from PyQt5.QtTest import QSignalSpy
elif qt.BINDING == "PySide6":
    from PySide6.QtTest import QSignalSpy
elif qt.BINDING == "PyQt6":
    from PyQt6.QtTest import QSignalSpy
else:
    QSignalSpy = None
