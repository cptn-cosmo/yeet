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
        self._updating_wh = False

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

        self.collisions_row = Adw.ActionRow()
        self.collisions_row.set_title("Total Collision Impacts")
        self.collisions_badge = Gtk.Label(label="0 hits")
        self.collisions_badge.add_css_class("accent")
        self.collisions_row.add_suffix(self.collisions_badge)
        self.status_group.add(self.collisions_row)

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

        # --- 3. Collision Webhooks (First & Last Hit) Group ---
        self.webhook_group = Adw.PreferencesGroup()
        self.webhook_group.set_title("Collision Webhooks (First and Last Hit)")
        self.webhook_group.set_description("Trigger external URLs on the initial impact and when the barrage settles (e.g. for VTube Studio expressions or lighting).")
        self.add(self.webhook_group)

        # Switch to enable webhooks
        self.webhook_switch = Adw.SwitchRow()
        self.webhook_switch.set_title("Enable Outbound Webhooks")
        self.webhook_switch.set_subtitle("Dispatches HTTP requests upon target collisions")
        self.webhook_switch.connect("notify::active", self._on_webhook_changed)
        self.webhook_group.add(self.webhook_switch)

        # First Hit URL
        self.first_url_row = Adw.EntryRow()
        self.first_url_row.set_title("First Hit URL")
        self.first_url_row.connect("changed", self._on_webhook_changed)
        self.webhook_group.add(self.first_url_row)

        # First Hit Method
        self.first_method_row = Adw.ComboRow()
        self.first_method_row.set_title("First Hit HTTP Method")
        self.first_method_row.set_model(Gtk.StringList.new(["GET", "POST"]))
        self.first_method_row.connect("notify::selected", self._on_webhook_changed)
        self.webhook_group.add(self.first_method_row)

        # Last Hit URL
        self.last_url_row = Adw.EntryRow()
        self.last_url_row.set_title("Last Hit URL")
        self.last_url_row.connect("changed", self._on_webhook_changed)
        self.webhook_group.add(self.last_url_row)

        # Last Hit Method
        self.last_method_row = Adw.ComboRow()
        self.last_method_row.set_title("Last Hit HTTP Method")
        self.last_method_row.set_model(Gtk.StringList.new(["GET", "POST"]))
        self.last_method_row.connect("notify::selected", self._on_webhook_changed)
        self.webhook_group.add(self.last_method_row)

        # Barrage Settling Delay
        self.delay_row = Adw.SpinRow()
        self.delay_row.set_title("Barrage Settling Delay (seconds)")
        self.delay_row.set_subtitle("Quiet period after a collision before triggering the Last Hit URL")
        self.delay_row.set_adjustment(Gtk.Adjustment(value=2.0, lower=0.5, upper=10.0, step_increment=0.5, page_increment=1.0))
        self.delay_row.set_digits(1)
        self.delay_row.connect("notify::value", self._on_webhook_changed)
        self.webhook_group.add(self.delay_row)

        # Webhook Testing Action Row
        wh_test_row = Adw.ActionRow()
        wh_test_row.set_title("Test Webhook Triggers")
        wh_test_row.set_subtitle("Supports {target}, {item}, and {hits} URL replacements")

        first_test_btn = Gtk.Button(label="Test First Hit")
        first_test_btn.set_icon_name("media-playback-start-symbolic")
        first_test_btn.connect("clicked", lambda b: self._test_webhook("first_hit"))
        wh_test_row.add_suffix(first_test_btn)

        last_test_btn = Gtk.Button(label="Test Last Hit")
        last_test_btn.set_icon_name("media-playback-stop-symbolic")
        last_test_btn.connect("clicked", lambda b: self._test_webhook("last_hit"))
        wh_test_row.add_suffix(last_test_btn)

        self.webhook_group.add(wh_test_row)

        # --- 4. REST API & Bot Integration Documentation ---
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

        # GET /api/v1/throw (Random Mix, Groups and Exclusions) Expander
        mix_exp = Adw.ExpanderRow()
        mix_exp.set_title("GET /api/v1/throw (Random Mix, Groups and Exclusions)")
        mix_exp.set_subtitle("Barrage where each item is selected randomly from a pool or group with exclusions")

        mix_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        mix_box.set_margin_top(8)
        mix_box.set_margin_bottom(8)
        mix_box.set_margin_start(16)
        mix_box.set_margin_end(16)

        curl_mix = 'curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&items=all&item_exclude=winter&amount=5"'
        mix_lbl = Gtk.Label(label=curl_mix, xalign=0)
        mix_lbl.add_css_class("monospace")
        mix_lbl.set_selectable(True)
        mix_box.append(mix_lbl)

        mix_copy_btn = Gtk.Button(label="Copy Random Mix Request")
        mix_copy_btn.set_icon_name("edit-copy-symbolic")
        mix_copy_btn.connect("clicked", lambda b: self._copy_to_clipboard(curl_mix))
        mix_box.append(mix_copy_btn)

        mix_exp.add_row(mix_box)
        api_group.add(mix_exp)

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

        # GET /api/v1/collision Expander
        coll_trigger_exp = Adw.ExpanderRow()
        coll_trigger_exp.set_title("GET /api/v1/collision (Trigger Direct Hit)")
        coll_trigger_exp.set_subtitle("Simulate an immediate impact/bonk sound and visual burst on an avatar target")

        coll_trigger_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        coll_trigger_box.set_margin_top(8)
        coll_trigger_box.set_margin_bottom(8)
        coll_trigger_box.set_margin_start(16)
        coll_trigger_box.set_margin_end(16)

        curl_coll_trigger = 'curl "http://127.0.0.1:49122/api/v1/collision?target=VTuber+Head&item=beachball&sound=pop"'
        coll_trigger_lbl = Gtk.Label(label=curl_coll_trigger, xalign=0)
        coll_trigger_lbl.add_css_class("monospace")
        coll_trigger_lbl.set_selectable(True)
        coll_trigger_box.append(coll_trigger_lbl)

        coll_trigger_copy_btn = Gtk.Button(label="Copy GET Collision Request")
        coll_trigger_copy_btn.set_icon_name("edit-copy-symbolic")
        coll_trigger_copy_btn.connect("clicked", lambda b: self._copy_to_clipboard(curl_coll_trigger))
        coll_trigger_box.append(coll_trigger_copy_btn)

        coll_trigger_exp.add_row(coll_trigger_box)
        api_group.add(coll_trigger_exp)

        # GET /api/v1/collisions Expander
        coll_stats_exp = Adw.ExpanderRow()
        coll_stats_exp.set_title("GET /api/v1/collisions (Query Hit Statistics)")
        coll_stats_exp.set_subtitle("Retrieve total collision count, breakdown by target, and recent hits log")

        coll_stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        coll_stats_box.set_margin_top(8)
        coll_stats_box.set_margin_bottom(8)
        coll_stats_box.set_margin_start(16)
        coll_stats_box.set_margin_end(16)

        curl_coll_stats = 'curl http://127.0.0.1:49122/api/v1/collisions'
        coll_stats_lbl = Gtk.Label(label=curl_coll_stats, xalign=0)
        coll_stats_lbl.add_css_class("monospace")
        coll_stats_lbl.set_selectable(True)
        coll_stats_box.append(coll_stats_lbl)

        coll_stats_copy_btn = Gtk.Button(label="Copy curl Command")
        coll_stats_copy_btn.set_icon_name("edit-copy-symbolic")
        coll_stats_copy_btn.connect("clicked", lambda b: self._copy_to_clipboard(curl_coll_stats))
        coll_stats_box.append(coll_stats_copy_btn)

        coll_stats_exp.add_row(coll_stats_box)
        api_group.add(coll_stats_exp)

        # Refresh URL
        self.update_url_display()

    def get_overlay_url(self) -> str:
        s = self.config_manager.server
        return f"http://{s.host}:{s.port}/overlay"

    def update_url_display(self):
        url = self.get_overlay_url()
        self.url_row.set_subtitle(url)
        self.port_row.set_value(self.config_manager.server.port)
        self._refresh_webhooks()

    def _refresh_webhooks(self):
        wh = self.config_manager.webhooks
        self._updating_wh = True
        try:
            self.webhook_switch.set_active(wh.enabled)
            self.first_url_row.set_text(wh.first_hit_url or "")
            self.first_method_row.set_selected(0 if (wh.first_hit_method or "GET").upper() == "GET" else 1)
            self.last_url_row.set_text(wh.last_hit_url or "")
            self.last_method_row.set_selected(0 if (wh.last_hit_method or "GET").upper() == "GET" else 1)
            self.delay_row.set_value(wh.settling_delay or 2.0)
        finally:
            self._updating_wh = False

    def _on_webhook_changed(self, *args):
        if self._updating_wh:
            return
        wh = self.config_manager.webhooks
        wh.enabled = self.webhook_switch.get_active()
        wh.first_hit_url = self.first_url_row.get_text().strip()
        wh.first_hit_method = "GET" if self.first_method_row.get_selected() == 0 else "POST"
        wh.last_hit_url = self.last_url_row.get_text().strip()
        wh.last_hit_method = "GET" if self.last_method_row.get_selected() == 0 else "POST"
        wh.settling_delay = float(self.delay_row.get_value())
        self.config_manager.save()

    def _test_webhook(self, event_type: str):
        port = self.config_manager.server.port
        url = f"http://127.0.0.1:{port}/api/v1/webhooks/test?event={event_type}"

        def _worker():
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "Yeet-App"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    pass
                GLib.idle_add(self._notify_test_result, event_type, True)
            except Exception as e:
                GLib.idle_add(self._notify_test_result, event_type, False, str(e))

        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def _notify_test_result(self, event_type: str, success: bool, err_msg: str = ""):
        event_name = "First Hit" if event_type == "first_hit" else "Last Hit"
        root = self.get_root()
        if success:
            msg = f"Dispatched {event_name} test webhook!"
        else:
            msg = f"Failed to test {event_name}: {err_msg}"
        if root and hasattr(root, "show_toast"):
            root.show_toast(msg)

    def update_connected_clients(self, count: int):
        self.clients_badge.set_text(f"{count} active")

    def update_collision_count(self, count: int):
        self.collisions_badge.set_text(f"{count} hits")

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

