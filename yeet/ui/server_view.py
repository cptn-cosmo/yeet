"""
Yeet - Server & OBS Integration View (Libadwaita)
App ID: gay.geeks.Yeet
"""

from typing import Optional, Callable
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk

from ..config import ConfigManager

class ServerView(Adw.PreferencesPage):
    def __init__(self, config_manager: ConfigManager, on_copy_url: Optional[Callable[[str], None]] = None, on_clear_canvas=None):
        super().__init__()
        self.config_manager = config_manager
        self.on_copy_url = on_copy_url
        self.on_clear_canvas = on_clear_canvas

        self.set_title("OBS and Server")
        self.set_icon_name("network-server-symbolic")

        # --- 1. OBS Browser Source Setup Group ---
        obs_group = Adw.PreferencesGroup()
        obs_group.set_title("OBS Studio Browser Source")
        obs_group.set_description("Add this URL as a Browser Source inside OBS Studio to display the physics overlay.")
        self.add(obs_group)

        # URL Card Row
        self.url_row = Adw.ActionRow()
        self.url_row.set_title("Browser Source URL")
        self.url_row.add_css_class("property")

        copy_btn = Gtk.Button(label="Copy URL")
        copy_btn.set_icon_name("edit-copy-symbolic")
        copy_btn.add_css_class("suggested-action")
        copy_btn.connect("clicked", self._on_copy_url_clicked)
        self.url_row.add_suffix(copy_btn)

        open_btn = Gtk.Button(label="Open in Browser")
        open_btn.set_icon_name("web-browser-symbolic")
        open_btn.connect("clicked", self._on_open_browser_clicked)
        self.url_row.add_suffix(open_btn)

        obs_group.add(self.url_row)

        # Recommended OBS Settings Info Row
        obs_setup_row = Adw.ExpanderRow()
        obs_setup_row.set_title("Recommended OBS Studio Source Settings")
        obs_setup_row.set_subtitle("Click to view optimal canvas, frame rate, and visibility settings")
        obs_setup_row.set_icon_name("help-about-symbolic")

        tip_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        tip_box.set_margin_top(8)
        tip_box.set_margin_bottom(8)
        tip_box.set_margin_start(16)
        tip_box.set_margin_end(16)

        tips = [
            "• Width and Height: 1920 × 1080 (or match your base stream canvas)",
            "• Custom Frame Rate: Checked, set to 60 FPS for buttery physics",
            "• Control Audio via OBS: Optional (overlay plays audio natively via browser)",
            "• Shutdown source when not visible: UNCHECKED (to maintain persistent WebSocket)",
            "• Refresh browser when scene becomes active: UNCHECKED"
        ]
        for t in tips:
            lbl = Gtk.Label(label=t, xalign=0)
            lbl.add_css_class("dim-label")
            tip_box.append(lbl)

        obs_setup_row.add_row(tip_box)
        obs_group.add(obs_setup_row)

        # --- 2. Live Daemon Status Group ---
        self.status_group = Adw.PreferencesGroup()
        self.status_group.set_title("Local Daemon Status")
        self.add(self.status_group)

        # Status & Overlays Count Row
        self.status_row = Adw.ActionRow()
        self.status_row.set_title("Daemon Status")
        self.status_badge = Gtk.Label(label="Running")
        self.status_badge.add_css_class("success")
        self.status_row.add_suffix(self.status_badge)
        self.status_group.add(self.status_row)

        self.clients_row = Adw.ActionRow()
        self.clients_row.set_title("Connected OBS Overlays")
        self.clients_badge = Gtk.Label(label="0 active")
        self.clients_badge.add_css_class("accent")
        self.clients_row.add_suffix(self.clients_badge)
        self.status_group.add(self.clients_row)

        # Server Port Row
        self.port_row = Adw.SpinRow()
        self.port_row.set_title("HTTP / WebSocket Port")
        self.port_row.set_subtitle("Default: 49122")
        self.port_row.set_adjustment(Gtk.Adjustment(value=49122, lower=1024, upper=65535, step_increment=1, page_increment=100))
        self.port_row.set_digits(0)
        self.port_row.connect("notify::value", self._on_port_changed)
        self.status_group.add(self.port_row)

        # Clear Canvas Button
        clear_row = Adw.ActionRow()
        clear_row.set_title("Emergency Overlay Reset")
        clear_row.set_subtitle("Clears all active physics bodies from all connected browser sources")
        clear_btn = Gtk.Button(label="Clear Canvas")
        clear_btn.set_icon_name("edit-clear-symbolic")
        clear_btn.add_css_class("destructive-action")
        clear_btn.connect("clicked", lambda b: self.on_clear_canvas() if self.on_clear_canvas else None)
        clear_row.add_suffix(clear_btn)
        self.status_group.add(clear_row)

        # --- 3. REST API & Bot Integration Documentation ---
        api_group = Adw.PreferencesGroup()
        api_group.set_title("REST API and Bot Triggers")
        api_group.set_description("Control Yeet programmatically using Streamer.bot, MixItUp, SAMMI, or curl.")
        self.add(api_group)

        # POST /api/v1/throw Expander (JSON)
        throw_exp = Adw.ExpanderRow()
        throw_exp.set_title("POST /api/v1/throw (JSON Body)")
        throw_exp.set_subtitle("Spawn items using JSON payload (for Streamer.bot, webhooks, or scripts)")

        throw_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        throw_box.set_margin_top(8)
        throw_box.set_margin_bottom(8)
        throw_box.set_margin_start(16)
        throw_box.set_margin_end(16)

        curl_throw = (
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
        curl_lbl = Gtk.Label(label=curl_throw, xalign=0)
        curl_lbl.add_css_class("monospace")
        curl_lbl.set_selectable(True)
        throw_box.append(curl_lbl)

        throw_copy_btn = Gtk.Button(label="Copy curl Command")
        throw_copy_btn.set_icon_name("edit-copy-symbolic")
        throw_copy_btn.connect("clicked", lambda b: self._copy_to_clipboard(curl_throw))
        throw_box.append(throw_copy_btn)

        throw_exp.add_row(throw_box)
        api_group.add(throw_exp)

        # GET /api/v1/throw Expander (URL Query Parameters)
        query_exp = Adw.ExpanderRow()
        query_exp.set_title("GET /api/v1/throw (URL Query Parameters)")
        query_exp.set_subtitle("Trigger throws directly via URL parameters in browser links, Nightbot, or GET requests")

        query_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        query_box.set_margin_top(8)
        query_box.set_margin_bottom(8)
        query_box.set_margin_start(16)
        query_box.set_margin_end(16)

        curl_query = 'curl "http://127.0.0.1:49122/api/v1/throw?item=beachball&amount=3&spawn_direction=rain&force=1.2"'
        query_lbl = Gtk.Label(label=curl_query, xalign=0)
        query_lbl.add_css_class("monospace")
        query_lbl.set_selectable(True)
        query_box.append(query_lbl)

        query_copy_btn = Gtk.Button(label="Copy GET Request")
        query_copy_btn.set_icon_name("edit-copy-symbolic")
        query_copy_btn.connect("clicked", lambda b: self._copy_to_clipboard(curl_query))
        query_box.append(query_copy_btn)

        query_exp.add_row(query_box)
        api_group.add(query_exp)

        # POST /api/v1/clear Expander
        clear_exp = Adw.ExpanderRow()
        clear_exp.set_title("POST /api/v1/clear")
        clear_exp.set_subtitle("Removes all active bodies immediately from the overlay")

        clear_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        clear_box.set_margin_top(8)
        clear_box.set_margin_bottom(8)
        clear_box.set_margin_start(16)
        clear_box.set_margin_end(16)

        curl_clear = 'curl -X POST http://127.0.0.1:49122/api/v1/clear'
        clear_lbl = Gtk.Label(label=curl_clear, xalign=0)
        clear_lbl.add_css_class("monospace")
        clear_lbl.set_selectable(True)
        clear_box.append(clear_lbl)

        clear_copy_btn = Gtk.Button(label="Copy curl Command")
        clear_copy_btn.set_icon_name("edit-copy-symbolic")
        clear_copy_btn.connect("clicked", lambda b: self._copy_to_clipboard(curl_clear))
        clear_box.append(clear_copy_btn)

        clear_exp.add_row(clear_box)
        api_group.add(clear_exp)

        # GET /api/v1/items Expander
        items_exp = Adw.ExpanderRow()
        items_exp.set_title("GET /api/v1/items")
        items_exp.set_subtitle("List configured items and their metadata")

        items_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        items_box.set_margin_top(8)
        items_box.set_margin_bottom(8)
        items_box.set_margin_start(16)
        items_box.set_margin_end(16)

        curl_items = 'curl http://127.0.0.1:49122/api/v1/items'
        items_lbl = Gtk.Label(label=curl_items, xalign=0)
        items_lbl.add_css_class("monospace")
        items_lbl.set_selectable(True)
        items_box.append(items_lbl)

        items_exp.add_row(items_box)
        api_group.add(items_exp)

        # GET /api/v1/status Expander
        status_exp = Adw.ExpanderRow()
        status_exp.set_title("GET /api/v1/status")
        status_exp.set_subtitle("Health check, daemon uptime, and connected OBS overlay count")

        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        status_box.set_margin_top(8)
        status_box.set_margin_bottom(8)
        status_box.set_margin_start(16)
        status_box.set_margin_end(16)

        curl_status = 'curl http://127.0.0.1:49122/api/v1/status'
        status_api_lbl = Gtk.Label(label=curl_status, xalign=0)
        status_api_lbl.add_css_class("monospace")
        status_api_lbl.set_selectable(True)
        status_box.append(status_api_lbl)

        status_exp.add_row(status_box)
        api_group.add(status_exp)

        # Refresh URL
        self.update_url_display()

    def get_overlay_url(self) -> str:
        s = self.config_manager.server
        return f"http://{s.host}:{s.port}/overlay"

    def update_url_display(self):
        url = self.get_overlay_url()
        self.url_row.set_subtitle(url)
        self.port_row.set_value(self.config_manager.server.port)

    def update_connected_clients(self, count: int):
        self.clients_badge.set_text(f"{count} active")

    def _on_port_changed(self, row, pspec):
        val = int(self.port_row.get_value())
        if val != self.config_manager.server.port:
            self.config_manager.server.port = val
            self.config_manager.save()
            self.update_url_display()

    def _copy_to_clipboard(self, text: str):
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(text)
        if self.on_copy_url:
            self.on_copy_url(text)

    def _on_copy_url_clicked(self, btn):
        self._copy_to_clipboard(self.get_overlay_url())

    def _on_open_browser_clicked(self, btn):
        url = self.get_overlay_url()
        Gtk.show_uri(self.get_root(), url, Gdk.CURRENT_TIME)
