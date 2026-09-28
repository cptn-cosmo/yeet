"""
Yeet - Server & OBS Integration View (Qt6 / KDE 6)
App ID: gay.geeks.Yeet
"""

import threading
import urllib.request
from typing import Optional
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, Slot
from ..config import ConfigManager
from .widgets import KdeCard, FormRow, KdeExpander, CodeBlock, StatusBadge

class ServerView(QtWidgets.QWidget):
    copyUrlRequested = Signal(str)
    clearCanvasRequested = Signal()
    messageNotice = Signal(str)

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._updating_wh = False

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        main_layout.addWidget(scroll)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        scroll.setWidget(container)

        # --- 1. OBS Studio Browser Source Card ---
        obs_card = KdeCard(
            title="OBS Studio Browser Source",
            subtitle="Add this URL as a Browser Source inside OBS Studio to display the physics overlay."
        )

        url_box = QtWidgets.QHBoxLayout()
        url_box.setSpacing(8)

        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setReadOnly(True)
        self.url_edit.setStyleSheet("font-family: monospace; font-size: 10pt; padding: 6px;")
        url_box.addWidget(self.url_edit, stretch=1)

        copy_btn = QtWidgets.QPushButton("Copy URL")
        copy_btn.setIcon(QtGui.QIcon.fromTheme("edit-copy"))
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3daee9;
                color: #ffffff;
                font-weight: 600;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        copy_btn.clicked.connect(self._on_copy_url_clicked)
        url_box.addWidget(copy_btn)

        open_btn = QtWidgets.QPushButton("Open in Browser")
        open_btn.setIcon(QtGui.QIcon.fromTheme("web-browser"))
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self._on_open_browser_clicked)
        url_box.addWidget(open_btn)

        obs_card.addLayout(url_box)

        # Recommended OBS Settings Expander
        obs_exp = KdeExpander("Recommended OBS Studio Source Settings", "Click to view optimal canvas, frame rate, and visibility settings", "help-about")
        tips = [
            "• <b>Width & Height:</b> 1920 × 1080 (or match your base stream canvas)",
            "• <b>Custom Frame Rate:</b> Checked, set to 60 FPS for smooth physics",
            "• <b>Control Audio via OBS:</b> Optional (overlay plays audio natively via browser)",
            "• <b>Shutdown source when not visible:</b> <b>UNCHECKED</b> (essential to keep WebSocket alive)",
            "• <b>Refresh browser when scene becomes active:</b> <b>UNCHECKED</b>"
        ]
        for t in tips:
            lbl = QtWidgets.QLabel(t)
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setStyleSheet("color: palette(placeholder-text); font-size: 9.5pt;")
            obs_exp.addWidget(lbl)

        obs_card.addWidget(obs_exp)
        layout.addWidget(obs_card)

        # --- 2. Live Daemon Status Card ---
        self.status_card = KdeCard(
            title="Local Daemon Status",
            subtitle="Real-time WebSocket connection state and impact counters."
        )

        self.status_badge = StatusBadge()
        self.status_card.addWidget(FormRow("Daemon State", self.status_badge, "Embedded aiohttp server thread"))

        self.clients_label = QtWidgets.QLabel("0 active")
        self.clients_label.setStyleSheet("font-weight: bold; color: #3daee9;")
        self.status_card.addWidget(FormRow("Connected OBS Overlays", self.clients_label, "Browser sources receiving real-time events"))

        self.hits_label = QtWidgets.QLabel("0 hits")
        self.hits_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.status_card.addWidget(FormRow("Total Collision Impacts", self.hits_label, "Cumulative hits recorded during this session"))

        self.port_spin = QtWidgets.QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(49122)
        self.port_spin.setMinimumWidth(120)
        self.port_spin.valueChanged.connect(self._on_port_changed)
        self.status_card.addWidget(FormRow("HTTP / WebSocket Port", self.port_spin, "Default: 49122"))

        clear_btn = QtWidgets.QPushButton("Clear Canvas")
        clear_btn.setIcon(QtGui.QIcon.fromTheme("edit-clear"))
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #da4453;
                color: #ffffff;
                font-weight: 600;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        clear_btn.clicked.connect(lambda: self.clearCanvasRequested.emit())
        self.status_card.addWidget(FormRow("Emergency Overlay Reset", clear_btn, "Removes all active physics bodies from connected overlays"))

        layout.addWidget(self.status_card)

        # --- 3. Collision Webhooks (First & Last Hit) Card ---
        self.webhook_card = KdeCard(
            title="Collision Webhooks (First and Last Hit)",
            subtitle="Trigger external URLs upon initial impact and after the barrage settles (ideal for VTube Studio or smart lights)."
        )

        self.wh_enabled_check = QtWidgets.QCheckBox("Enable Outbound Webhooks")
        self.wh_enabled_check.toggled.connect(self._on_webhook_changed)
        self.webhook_card.addWidget(FormRow("Outbound Webhooks", self.wh_enabled_check, "Dispatches HTTP requests on collisions"))

        self.first_url_edit = QtWidgets.QLineEdit()
        self.first_url_edit.setPlaceholderText("http://127.0.0.1:8001/vts/hotkey?id=Expression_Dizzy")
        self.first_url_edit.textChanged.connect(self._on_webhook_changed)
        self.webhook_card.addWidget(FormRow("First Hit URL", self.first_url_edit, "Fires on the very first impact of a throw"))

        self.first_method_combo = QtWidgets.QComboBox()
        self.first_method_combo.addItems(["GET", "POST"])
        self.first_method_combo.currentIndexChanged.connect(self._on_webhook_changed)
        self.webhook_card.addWidget(FormRow("First Hit Method", self.first_method_combo, "HTTP Request Method"))

        self.last_url_edit = QtWidgets.QLineEdit()
        self.last_url_edit.setPlaceholderText("http://127.0.0.1:8001/vts/hotkey?id=Expression_Neutral")
        self.last_url_edit.textChanged.connect(self._on_webhook_changed)
        self.webhook_card.addWidget(FormRow("Last Hit URL", self.last_url_edit, "Fires when the barrage settles"))

        self.last_method_combo = QtWidgets.QComboBox()
        self.last_method_combo.addItems(["GET", "POST"])
        self.last_method_combo.currentIndexChanged.connect(self._on_webhook_changed)
        self.webhook_card.addWidget(FormRow("Last Hit Method", self.last_method_combo, "HTTP Request Method"))

        self.delay_spin = QtWidgets.QDoubleSpinBox()
        self.delay_spin.setRange(0.5, 10.0)
        self.delay_spin.setSingleStep(0.5)
        self.delay_spin.setDecimals(1)
        self.delay_spin.setSuffix(" s")
        self.delay_spin.setMinimumWidth(120)
        self.delay_spin.valueChanged.connect(self._on_webhook_changed)
        self.webhook_card.addWidget(FormRow("Barrage Settling Delay", self.delay_spin, "Silence duration after impact before triggering Last Hit"))

        # Webhook Testing Row
        test_wh_box = QtWidgets.QHBoxLayout()
        test_wh_box.setSpacing(8)

        test_first_btn = QtWidgets.QPushButton("Test First Hit")
        test_first_btn.setIcon(QtGui.QIcon.fromTheme("media-playback-start"))
        test_first_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_first_btn.clicked.connect(lambda: self._test_webhook("first_hit"))
        test_wh_box.addWidget(test_first_btn)

        test_last_btn = QtWidgets.QPushButton("Test Last Hit")
        test_last_btn.setIcon(QtGui.QIcon.fromTheme("media-playback-stop"))
        test_last_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_last_btn.clicked.connect(lambda: self._test_webhook("last_hit"))
        test_wh_box.addWidget(test_last_btn)

        test_wh_box.addStretch()
        self.webhook_card.addWidget(FormRow("Test Webhook Triggers", QtWidgets.QWidget()))
        self.webhook_card.addLayout(test_wh_box)

        layout.addWidget(self.webhook_card)

        # --- 4. REST API & Bot Triggers Card ---
        api_card = KdeCard(
            title="REST API and Bot Triggers",
            subtitle="Trigger throws and collisions programmatically using Streamer.bot, MixItUp, SAMMI, or curl."
        )

        # POST /api/v1/throw
        post_throw_exp = KdeExpander("POST /api/v1/throw (JSON Body)", "Trigger throws using JSON payload", "applications-internet")
        curl_post_throw = (
            'curl -X POST http://127.0.0.1:49122/api/v1/throw \\\n'
            '  -H "Content-Type: application/json" \\\n'
            '  -d \'{\n'
            '    "item": "beachball",\n'
            '    "amount": 3,\n'
            '    "spawn_direction": "aimed",\n'
            '    "force": 1.2,\n'
            '    "spread": 15.0\n'
            '  }\''
        )
        post_throw_exp.addWidget(CodeBlock(curl_post_throw))
        api_card.addWidget(post_throw_exp)

        # GET /api/v1/throw
        get_throw_exp = KdeExpander("GET /api/v1/throw (URL Query Parameters)", "Trigger throws via URL query string (chat bot bookmarks)", "applications-internet")
        curl_get_throw = 'curl "http://127.0.0.1:49122/api/v1/throw?item=beachball&amount=3&spawn_direction=rain&force=1.2"'
        get_throw_exp.addWidget(CodeBlock(curl_get_throw))
        api_card.addWidget(get_throw_exp)

        # GET /api/v1/throw (Random Mix)
        mix_throw_exp = KdeExpander("GET /api/v1/throw (Random Mix & Group Filters)", "Barrage where projectiles are randomly picked from filtered pools", "applications-internet")
        curl_mix_throw = 'curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&items=all&item_exclude=winter&amount=5"'
        mix_throw_exp.addWidget(CodeBlock(curl_mix_throw))
        api_card.addWidget(mix_throw_exp)

        # POST /api/v1/clear
        clear_api_exp = KdeExpander("POST /api/v1/clear (Clear Canvas)", "Immediately despawn all active physics bodies", "edit-clear")
        curl_clear = 'curl -X POST http://127.0.0.1:49122/api/v1/clear'
        clear_api_exp.addWidget(CodeBlock(curl_clear))
        api_card.addWidget(clear_api_exp)

        # GET /api/v1/collision
        coll_api_exp = KdeExpander("GET /api/v1/collision (Trigger Direct Hit)", "Simulate immediate impact sound and burst without projectile delay", "dialog-information")
        curl_coll = 'curl "http://127.0.0.1:49122/api/v1/collision?target=VTuber+Head&item=beachball&sound=pop"'
        coll_api_exp.addWidget(CodeBlock(curl_coll))
        api_card.addWidget(coll_api_exp)

        # GET /api/v1/collisions
        stats_api_exp = KdeExpander("GET /api/v1/collisions (Query Hit Statistics)", "Retrieve total hits, breakdown by target, and recent log", "view-statistics")
        curl_stats = 'curl http://127.0.0.1:49122/api/v1/collisions'
        stats_api_exp.addWidget(CodeBlock(curl_stats))
        api_card.addWidget(stats_api_exp)

        layout.addWidget(api_card)
        layout.addStretch()

        self.update_url_display()

    def get_overlay_url(self) -> str:
        s = self.config_manager.server
        return f"http://{s.host}:{s.port}/overlay"

    def update_url_display(self):
        url = self.get_overlay_url()
        self.url_edit.setText(url)
        self.port_spin.setValue(self.config_manager.server.port)
        self._refresh_webhooks()

    def update_connected_clients(self, count: int):
        self.clients_label.setText(f"{count} active")
        if count > 0:
            self.status_badge.setStatus("connected", f"OBS Connected ({count})")
        else:
            port = self.config_manager.server.port
            self.status_badge.setStatus("ready", f"Ready :{port}")

    def update_collision_count(self, count: int):
        self.hits_label.setText(f"{count} hits")

    def _refresh_webhooks(self):
        wh = self.config_manager.webhooks
        self._updating_wh = True
        try:
            self.wh_enabled_check.setChecked(wh.enabled)
            self.first_url_edit.setText(wh.first_hit_url or "")
            self.first_method_combo.setCurrentIndex(0 if (wh.first_hit_method or "GET").upper() == "GET" else 1)
            self.last_url_edit.setText(wh.last_hit_url or "")
            self.last_method_combo.setCurrentIndex(0 if (wh.last_hit_method or "GET").upper() == "GET" else 1)
            self.delay_spin.setValue(wh.settling_delay or 2.0)
        finally:
            self._updating_wh = False

    def _on_webhook_changed(self, *args):
        if self._updating_wh:
            return
        wh = self.config_manager.webhooks
        wh.enabled = self.wh_enabled_check.isChecked()
        wh.first_hit_url = self.first_url_edit.text().strip()
        wh.first_hit_method = self.first_method_combo.currentText()
        wh.last_hit_url = self.last_url_edit.text().strip()
        wh.last_method_combo = self.last_method_combo.currentText()
        wh.settling_delay = self.delay_spin.value()
        self.config_manager.save()

    def _test_webhook(self, event_type: str):
        port = self.config_manager.server.port
        url = f"http://127.0.0.1:{port}/api/v1/webhooks/test?event={event_type}"

        def _worker():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Yeet-Qt-App"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    pass
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_notify_test_success",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, event_type)
                )
            except Exception as e:
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_notify_test_error",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, event_type),
                    QtCore.Q_ARG(str, str(e))
                )

        threading.Thread(target=_worker, daemon=True).start()

    @Slot(str)
    def _notify_test_success(self, event_type: str):
        event_name = "First Hit" if event_type == "first_hit" else "Last Hit"
        self.messageNotice.emit(f"Dispatched {event_name} test webhook!")

    @Slot(str, str)
    def _notify_test_error(self, event_type: str, err: str):
        event_name = "First Hit" if event_type == "first_hit" else "Last Hit"
        self.messageNotice.emit(f"Failed to dispatch {event_name}: {err}")

    def _on_port_changed(self, val: int):
        if val != self.config_manager.server.port:
            self.config_manager.server.port = val
            self.config_manager.save()
            self.update_url_display()

    def _on_copy_url_clicked(self):
        url = self.get_overlay_url()
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(url)
        self.copyUrlRequested.emit(url)

    def _on_open_browser_clicked(self):
        url = self.get_overlay_url()
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
