"""
Yeet - Adw.Application Subclass
App ID: gay.geeks.Yeet
"""

import sys
import logging
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from .config import ConfigManager
from .server import ServerDaemon
from .ui.window import YeetWindow

logger = logging.getLogger("yeet.app")

class YeetApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="gay.geeks.Yeet",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        self.config_manager = ConfigManager()
        self.server_daemon = ServerDaemon(self.config_manager)
        self.window = None

    def do_startup(self):
        Adw.Application.do_startup(self)

        # Add Actions
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda a, p: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q"])

        clear_action = Gio.SimpleAction.new("clear_canvas", None)
        clear_action.connect("activate", self._on_clear_action)
        self.add_action(clear_action)
        self.set_accels_for_action("app.clear_canvas", ["<Control>k"])

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about_action)
        self.add_action(about_action)

        docs_action = Gio.SimpleAction.new("documentation", None)
        docs_action.connect("activate", self._on_docs_action)
        self.add_action(docs_action)

        # Start background server daemon
        self.server_daemon.start()

    def do_activate(self):
        if not self.window:
            self.window = YeetWindow(self, self.config_manager, self.server_daemon)
        self.window.present()

    def do_shutdown(self):
        if self.server_daemon:
            self.server_daemon.stop()
        Adw.Application.do_shutdown(self)

    def _on_clear_action(self, action, param):
        if self.window:
            self.window.trigger_clear()

    def _on_docs_action(self, action, param):
        url = f"http://{self.config_manager.server.host}:{self.config_manager.server.port}/overlay"
        Gtk.show_uri(self.window, url, 0)

    def _on_about_action(self, action, param):
        about = Adw.AboutDialog(
            application_name="Yeet",
            application_icon="gay.geeks.Yeet",
            developer_name="Yeet Contributors",
            version="1.0.0",
            copyright="© 2026 Yeet Developers",
            license_type=Gtk.License.GPL_3_0,
            website="https://github.com/geeks/yeet",
            issue_url="https://github.com/geeks/yeet/issues",
            comments="Wayland-native interactive stream throwing system and physics overlay for OBS Studio adhering to GNOME Human Interface Guidelines."
        )
        about.present(self.window)
