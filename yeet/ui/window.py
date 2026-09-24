"""
Yeet - Main Application Window (Libadwaita)
App ID: gay.geeks.Yeet
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, Gio, GObject

from ..config import ConfigManager
from ..server import ServerDaemon
from .target_view import TargetView
from .items_view import ItemsView
from .physics_view import PhysicsView
from .server_view import ServerView

class YeetWindow(Adw.ApplicationWindow):
    def __init__(self, app, config_manager: ConfigManager, server_daemon: ServerDaemon):
        super().__init__(application=app, title="Yeet")
        self.config_manager = config_manager
        self.server_daemon = server_daemon

        self.set_default_size(960, 720)
        self.set_size_request(600, 500)

        # Main Toast Overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        # Outer Box
        outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(outer_box)

        # Header Bar
        header_bar = Adw.HeaderBar()
        outer_box.append(header_bar)

        # Header Title with View Switcher
        self.view_stack = Adw.ViewStack()
        view_switcher_title = Adw.ViewSwitcherTitle()
        view_switcher_title.set_stack(self.view_stack)
        view_switcher_title.set_title("Yeet")
        view_switcher_title.set_subtitle("Stream Throwing System")
        header_bar.set_title_widget(view_switcher_title)

        # One-Click Copy OBS URL Button
        copy_url_btn = Gtk.Button()
        copy_url_btn.set_icon_name("edit-copy-symbolic")
        copy_url_btn.set_tooltip_text("Copy OBS Browser Source URL to Clipboard")
        copy_url_btn.connect("clicked", self._on_copy_obs_url)
        header_bar.pack_start(copy_url_btn)

        # Quick Test Throw Action Button
        test_throw_btn = Gtk.Button()
        test_throw_btn.set_icon_name("media-playback-start-symbolic")
        test_throw_btn.set_tooltip_text("Launch Quick Test Throw")
        test_throw_btn.add_css_class("suggested-action")
        test_throw_btn.connect("clicked", self._on_quick_test_throw)
        header_bar.pack_start(test_throw_btn)

        # Server Status Pill Badge
        self.server_badge = Gtk.Label()
        self.server_badge.add_css_class("success")
        self.server_badge.add_css_class("caption")
        self._update_server_badge()
        header_bar.pack_end(self.server_badge)

        # Primary App Menu
        menu = Gio.Menu()
        menu.append("Clear Canvas", "app.clear_canvas")
        menu.append("Documentation", "app.documentation")
        menu.append("About Yeet", "app.about")
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_menu_model(menu)
        header_bar.pack_end(menu_btn)

        # Setup Views
        self.target_view = TargetView(
            config_manager=self.config_manager,
            on_targets_updated=self._on_targets_updated
        )
        self.items_view = ItemsView(
            config_manager=self.config_manager,
            on_items_updated=self._on_items_updated,
            on_test_throw=self.trigger_throw
        )
        self.physics_view = PhysicsView(
            config_manager=self.config_manager,
            on_physics_updated=self._on_physics_updated,
            on_test_throw=self.trigger_throw,
            on_clear_canvas=self.trigger_clear
        )
        self.server_view = ServerView(
            config_manager=self.config_manager,
            on_copy_url=self._on_url_copied,
            on_clear_canvas=self.trigger_clear
        )

        # Add pages to ViewStack
        page1 = self.view_stack.add_titled(self.target_view, "targets", "Targets")
        page1.set_icon_name("mark-location-symbolic")

        page2 = self.view_stack.add_titled(self.items_view, "items", "Items")
        page2.set_icon_name("package-x-generic-symbolic")

        page3 = self.view_stack.add_titled(self.physics_view, "physics", "Physics and Spawns")
        page3.set_icon_name("applications-games-symbolic")

        page4 = self.view_stack.add_titled(self.server_view, "server", "OBS and Server")
        page4.set_icon_name("network-server-symbolic")

        outer_box.append(self.view_stack)

        # Bottom View Switcher Bar for compact/mobile viewports
        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(self.view_stack)
        view_switcher_title.bind_property(
            "title-visible",
            switcher_bar,
            "reveal",
            GObject.BindingFlags.SYNC_CREATE
        )
        outer_box.append(switcher_bar)

        # Periodic timer for status & connected client counts
        GLib.timeout_add_seconds(2, self._on_periodic_status_update)

    def show_toast(self, text: str):
        toast = Adw.Toast.new(text)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

    def _update_server_badge(self):
        port = self.config_manager.server.port
        count = self.server_daemon.get_connected_count()
        if count > 0:
            self.server_badge.set_text(f"● OBS Connected ({count})")
            self.server_badge.remove_css_class("dim-label")
            self.server_badge.add_css_class("success")
        else:
            self.server_badge.set_text(f"● Ready :{port}")
            self.server_badge.remove_css_class("dim-label")
            self.server_badge.add_css_class("accent")

    def _on_periodic_status_update(self) -> bool:
        self._update_server_badge()
        count = self.server_daemon.get_connected_count()
        self.server_view.update_connected_clients(count)
        return True

    def _on_copy_obs_url(self, btn):
        url = self.server_view.get_overlay_url()
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(url)
        self.show_toast("OBS Browser Source URL copied to clipboard!")

    def _on_url_copied(self, url: str):
        self.show_toast("Copied to clipboard!")

    def _on_quick_test_throw(self, btn):
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
        self.show_toast(f"Thrown {amount} × {item_id}!")

    def trigger_clear(self):
        self.server_daemon.threadsafe_clear()
        self.show_toast("OBS Overlay cleared!")

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
        self.target_view.canvas.set_spawn_direction(self.config_manager.physics.default_spawn_direction)
