"""
Yeet - Qt6 Application Subclass
App ID: gay.geeks.Yeet
"""

import sys
import signal
import logging
from .qt_compat import QtCore, QtGui, QtWidgets, Qt, QTimer
from .config import ConfigManager
from .server import ServerDaemon
from .ui.window import YeetWindow

logger = logging.getLogger("yeet.app")

class YeetApplication(QtWidgets.QApplication):
    def __init__(self, argv=None):
        super().__init__(argv or sys.argv)

        self.setApplicationName("Yeet")
        self.setApplicationDisplayName("Yeet")
        self.setDesktopFileName("gay.geeks.Yeet")
        self.setOrganizationName("gay.geeks")
        self.setOrganizationDomain("geeks.gay")
        self.setApplicationVersion("1.0.0")

        # Set default window icon
        icon = QtGui.QIcon.fromTheme("gay.geeks.Yeet", QtGui.QIcon.fromTheme("applications-games"))
        self.setWindowIcon(icon)

        self.config_manager = ConfigManager()
        self.server_daemon = ServerDaemon(self.config_manager)
        self.window: Optional[YeetWindow] = None

        # Clean shutdown hook
        self.aboutToQuit.connect(self._on_about_to_quit)

        # Allow terminal Ctrl+C (SIGINT) to interrupt Qt loop cleanly
        signal.signal(signal.SIGINT, lambda *args: self.quit())
        self._sigint_timer = QTimer(self)
        self._sigint_timer.timeout.connect(lambda: None)
        self._sigint_timer.start(500)

    def start(self):
        # Start background server daemon
        self.server_daemon.start()

        # Present main window
        self.window = YeetWindow(self.config_manager, self.server_daemon)
        self.window.show()

    def _on_about_to_quit(self):
        logger.info("Yeet application shutting down...")
        if self.server_daemon:
            self.server_daemon.stop()
