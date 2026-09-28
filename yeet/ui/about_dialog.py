"""
Yeet - KDE 6 Style About Application Dialog
App ID: gay.geeks.Yeet
"""

import os
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Yeet")
        self.setMinimumSize(540, 440)
        self.resize(560, 480)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 16)
        main_layout.setSpacing(16)

        # Header area: App Icon, Title, Version, Subtitle
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(16)

        icon_label = QtWidgets.QLabel()
        # Find scalable icon
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "icons", "gay.geeks.Yeet.svg"))
        if os.path.exists(icon_path):
            pixmap = QtGui.QIcon(icon_path).pixmap(64, 64)
        else:
            pixmap = QtGui.QIcon.fromTheme("gay.geeks.Yeet", QtGui.QIcon.fromTheme("applications-games")).pixmap(64, 64)
        icon_label.setPixmap(pixmap)
        header_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignTop)

        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(3)

        title_lbl = QtWidgets.QLabel("Yeet")
        title_lbl.setStyleSheet("font-size: 18pt; font-weight: bold;")
        info_layout.addWidget(title_lbl)

        version_lbl = QtWidgets.QLabel("Version 1.0.0 (Qt6 / KDE 6 Native)")
        version_lbl.setStyleSheet("color: palette(placeholder-text); font-size: 10pt;")
        info_layout.addWidget(version_lbl)

        subtitle_lbl = QtWidgets.QLabel("Wayland-native interactive stream throwing system and 2D physics overlay for OBS Studio.")
        subtitle_lbl.setWordWrap(True)
        subtitle_lbl.setStyleSheet("font-size: 10pt; margin-top: 4px;")
        info_layout.addWidget(subtitle_lbl)

        header_layout.addLayout(info_layout, stretch=1)
        main_layout.addLayout(header_layout)

        # Tab widget for About, Authors, License
        tab_widget = QtWidgets.QTabWidget()

        # Tab 1: About
        about_tab = QtWidgets.QWidget()
        about_layout = QtWidgets.QVBoxLayout(about_tab)
        about_layout.setContentsMargins(14, 14, 14, 14)
        about_layout.setSpacing(12)

        desc_text = QtWidgets.QLabel(
            "Yeet empowers livestreamers and VTubers to configure customizable 2D collision targets, "
            "manage throwable items with collision sounds, trigger throws via a local HTTP REST API, "
            "and render real-time physics overlays inside OBS Studio.<br><br>"
            "Built with <b>Qt6</b> adhering to the <b>KDE Human Interface Guidelines (HIG)</b> for "
            "pure Wayland sessions on KDE Plasma 6."
        )
        desc_text.setWordWrap(True)
        desc_text.setTextFormat(Qt.TextFormat.RichText)
        about_layout.addWidget(desc_text)

        links_form = QtWidgets.QFormLayout()
        links_form.setSpacing(8)

        gh_link = QtWidgets.QLabel('<a href="https://github.com/geeks/yeet" style="color: #3daee9;">https://github.com/geeks/yeet</a>')
        gh_link.setOpenExternalLinks(True)
        links_form.addRow("<b>Homepage:</b>", gh_link)

        issues_link = QtWidgets.QLabel('<a href="https://github.com/geeks/yeet/issues" style="color: #3daee9;">https://github.com/geeks/yeet/issues</a>')
        issues_link.setOpenExternalLinks(True)
        links_form.addRow("<b>Bug Tracker:</b>", issues_link)

        about_layout.addLayout(links_form)
        about_layout.addStretch()
        tab_widget.addTab(about_tab, QtGui.QIcon.fromTheme("help-about"), "About")

        # Tab 2: Authors
        authors_tab = QtWidgets.QWidget()
        authors_layout = QtWidgets.QVBoxLayout(authors_tab)
        authors_layout.setContentsMargins(14, 14, 14, 14)
        authors_layout.setSpacing(8)

        authors_list = QtWidgets.QListWidget()
        authors_list.setStyleSheet("background: transparent; border: none;")
        item1 = QtWidgets.QListWidgetItem("Yeet Contributors")
        item1.setToolTip("Core maintainers and developers")
        authors_list.addItem(item1)
        authors_layout.addWidget(authors_list)
        authors_layout.addWidget(QtWidgets.QLabel("Special thanks to all open source contributors and the KDE community!"))
        tab_widget.addTab(authors_tab, QtGui.QIcon.fromTheme("user-identity"), "Authors")

        # Tab 3: License
        license_tab = QtWidgets.QWidget()
        license_layout = QtWidgets.QVBoxLayout(license_tab)
        license_layout.setContentsMargins(14, 14, 14, 14)

        license_edit = QtWidgets.QPlainTextEdit()
        license_edit.setReadOnly(True)
        license_edit.setPlainText(
            "GNU GENERAL PUBLIC LICENSE\n"
            "Version 3, 29 June 2007\n\n"
            "Copyright (C) 2026 Yeet Contributors\n\n"
            "This program is free software: you can redistribute it and/or modify\n"
            "it under the terms of the GNU General Public License as published by\n"
            "the Free Software Foundation, either version 3 of the License, or\n"
            "(at your option) any later version.\n\n"
            "This program is distributed in the hope that it will be useful,\n"
            "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the\n"
            "GNU General Public License for more details."
        )
        license_edit.setStyleSheet("font-family: monospace; font-size: 9pt;")
        license_layout.addWidget(license_edit)
        tab_widget.addTab(license_tab, QtGui.QIcon.fromTheme("text-x-generic"), "License")

        main_layout.addWidget(tab_widget, stretch=1)

        # Bottom button box
        btn_box = QtWidgets.QHBoxLayout()
        btn_box.addStretch()

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setIcon(QtGui.QIcon.fromTheme("dialog-close"))
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        btn_box.addWidget(close_btn)

        main_layout.addLayout(btn_box)
