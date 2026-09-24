"""
Yeet - Spawn & Physics Rules View (Libadwaita)
App ID: gay.geeks.Yeet
"""

from typing import Optional
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from ..config import ConfigManager

class PhysicsView(Adw.PreferencesPage):
    def __init__(self, config_manager: ConfigManager, on_physics_updated=None, on_test_throw=None, on_clear_canvas=None):
        super().__init__()
        self.config_manager = config_manager
        self.on_physics_updated = on_physics_updated
        self.on_test_throw = on_test_throw
        self.on_clear_canvas = on_clear_canvas
        self._updating_ui = False

        self.set_title("Physics and Spawns")
        self.set_icon_name("applications-games-symbolic")

        # --- 1. Spawn Rules Group ---
        spawn_group = Adw.PreferencesGroup()
        spawn_group.set_title("Spawn Behaviors and Trajectories")
        spawn_group.set_description("Control spawn locations, ballistic targeting, and barrage spread.")
        self.add(spawn_group)

        # Default Spawn Direction Combo
        self.spawn_directions = ["random", "left", "right", "top", "bottom", "aimed", "rain", "spray"]
        dir_labels = [
            "Random Screen Edge",
            "Left Edge (Shoots Right)",
            "Right Edge (Shoots Left)",
            "Top Edge (Falls Down)",
            "Bottom Edge (Shoots Up)",
            "Aimed Arc (Direct at Avatar Target)",
            "Rain / Dropping (Top Grid)",
            "Point-Source Spray (Custom Emitter)"
        ]
        self.dir_model = Gtk.StringList.new(dir_labels)
        self.dir_row = Adw.ComboRow()
        self.dir_row.set_title("Default Spawn Mode")
        self.dir_row.set_model(self.dir_model)
        self.dir_row.connect("notify::selected", self._on_spawn_dir_changed)
        spawn_group.add(self.dir_row)

        # Default Force (Velocity Multiplier)
        self.force_row = Adw.SpinRow()
        self.force_row.set_title("Launch Velocity Multiplier")
        self.force_row.set_subtitle("Scales projectile velocity when thrown")
        self.force_row.set_adjustment(Gtk.Adjustment(value=1.0, lower=0.2, upper=3.5, step_increment=0.1, page_increment=0.5))
        self.force_row.set_digits(2)
        self.force_row.connect("notify::value", self._on_physics_changed)
        spawn_group.add(self.force_row)

        # Spread Variance
        self.spread_row = Adw.SpinRow()
        self.spread_row.set_title("Spread Angle Variance (Degrees)")
        self.spread_row.set_subtitle("Angle deviation for projectile barrages")
        self.spread_row.set_adjustment(Gtk.Adjustment(value=15.0, lower=0.0, upper=90.0, step_increment=2.5, page_increment=10.0))
        self.spread_row.set_digits(1)
        self.spread_row.connect("notify::value", self._on_physics_changed)
        spawn_group.add(self.spread_row)

        # Spray Emitter Controls
        self.spray_group = Adw.PreferencesGroup()
        self.spray_group.set_title("Point-Source Spray Emitter")
        self.spray_group.set_description("Origin coordinates and launch angle when using Point-Source Spray mode.")
        self.add(self.spray_group)

        self.spray_x_row = Adw.SpinRow()
        self.spray_x_row.set_title("Emitter Origin X (Normalized)")
        self.spray_x_row.set_adjustment(Gtk.Adjustment(value=0.0, lower=0.0, upper=1.0, step_increment=0.05, page_increment=0.1))
        self.spray_x_row.set_digits(2)
        self.spray_x_row.connect("notify::value", self._on_spray_changed)
        self.spray_group.add(self.spray_x_row)

        self.spray_y_row = Adw.SpinRow()
        self.spray_y_row.set_title("Emitter Origin Y (Normalized)")
        self.spray_y_row.set_adjustment(Gtk.Adjustment(value=0.5, lower=0.0, upper=1.0, step_increment=0.05, page_increment=0.1))
        self.spray_y_row.set_digits(2)
        self.spray_y_row.connect("notify::value", self._on_spray_changed)
        self.spray_group.add(self.spray_y_row)

        self.spray_angle_row = Adw.SpinRow()
        self.spray_angle_row.set_title("Spray Emitter Angle (Degrees)")
        self.spray_angle_row.set_subtitle("0° = Right, 90° = Down, 180° = Left, 270° = Up")
        self.spray_angle_row.set_adjustment(Gtk.Adjustment(value=0.0, lower=-180.0, upper=180.0, step_increment=5.0, page_increment=15.0))
        self.spray_angle_row.set_digits(1)
        self.spray_angle_row.connect("notify::value", self._on_spray_changed)
        self.spray_group.add(self.spray_angle_row)

        # --- 2. World Physics & Audio Limiter Group ---
        world_group = Adw.PreferencesGroup()
        world_group.set_title("World Physics and Performance")
        self.add(world_group)

        # World Gravity Y
        self.grav_y_row = Adw.SpinRow()
        self.grav_y_row.set_title("World Vertical Gravity (Y)")
        self.grav_y_row.set_subtitle("1.0 = Standard downward gravity, 0.0 = Zero-G space, -1.0 = Upward float")
        self.grav_y_row.set_adjustment(Gtk.Adjustment(value=1.0, lower=-2.0, upper=3.0, step_increment=0.1, page_increment=0.5))
        self.grav_y_row.set_digits(2)
        self.grav_y_row.connect("notify::value", self._on_gravity_changed)
        world_group.add(self.grav_y_row)

        # Sound Debounce Limiter
        self.debounce_row = Adw.SpinRow()
        self.debounce_row.set_title("Sound Debounce / Audio Limiter (ms)")
        self.debounce_row.set_subtitle("Minimum interval between impact sounds to prevent clipping during barrages")
        self.debounce_row.set_adjustment(Gtk.Adjustment(value=50, lower=10, upper=250, step_increment=10, page_increment=25))
        self.debounce_row.set_digits(0)
        self.debounce_row.connect("notify::value", self._on_physics_changed)
        world_group.add(self.debounce_row)

        # Max Active Items
        self.max_items_row = Adw.SpinRow()
        self.max_items_row.set_title("Max Simultaneous Items on Canvas")
        self.max_items_row.set_subtitle("Recycles oldest items to maintain a smooth 60 FPS in OBS")
        self.max_items_row.set_adjustment(Gtk.Adjustment(value=120, lower=20, upper=300, step_increment=10, page_increment=20))
        self.max_items_row.set_digits(0)
        self.max_items_row.connect("notify::value", self._on_physics_changed)
        world_group.add(self.max_items_row)

        # Overlay Wireframe Target Debug Toggle
        self.debug_row = Adw.SwitchRow()
        self.debug_row.set_title("Show Target Boundaries in OBS")
        self.debug_row.set_subtitle("Renders visual collider wireframes in the OBS overlay to help align with your stream avatar")
        self.debug_row.connect("notify::active", self._on_debug_toggled)
        world_group.add(self.debug_row)

        # --- 3. Test Throw Playground ---
        test_group = Adw.PreferencesGroup()
        test_group.set_title("Test Throw Playground")
        test_group.set_description("Instantly test throwing items into your live OBS overlay.")
        self.add(test_group)

        # Item Selector
        self.test_item_combo = Adw.ComboRow()
        self.test_item_combo.set_title("Throw Item")
        test_group.add(self.test_item_combo)

        # Amount
        self.test_amount_row = Adw.SpinRow()
        self.test_amount_row.set_title("Throw Amount")
        self.test_amount_row.set_adjustment(Gtk.Adjustment(value=5, lower=1, upper=50, step_increment=1, page_increment=5))
        self.test_amount_row.set_digits(0)
        test_group.add(self.test_amount_row)

        # Test Actions Row
        test_action_row = Adw.ActionRow()
        test_action_row.set_title("Trigger Actions")

        launch_btn = Gtk.Button(label="Launch Throw!")
        launch_btn.set_icon_name("media-playback-start-symbolic")
        launch_btn.add_css_class("suggested-action")
        launch_btn.add_css_class("pill")
        launch_btn.connect("clicked", self._on_launch_test)
        test_action_row.add_suffix(launch_btn)

        clear_btn = Gtk.Button(label="Clear Canvas")
        clear_btn.set_icon_name("edit-clear-symbolic")
        clear_btn.add_css_class("destructive-action")
        clear_btn.connect("clicked", self._on_clear_test)
        test_action_row.add_suffix(clear_btn)

        test_group.add(test_action_row)

        # Initialize
        self.refresh_from_config()

    def refresh_from_config(self):
        self._updating_ui = True
        p = self.config_manager.physics

        if p.default_spawn_direction in self.spawn_directions:
            self.dir_row.set_selected(self.spawn_directions.index(p.default_spawn_direction))
        else:
            self.dir_row.set_selected(0)

        self.force_row.set_value(p.default_force)
        self.spread_row.set_value(p.default_spread)
        self.spray_x_row.set_value(p.spawn_point[0] if len(p.spawn_point) > 0 else 0.0)
        self.spray_y_row.set_value(p.spawn_point[1] if len(p.spawn_point) > 1 else 0.5)
        self.spray_angle_row.set_value(p.spray_angle)

        self.grav_y_row.set_value(p.gravity[1] if len(p.gravity) > 1 else 1.0)
        self.debounce_row.set_value(p.sound_debounce_ms)
        self.max_items_row.set_value(p.max_active_items)
        self.debug_row.set_active(p.debug_boundaries)

        # Update test item combo
        items_list = list(self.config_manager.items.values())
        names = [f"{it.name} [{it.group}]" if it.group else it.name for it in items_list] if items_list else []
        self.test_item_combo.set_model(Gtk.StringList.new(["🎲 Random Item", "🔀 Random Mix (All Items)"] + names))

        self._updating_ui = False

    def _on_spawn_dir_changed(self, row, pspec):
        if self._updating_ui:
            return
        idx = row.get_selected()
        self.config_manager.physics.default_spawn_direction = self.spawn_directions[idx]
        self.config_manager.save()
        if self.on_physics_updated:
            self.on_physics_updated()

    def _on_physics_changed(self, *args):
        if self._updating_ui:
            return
        p = self.config_manager.physics
        p.default_force = self.force_row.get_value()
        p.default_spread = self.spread_row.get_value()
        p.sound_debounce_ms = int(self.debounce_row.get_value())
        p.max_active_items = int(self.max_items_row.get_value())
        self.config_manager.save()
        if self.on_physics_updated:
            self.on_physics_updated()

    def _on_spray_changed(self, *args):
        if self._updating_ui:
            return
        p = self.config_manager.physics
        p.spawn_point = [self.spray_x_row.get_value(), self.spray_y_row.get_value()]
        p.spray_angle = self.spray_angle_row.get_value()
        self.config_manager.save()
        if self.on_physics_updated:
            self.on_physics_updated()

    def _on_gravity_changed(self, *args):
        if self._updating_ui:
            return
        self.config_manager.physics.gravity = [0.0, self.grav_y_row.get_value()]
        self.config_manager.save()
        if self.on_physics_updated:
            self.on_physics_updated()

    def _on_debug_toggled(self, row, pspec):
        if self._updating_ui:
            return
        self.config_manager.physics.debug_boundaries = self.debug_row.get_active()
        self.config_manager.save()
        if self.on_physics_updated:
            self.on_physics_updated()

    def _on_launch_test(self, btn):
        idx = self.test_item_combo.get_selected()
        items_list = list(self.config_manager.items.values())

        if idx == 0 or not items_list:
            item_id = "random"
        elif idx == 1:
            item_id = "random_mix"
        else:
            item_id = items_list[idx - 2].id

        amount = int(self.test_amount_row.get_value())
        dir_idx = self.dir_row.get_selected()
        direction = self.spawn_directions[dir_idx]
        force = self.force_row.get_value()
        spread = self.spread_row.get_value()

        if self.on_test_throw:
            self.on_test_throw(item_id, amount, direction, force, spread)

    def _on_clear_test(self, btn):
        if self.on_clear_canvas:
            self.on_clear_canvas()
