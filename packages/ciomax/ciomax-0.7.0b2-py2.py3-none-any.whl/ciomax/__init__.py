from .const import MAX_VERSION_MAJOR

if MAX_VERSION_MAJOR >= 2025:
    from PySide6 import QtWidgets, QtCore, QtGui
else:
    from PySide2 import QtWidgets, QtCore, QtGui