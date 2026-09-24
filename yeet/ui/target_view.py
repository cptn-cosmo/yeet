"""
Yeet - Target Setup & Boundary Configuration View (Libadwaita)
App ID: gay.geeks.Yeet
"""

import uuid
from typing import Optional
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, GdkPixbuf

from ..config import ConfigManager
from ..models import Target
from .mapper_canvas import MapperCanvas

class TargetView(Adw.PreferencesPage):
    def __init__(self, config_manager: ConfigManager, on_targets_updated=None):
        super().__init__()
        self.config_manager = config_manager
        self.on_targets_updated = on_targets_updated
        self._updating_ui = False

        self.set_title("Targets")
        self.set_icon_name("mark-location-symbolic")

        # --- 1. Canvas Group ---
        canvas_group = Adw.PreferencesGroup()
        canvas_group.set_title("Coordinate Mapper")
        canvas_group.set_description("Configure normalized 2D collision boundaries. Drag center to move, corners to resize, top arm to rotate.")
        self.add(canvas_group)

        # Toolbar Box above Canvas
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.set_margin_bottom(8)

        # Add Target Menu
        add_btn = Gtk.MenuButton()
        add_btn.set_label("Add Target…")
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.add_css_class("suggested-action")

        menu = Gtk.PopoverMenu()
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        menu_box.set_margin_top(6)
        menu_box.set_margin_bottom(6)
        menu_box.set_margin_start(6)
        menu_box.set_margin_end(6)

        for shape_name, shape_id in [("Capsule / Pill (VTuber)", "capsule"), ("Rectangle / Box", "box"), ("Circle / Ellipse", "circle"), ("Custom Polygon", "polygon")]:
            btn = Gtk.Button(label=shape_name)
            btn.connect("clicked", lambda b, s=shape_id: self._on_add_target(s))
            menu_box.append(btn)
        popover = Gtk.Popover()
        popover.set_child(menu_box)
        add_btn.set_popover(popover)
        toolbar.append(add_btn)

        # Toggle Grid Checkbox
        grid_check = Gtk.CheckButton(label="Show Grid")
        grid_check.set_active(True)
        grid_check.connect("toggled", self._on_toggle_grid)
        toolbar.append(grid_check)

        # Toggle Trajectory Checkbox
        traj_check = Gtk.CheckButton(label="Show Trajectory")
        traj_check.set_active(True)
        traj_check.connect("toggled", self._on_toggle_trajectory)
        toolbar.append(traj_check)

        # Load Backdrop Screenshot
        backdrop_btn = Gtk.Button(label="Set Backdrop…")
        backdrop_btn.set_icon_name("image-x-generic-symbolic")
        backdrop_btn.connect("clicked", self._on_load_backdrop)
        toolbar.append(backdrop_btn)

        canvas_group.add(toolbar)

        # Canvas Frame
        frame = Gtk.Frame()
        frame.add_css_class("view")
        self.canvas = MapperCanvas(on_target_changed=self._on_canvas_target_changed)
        frame.set_child(self.canvas)
        canvas_group.add(frame)

        # --- 2. Selected Target Properties Group ---
        self.props_group = Adw.PreferencesGroup()
        self.props_group.set_title("Selected Target Properties")
        self.add(self.props_group)

        # Target Selector Dropdown
        self.target_selector = Adw.ComboRow()
        self.target_selector.set_title("Active Target")
        self.target_selector.connect("notify::selected", self._on_target_selection_changed)
        self.props_group.add(self.target_selector)

        # Target Name
        self.name_row = Adw.EntryRow()
        self.name_row.set_title("Target Label")
        self.name_row.connect("changed", self._on_prop_changed)
        self.props_group.add(self.name_row)

        # Shape Type Combo
        self.shape_model = Gtk.StringList.new(["Capsule (Pill)", "Box (Rectangle)", "Circle", "Polygon"])
        self.shape_row = Adw.ComboRow()
        self.shape_row.set_title("Collision Shape")
        self.shape_row.set_model(self.shape_model)
        self.shape_row.connect("notify::selected", self._on_shape_type_changed)
        self.props_group.add(self.shape_row)

        # Position X
        self.pos_x_row = Adw.SpinRow()
        self.pos_x_row.set_title("Position X (Normalized)")
        self.pos_x_row.set_subtitle("0.0 (Left) to 1.0 (Right)")
        self.pos_x_row.set_adjustment(Gtk.Adjustment(value=0.5, lower=0.0, upper=1.0, step_increment=0.01, page_increment=0.05))
        self.pos_x_row.set_digits(3)
        self.pos_x_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.pos_x_row)

        # Position Y
        self.pos_y_row = Adw.SpinRow()
        self.pos_y_row.set_title("Position Y (Normalized)")
        self.pos_y_row.set_subtitle("0.0 (Top) to 1.0 (Bottom)")
        self.pos_y_row.set_adjustment(Gtk.Adjustment(value=0.5, lower=0.0, upper=1.0, step_increment=0.01, page_increment=0.05))
        self.pos_y_row.set_digits(3)
        self.pos_y_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.pos_y_row)

        # Width
        self.width_row = Adw.SpinRow()
        self.width_row.set_title("Width (Normalized)")
        self.width_row.set_adjustment(Gtk.Adjustment(value=0.2, lower=0.02, upper=1.0, step_increment=0.01, page_increment=0.05))
        self.width_row.set_digits(3)
        self.width_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.width_row)

        # Height
        self.height_row = Adw.SpinRow()
        self.height_row.set_title("Height (Normalized)")
        self.height_row.set_adjustment(Gtk.Adjustment(value=0.3, lower=0.02, upper=1.0, step_increment=0.01, page_increment=0.05))
        self.height_row.set_digits(3)
        self.height_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.height_row)

        # Radius (for Circle)
        self.radius_row = Adw.SpinRow()
        self.radius_row.set_title("Radius (Normalized)")
        self.radius_row.set_adjustment(Gtk.Adjustment(value=0.1, lower=0.01, upper=0.5, step_increment=0.01, page_increment=0.05))
        self.radius_row.set_digits(3)
        self.radius_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.radius_row)

        # Rotation
        self.rotation_row = Adw.SpinRow()
        self.rotation_row.set_title("Rotation (Degrees)")
        self.rotation_row.set_adjustment(Gtk.Adjustment(value=0.0, lower=-180.0, upper=180.0, step_increment=1.0, page_increment=15.0))
        self.rotation_row.set_digits(1)
        self.rotation_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.rotation_row)

        # Bounciness (Restitution)
        self.bounce_row = Adw.SpinRow()
        self.bounce_row.set_title("Restitution (Bounciness)")
        self.bounce_row.set_subtitle("0.0 = Absorb all impact, 1.0 = Elastic super bounce")
        self.bounce_row.set_adjustment(Gtk.Adjustment(value=0.6, lower=0.0, upper=1.0, step_increment=0.05, page_increment=0.1))
        self.bounce_row.set_digits(2)
        self.bounce_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.bounce_row)

        # Delete Target Action Row
        self.delete_row = Adw.ActionRow()
        self.delete_row.set_title("Remove Target")
        del_btn = Gtk.Button(label="Delete")
        del_btn.add_css_class("destructive-action")
        del_btn.connect("clicked", self._on_delete_target)
        self.delete_row.add_suffix(del_btn)
        self.props_group.add(self.delete_row)

        # Initialize View
        self.refresh_from_config()

    def refresh_from_config(self):
        self._updating_ui = True
        targets = self.config_manager.targets
        names = [t.name for t in targets] if targets else ["No Targets"]
        model = Gtk.StringList.new(names)
        self.target_selector.set_model(model)

        selected_id = self.canvas.selected_target_id
        if not selected_id and targets:
            selected_id = targets[0].id

        self.canvas.set_targets(targets, selected_id)

        # Select corresponding index in combo
        for idx, t in enumerate(targets):
            if t.id == selected_id:
                self.target_selector.set_selected(idx)
                break

        self._update_property_controls()
        self._updating_ui = False

    def _update_property_controls(self):
        tgt = self.canvas.get_selected_target()
        if not tgt:
            self.props_group.set_sensitive(False)
            return

        self.props_group.set_sensitive(True)
        self._updating_ui = True

        self.name_row.set_text(tgt.name)
        type_indices = {"capsule": 0, "box": 1, "circle": 2, "polygon": 3}
        self.shape_row.set_selected(type_indices.get(tgt.type, 0))

        self.pos_x_row.set_value(tgt.x)
        self.pos_y_row.set_value(tgt.y)
        self.width_row.set_value(tgt.width)
        self.height_row.set_value(tgt.height)
        self.radius_row.set_value(tgt.radius)
        self.rotation_row.set_value(tgt.rotation)
        self.bounce_row.set_value(tgt.bounciness)

        # Visibility based on shape
        is_circle = (tgt.type == "circle")
        is_poly = (tgt.type == "polygon")
        self.radius_row.set_visible(is_circle)
        self.width_row.set_visible(not is_circle and not is_poly)
        self.height_row.set_visible(not is_circle and not is_poly)
        self.rotation_row.set_visible(not is_circle)

        self._updating_ui = False

    def _on_canvas_target_changed(self, target: Target):
        if not self._updating_ui:
            self._update_property_controls()
            self.config_manager.save()
            if self.on_targets_updated:
                self.on_targets_updated()

    def _on_target_selection_changed(self, row, pspec):
        if self._updating_ui:
            return
        idx = row.get_selected()
        if 0 <= idx < len(self.config_manager.targets):
            tgt = self.config_manager.targets[idx]
            self.canvas.select_target(tgt.id)
            self._update_property_controls()

    def _on_shape_type_changed(self, row, pspec):
        if self._updating_ui:
            return
        tgt = self.canvas.get_selected_target()
        if not tgt:
            return
        idx = row.get_selected()
        shape_types = ["capsule", "box", "circle", "polygon"]
        tgt.type = shape_types[idx]
        if tgt.type == "polygon" and not tgt.points:
            # Default triangle
            tgt.points = [
                [tgt.x, tgt.y - 0.15],
                [tgt.x - 0.12, tgt.y + 0.15],
                [tgt.x + 0.12, tgt.y + 0.15]
            ]
        self.canvas.queue_draw()
        self._update_property_controls()
        self.config_manager.save()
        if self.on_targets_updated:
            self.on_targets_updated()

    def _on_prop_changed(self, *args):
        if self._updating_ui:
            return
        tgt = self.canvas.get_selected_target()
        if not tgt:
            return

        tgt.name = self.name_row.get_text() or "Target"
        tgt.x = self.pos_x_row.get_value()
        tgt.y = self.pos_y_row.get_value()
        tgt.width = self.width_row.get_value()
        tgt.height = self.height_row.get_value()
        tgt.radius = self.radius_row.get_value()
        tgt.rotation = self.rotation_row.get_value()
        tgt.bounciness = self.bounce_row.get_value()

        self.canvas.queue_draw()
        self.config_manager.save()
        if self.on_targets_updated:
            self.on_targets_updated()

    def _on_add_target(self, shape_type: str):
        new_id = f"target_{uuid.uuid4().hex[:6]}"
        count = len(self.config_manager.targets) + 1
        name = f"Target {count}"
        points = []
        if shape_type == "polygon":
            points = [[0.5, 0.35], [0.4, 0.65], [0.6, 0.65]]

        new_target = Target(
            id=new_id,
            name=name,
            type=shape_type,
            x=0.5,
            y=0.5,
            width=0.2,
            height=0.3,
            radius=0.1,
            rotation=0.0,
            points=points,
            bounciness=0.6,
            friction=0.1
        )
        self.config_manager.targets.append(new_target)
        self.config_manager.save()
        self.refresh_from_config()
        self.canvas.select_target(new_id)
        if self.on_targets_updated:
            self.on_targets_updated()

    def _on_delete_target(self, btn):
        tgt = self.canvas.get_selected_target()
        if not tgt:
            return
        self.config_manager.targets = [t for t in self.config_manager.targets if t.id != tgt.id]
        self.config_manager.save()
        self.refresh_from_config()
        if self.on_targets_updated:
            self.on_targets_updated()

    def _on_toggle_grid(self, check):
        self.canvas.show_grid = check.get_active()
        self.canvas.queue_draw()

    def _on_toggle_trajectory(self, check):
        self.canvas.show_trajectory = check.get_active()
        self.canvas.queue_draw()

    def _on_load_backdrop(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Stream Screenshot or Avatar Image")
        filter_img = Gtk.FileFilter()
        filter_img.set_name("Images")
        filter_img.add_mime_type("image/png")
        filter_img.add_mime_type("image/jpeg")
        filter_img.add_mime_type("image/webp")
        dialog.open(self.get_root(), None, self._on_backdrop_file_selected)

    def _on_backdrop_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                # Load and scale to canvas resolution
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 640, 360, False)
                self.canvas.background_pixbuf = pixbuf
                self.canvas.queue_draw()
        except Exception as e:
            pass
