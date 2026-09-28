"""
Yeet - Main Application Window (Qt6 / KDE 6 Native)
App ID: gay.geeks.Yeet
"""

import os
from typing import Optional
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, Slot, QTimer
from ..config import ConfigManager
from ..server import ServerDaemon
from .target_view import TargetView
from .items_view import ItemsView
from .physics_view import PhysicsView
from .server_view import ServerView
from .widgets import KdeToast, StatusBadge
from .about_dialog import AboutDialog

class NavListWidget(QtWidgets.QListWidget):
    """Modern KDE 6 styled navigation sidebar list."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(190)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet("""
            QListWidget {
                background-color: palette(window);
                border: none;
                border-right: 1px solid palette(midlight);
                padding: 10px 8px;
                outline: none;
            }
            QListWidget::item {
                height: 40px;
                padding-left: 10px;
                padding-right: 10px;
                margin-bottom: 4px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 10pt;
                color: palette(text);
            }
            QListWidget::item:hover {
                background-color: palette(midlight);
            }
            QListWidget::item:selected {
                background-color: #3daee9;
                color: #ffffff;
                font-weight: bold;
            }
        """)

class YeetWindow(QtWidgets.QMainWindow):
    def __init__(self, config_manager: ConfigManager, server_daemon: ServerDaemon, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.server_daemon = server_daemon

        self.setWindowTitle("Yeet — Stream Throwing System")
        self.resize(1000, 740)
        self.setMinimumSize(680, 520)

        # Set Window Icon
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "icons", "gay.geeks.Yeet.svg"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            self.setWindowIcon(QtGui.QIcon.fromTheme("gay.geeks.Yeet", QtGui.QIcon.fromTheme("applications-games")))

        # Central Widget & Layout
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        central_layout = QtWidgets.QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Sidebar Navigation
        self.nav_list = NavListWidget()
        self._setup_nav_items()
        central_layout.addWidget(self.nav_list)

        # Stacked Views
        self.view_stack = QtWidgets.QStackedWidget()
        central_layout.addWidget(self.view_stack, stretch=1)

        self._setup_views()

        # Connect navigation
        self.nav_list.currentRowChanged.connect(self.view_stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        # Build KDE 6 Toolbar
        self._setup_toolbar()

        # Build Keyboard Shortcuts
        self._setup_shortcuts()

        # In-App Floating Toast
        self.toast = KdeToast(self)

        # Periodic status refresh timer (every 2 seconds)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._on_periodic_status_update)
        self.status_timer.start(2000)

        # Initial badge update
        self._update_server_badge()

    def _setup_nav_items(self):
        items = [
            ("Targets", "mark-location", "Collision boundaries & coordinate mapper"),
            ("Items", "package-x-generic", "Throwable inventory & sounds"),
            ("Physics", "applications-games", "Spawns, ballistic aim & gravity"),
            ("OBS & Server", "network-server", "OBS browser source & REST API"),
        ]
        for title, icon_name, tooltip in items:
            item = QtWidgets.QListWidgetItem(QtGui.QIcon.fromTheme(icon_name), title)
            item.setToolTip(tooltip)
            self.nav_list.addItem(item)

    def _setup_views(self):
        # 1. Targets View
        self.target_view = TargetView(self.config_manager)
        self.target_view.targetsUpdated.connect(self._on_targets_updated)
        self.view_stack.addWidget(self.target_view)

        # 2. Items View
        self.items_view = ItemsView(self.config_manager)
        self.items_view.itemsUpdated.connect(self._on_items_updated)
        self.items_view.testThrowRequested.connect(self.trigger_throw)
        self.view_stack.addWidget(self.items_view)

        # 3. Physics View
        self.physics_view = PhysicsView(self.config_manager)
        self.physics_view.physicsUpdated.connect(self._on_physics_updated)
        self.physics_view.testThrowRequested.connect(self.trigger_throw)
        self.physics_view.clearCanvasRequested.connect(self.trigger_clear)
        self.view_stack.addWidget(self.physics_view)

        # 4. Server View
        self.server_view = ServerView(self.config_manager)
        self.server_view.copyUrlRequested.connect(self._on_url_copied)
        self.server_view.clearCanvasRequested.connect(self.trigger_clear)
        self.server_view.messageNotice.connect(self.show_toast)
        self.view_stack.addWidget(self.server_view)

    def _setup_toolbar(self):
        toolbar = QtWidgets.QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QtCore.QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: palette(window);
                border: none;
                border-bottom: 1px solid palette(midlight);
                padding: 4px 8px;
                spacing: 8px;
            }
            QToolButton {
                padding: 5px 10px;
                border-radius: 6px;
                font-weight: 500;
            }
            QToolButton:hover {
                background-color: palette(midlight);
            }
        """)

        # Quick Test Throw Action
        self.test_throw_action = QtGui.QAction(QtGui.QIcon.fromTheme("media-playback-start"), "Test Throw", self)
        self.test_throw_action.setToolTip("Launch quick test barrage into OBS")
        self.test_throw_action.triggered.connect(self._on_quick_test_throw)
        toolbar.addAction(self.test_throw_action)

        # Copy OBS URL Action
        self.copy_url_action = QtGui.QAction(QtGui.QIcon.fromTheme("edit-copy"), "Copy OBS URL", self)
        self.copy_url_action.setToolTip("Copy OBS Browser Source URL to clipboard")
        self.copy_url_action.triggered.connect(self._on_copy_obs_url)
        toolbar.addAction(self.copy_url_action)

        toolbar.addSeparator()

        # Clear Canvas Action
        self.clear_action = QtGui.QAction(QtGui.QIcon.fromTheme("edit-clear"), "Clear Canvas", self)
        self.clear_action.setToolTip("Despawn all active items from OBS overlay (Ctrl+K)")
        self.clear_action.setShortcut(QtGui.QKeySequence("Ctrl+K"))
        self.clear_action.triggered.connect(self.trigger_clear)
        toolbar.addAction(self.clear_action)

        # Spacer to push right-hand widgets
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Server Status Pill Badge
        self.server_badge = StatusBadge()
        toolbar.addWidget(self.server_badge)

        # Menu Button (Hamburger)
        menu_btn = QtWidgets.QToolButton()
        menu_btn.setIcon(QtGui.QIcon.fromTheme("application-menu", QtGui.QIcon.fromTheme("open-menu-symbolic")))
        menu_btn.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        app_menu = QtWidgets.QMenu(menu_btn)

        clear_menu_act = app_menu.addAction(QtGui.QIcon.fromTheme("edit-clear"), "Clear Overlay (Ctrl+K)", self.trigger_clear)
        open_browser_act = app_menu.addAction(QtGui.QIcon.fromTheme("web-browser"), "Open Overlay in Browser", self._on_docs_action)
        app_menu.addSeparator()
        docs_act = app_menu.addAction(QtGui.QIcon.fromTheme("help-contents"), "Documentation (F1)", self._on_docs_action)
        about_act = app_menu.addAction(QtGui.QIcon.fromTheme("help-about"), "About Yeet", self._on_about_action)
        app_menu.addSeparator()
        quit_act = app_menu.addAction(QtGui.QIcon.fromTheme("application-exit"), "Quit Yeet (Ctrl+Q)", self.close)

        menu_btn.setMenu(app_menu)
        toolbar.addWidget(menu_btn)

        self.addToolBar(toolbar)

    def _setup_shortcuts(self):
        quit_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)

        clear_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+K"), self)
        clear_shortcut.activated.connect(self.trigger_clear)

        docs_shortcut = QtGui.QShortcut(QtGui.QKeySequence("F1"), self)
        docs_shortcut.activated.connect(self._on_docs_action)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        super().resizeEvent(event)
        # Re-center toast if visible
        if hasattr(self, "toast") and self.toast.isVisible():
            pw = self.width()
            w = self.toast.sizeHint().width()
            self.toast.move(int((pw - w) / 2), 65)

    def show_toast(self, text: str, icon_name: str = "dialog-information"):
        self.toast.showMessage(text, icon_name=icon_name)

    def _update_server_badge(self):
        port = self.config_manager.server.port
        count = self.server_daemon.get_connected_count()
        if count > 0:
            self.server_badge.setStatus("connected", f"OBS Connected ({count})")
        else:
            self.server_badge.setStatus("ready", f"Ready :{port}")

    def _on_periodic_status_update(self):
        self._update_server_badge()
        count = self.server_daemon.get_connected_count()
        self.server_view.update_connected_clients(count)
        self.server_view.update_collision_count(self.server_daemon.total_collisions)

    def _on_copy_obs_url(self):
        url = self.server_view.get_overlay_url()
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(url)
        self.show_toast("OBS Browser Source URL copied to clipboard!", "edit-copy")

    def _on_url_copied(self, url: str):
        self.show_toast("Copied to clipboard!", "edit-copy")

    def _on_quick_test_throw(self):
        items = list(self.config_manager.items.keys())
        item_id = items[0] if items else "tomato"
        self.trigger_throw(item_id, 3)

    def trigger_throw(self, item_id: str, amount: int = 1, spawn_direction: str = None, force: float = None, spread: float = None):
        if not spawn_direction:
            spawn_direction = self.config_manager.physics.default_spawn_direction
        if force is None:
            force = self.config_manager.physics.default_force
        if spread is None:
            spread = self.config_manager.physics.default_spread

        self.server_daemon.threadsafe_throw(item_id, amount, spawn_direction, force, spread)
        self.show_toast(f"Thrown {amount} × {item_id}!", "media-playback-start")

    def trigger_clear(self):
        self.server_daemon.threadsafe_clear()
        self.show_toast("OBS Overlay cleared!", "edit-clear")

    def _on_targets_updated(self):
        self.server_daemon.threadsafe_broadcast({
            "type": "targets_updated",
            "targets": [t.to_dict() for t in self.config_manager.targets]
        })

    def _on_items_updated(self):
        self.server_daemon.threadsafe_update_config()
        self.physics_view.refresh_from_config()

    def _on_physics_updated(self):
        self.server_daemon.threadsafe_update_config()
        self.target_view.canvas.setSpawnDirection(self.config_manager.physics.default_spawn_direction)

    def _on_docs_action(self):
        url = f"http://{self.config_manager.server.host}:{self.config_manager.server.port}/overlay"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _on_about_action(self):
        dialog = AboutDialog(self)
        dialog.exec()
