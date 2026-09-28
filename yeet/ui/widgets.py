"""
Yeet - Modern KDE 6 UI Components & Widgets
App ID: gay.geeks.Yeet
Designed adhering to KDE 6 Human Interface Guidelines (HIG).
"""

from typing import Optional, Callable
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, Slot, QTimer, QPoint, QRect, QSize

class StatusBadge(QtWidgets.QFrame):
    """Modern KDE 6 status pill badge with colored dot."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusBadge")
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        self._dot = QtWidgets.QLabel()
        self._dot.setFixedSize(8, 8)
        self._label = QtWidgets.QLabel("Ready")
        self._label.setStyleSheet("font-weight: 600; font-size: 11px;")

        layout.addWidget(self._dot)
        layout.addWidget(self._label)

        self.setStatus("ready", "Ready")

    def setStatus(self, state: str, text: str):
        # State: "ready", "connected", "stopped", "accent"
        self._label.setText(text)
        if state == "connected":
            color = "#27ae60"  # Breeze positive green
            bg_color = "rgba(39, 174, 96, 0.18)"
            border_color = "rgba(39, 174, 96, 0.35)"
        elif state == "ready":
            color = "#3daee9"  # Breeze accent blue
            bg_color = "rgba(61, 174, 233, 0.15)"
            border_color = "rgba(61, 174, 233, 0.3)"
        elif state == "warning":
            color = "#f67400"  # Breeze warning orange
            bg_color = "rgba(246, 116, 0, 0.15)"
            border_color = "rgba(246, 116, 0, 0.3)"
        else:
            color = "#7f8c8d"
            bg_color = "rgba(127, 140, 141, 0.15)"
            border_color = "rgba(127, 140, 141, 0.3)"

        self._dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        self.setStyleSheet(f"""
            QFrame#statusBadge {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QLabel {{
                color: {color};
            }}
        """)


class KdeCard(QtWidgets.QFrame):
    """
    KDE 6 HIG Card Container.
    Features subtle rounded background, gentle border matching Breeze palette,
    and a clean title/subtitle header.
    """
    def __init__(self, title: str = "", subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("kdeCard")

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._main_layout.setContentsMargins(16, 14, 16, 16)
        self._main_layout.setSpacing(10)

        # Header section
        if title or subtitle:
            self._header_widget = QtWidgets.QWidget()
            header_layout = QtWidgets.QVBoxLayout(self._header_widget)
            header_layout.setContentsMargins(0, 0, 0, 4)
            header_layout.setSpacing(2)

            if title:
                self._title_label = QtWidgets.QLabel(title)
                self._title_label.setStyleSheet("font-size: 13pt; font-weight: bold;")
                header_layout.addWidget(self._title_label)

            if subtitle:
                self._subtitle_label = QtWidgets.QLabel(subtitle)
                self._subtitle_label.setWordWrap(True)
                self._subtitle_label.setStyleSheet("color: palette(placeholder-text); font-size: 9.5pt;")
                header_layout.addWidget(self._subtitle_label)

            self._main_layout.addWidget(self._header_widget)

        self._content_layout = QtWidgets.QVBoxLayout()
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        self._main_layout.addLayout(self._content_layout)

        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
            QFrame#kdeCard {
                background-color: palette(base);
                border: 1px solid palette(midlight);
                border-radius: 8px;
            }
        """)

    def addWidget(self, widget: QtWidgets.QWidget):
        self._content_layout.addWidget(widget)

    def addLayout(self, layout: QtWidgets.QLayout):
        self._content_layout.addLayout(layout)

    def setHeader(self, title: str, subtitle: str = ""):
        if hasattr(self, "_title_label"):
            self._title_label.setText(title)
        if hasattr(self, "_subtitle_label"):
            self._subtitle_label.setText(subtitle)


class FormRow(QtWidgets.QWidget):
    """
    A clean row in a KDE 6 card with a label (and optional description)
    and a control widget aligned to the right or expanded.
    """
    def __init__(self, label_text: str, control_widget: QtWidgets.QWidget, description: str = "", parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # Label container
        label_box = QtWidgets.QVBoxLayout()
        label_box.setContentsMargins(0, 0, 0, 0)
        label_box.setSpacing(2)

        self.label = QtWidgets.QLabel(label_text)
        self.label.setStyleSheet("font-weight: 500;")
        label_box.addWidget(self.label)

        if description:
            self.desc_label = QtWidgets.QLabel(description)
            self.desc_label.setWordWrap(True)
            self.desc_label.setStyleSheet("color: palette(placeholder-text); font-size: 9pt;")
            label_box.addWidget(self.desc_label)

        layout.addLayout(label_box, stretch=1)
        layout.addWidget(control_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class KdeExpander(QtWidgets.QFrame):
    """
    Modern collapsible disclosure section adhering to KDE 6 HIG.
    """
    def __init__(self, title: str, subtitle: str = "", icon_name: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("kdeExpander")
        self._is_expanded = False

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._main_layout.setContentsMargins(12, 10, 12, 10)
        self._main_layout.setSpacing(8)

        # Header clickable button
        self._toggle_btn = QtWidgets.QPushButton()
        self._toggle_btn.setFlat(True)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                border: none;
                padding: 4px 6px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: palette(midlight);
            }
        """)

        btn_layout = QtWidgets.QHBoxLayout(self._toggle_btn)
        btn_layout.setContentsMargins(4, 2, 4, 2)
        btn_layout.setSpacing(10)

        # Arrow indicator
        self._arrow_label = QtWidgets.QLabel("▶")
        self._arrow_label.setStyleSheet("font-size: 10pt; color: palette(placeholder-text);")
        btn_layout.addWidget(self._arrow_label)

        # Optional Icon
        if icon_name:
            icon_lbl = QtWidgets.QLabel()
            icon_lbl.setPixmap(QtGui.QIcon.fromTheme(icon_name).pixmap(18, 18))
            btn_layout.addWidget(icon_lbl)

        # Text labels
        text_layout = QtWidgets.QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self._title_lbl = QtWidgets.QLabel(title)
        self._title_lbl.setStyleSheet("font-weight: 600; font-size: 11pt;")
        text_layout.addWidget(self._title_lbl)

        if subtitle:
            self._sub_lbl = QtWidgets.QLabel(subtitle)
            self._sub_lbl.setStyleSheet("color: palette(placeholder-text); font-size: 9pt;")
            text_layout.addWidget(self._sub_lbl)

        btn_layout.addLayout(text_layout, stretch=1)
        self._main_layout.addWidget(self._toggle_btn)

        # Expandable container
        self._container = QtWidgets.QWidget()
        self._container_layout = QtWidgets.QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(12, 4, 8, 8)
        self._container_layout.setSpacing(6)
        self._container.setVisible(False)
        self._main_layout.addWidget(self._container)

        self._toggle_btn.clicked.connect(self.toggle)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet("""
            QFrame#kdeExpander {
                background-color: palette(base);
                border: 1px solid palette(midlight);
                border-radius: 8px;
            }
        """)

    def toggle(self):
        self.setExpanded(not self._is_expanded)

    def setExpanded(self, expanded: bool):
        self._is_expanded = expanded
        self._arrow_label.setText("▼" if expanded else "▶")
        self._container.setVisible(expanded)

    def addWidget(self, widget: QtWidgets.QWidget):
        self._container_layout.addWidget(widget)

    def addLayout(self, layout: QtWidgets.QLayout):
        self._container_layout.addLayout(layout)


class CodeBlock(QtWidgets.QFrame):
    """Monospaced command / code block with 1-click Copy button."""
    copied = Signal(str)

    def __init__(self, code_text: str, copy_label: str = "Copy Command", parent=None):
        super().__init__(parent)
        self.code_text = code_text
        self.setObjectName("codeBlock")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setPlainText(code_text)
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumHeight(90)
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Hack', 'Source Code Pro', 'JetBrains Mono', 'Monospace', monospace;
                font-size: 9pt;
                background-color: rgba(0, 0, 0, 0.25);
                color: palette(text);
                border: 1px solid palette(midlight);
                border-radius: 6px;
                padding: 6px;
            }
        """)
        layout.addWidget(self.text_edit)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        self.copy_btn = QtWidgets.QPushButton(copy_label)
        self.copy_btn.setIcon(QtGui.QIcon.fromTheme("edit-copy"))
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._on_copy)
        btn_layout.addWidget(self.copy_btn)

        layout.addLayout(btn_layout)
        self.setStyleSheet("""
            QFrame#codeBlock {
                background-color: palette(alternate-base);
                border: 1px solid palette(midlight);
                border-radius: 6px;
            }
        """)

    def _on_copy(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.code_text)
        self.copied.emit(self.code_text)
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("Copy Command"))


class KdeToast(QtWidgets.QFrame):
    """
    Floating notification toast that slides in and auto-dismisses,
    adhering to KDE Plasma 6 notification aesthetic.
    """
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setObjectName("kdeToast")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.icon_lbl = QtWidgets.QLabel()
        self.icon_lbl.setPixmap(QtGui.QIcon.fromTheme("dialog-information").pixmap(20, 20))
        layout.addWidget(self.icon_lbl)

        self.text_lbl = QtWidgets.QLabel()
        self.text_lbl.setStyleSheet("font-weight: 600; font-size: 10.5pt;")
        layout.addWidget(self.text_lbl)

        self.close_btn = QtWidgets.QPushButton()
        self.close_btn.setIcon(QtGui.QIcon.fromTheme("dialog-close"))
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setFlat(True)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.hideToast)
        layout.addWidget(self.close_btn)

        self.setStyleSheet("""
            QFrame#kdeToast {
                background-color: palette(window);
                border: 1px solid #3daee9;
                border-radius: 8px;
            }
            QLabel {
                color: palette(text);
            }
            QPushButton {
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: palette(midlight);
            }
        """)

        # Drop shadow effect
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hideToast)
        self.hide()

    def showMessage(self, message: str, icon_name: str = "dialog-information", timeout_ms: int = 3500):
        self.text_lbl.setText(message)
        self.icon_lbl.setPixmap(QtGui.QIcon.fromTheme(icon_name).pixmap(20, 20))
        self.adjustSize()

        # Center horizontally at top of parent
        parent = self.parentWidget()
        if parent:
            pw = parent.width()
            w = self.sizeHint().width()
            self.move(int((pw - w) / 2), 65)

        self.show()
        self.raise_()
        self._timer.start(timeout_ms)

    def hideToast(self):
        self._timer.stop()
        self.hide()
