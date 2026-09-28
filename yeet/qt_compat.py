"""
Yeet - Qt6 Compatibility Layer
App ID: gay.geeks.Yeet
Supports PySide6 (primary) and PyQt6 (fallback).
"""

import sys

try:
    from PySide6 import QtCore, QtGui, QtWidgets, QtSvg
    from PySide6.QtCore import Qt, Signal, Slot, QPoint, QPointF, QRect, QRectF, QSize, QSizeF, QTimer
    QT_BINDING = "PySide6"
except ImportError:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets, QtSvg
        from PyQt6.QtCore import Qt, pyqtSignal as Signal, pyqtSlot as Slot, QPoint, QPointF, QRect, QRectF, QSize, QSizeF, QTimer
        QT_BINDING = "PyQt6"
    except ImportError as e:
        raise ImportError(
            "Neither PySide6 nor PyQt6 could be imported. Please install python-pyside6 or python-pyqt6."
        ) from e

__all__ = [
    "QtCore",
    "QtGui",
    "QtWidgets",
    "QtSvg",
    "Qt",
    "Signal",
    "Slot",
    "QPoint",
    "QPointF",
    "QRect",
    "QRectF",
    "QSize",
    "QSizeF",
    "QTimer",
    "QT_BINDING",
]
