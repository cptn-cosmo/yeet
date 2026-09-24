"""
Yeet - Throwable Items Management View (Libadwaita)
App ID: gay.geeks.Yeet
"""

import os
import shutil
import uuid
from typing import Optional
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

from ..config import ConfigManager
from ..models import ThrowableItem

class ItemsView(Adw.PreferencesPage):
    def __init__(self, config_manager: ConfigManager, on_items_updated=None, on_test_throw=None):
        super().__init__()
        self.config_manager = config_manager
        self.on_items_updated = on_items_updated
        self.on_test_throw = on_test_throw
        self._updating_ui = False
        self.selected_item_id: Optional[str] = None

        self.set_title("Items")
        self.set_icon_name("package-x-generic-symbolic")

        # --- 1. Items List Group ---
        list_group = Adw.PreferencesGroup()
        list_group.set_title("Throwable Inventory")
        list_group.set_description("Manage 2D throwable items, collision sounds, restitution, and mass properties.")
        self.add(list_group)

        # Add Item Button Row
        add_row = Adw.ActionRow()
        add_row.set_title("Add New Throwable Item")
        add_row.set_subtitle("Load a custom PNG, WebP, GIF, or SVG image")
        add_btn = Gtk.Button(label="Add Item…")
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_item_dialog)
        add_row.add_suffix(add_btn)
        list_group.add(add_row)

        # Item Selector Combo Row
        self.item_combo = Adw.ComboRow()
        self.item_combo.set_title("Selected Item")
        self.item_combo.connect("notify::selected", self._on_item_selected)
        list_group.add(self.item_combo)

        # --- 2. Item Physical Properties Group ---
        self.props_group = Adw.PreferencesGroup()
        self.props_group.set_title("Item Physics and Visuals")
        self.add(self.props_group)

        # Item Name
        self.name_row = Adw.EntryRow()
        self.name_row.set_title("Display Name")
        self.name_row.connect("changed", self._on_prop_changed)
        self.props_group.add(self.name_row)

        # Scale Slider
        self.scale_row = Adw.SpinRow()
        self.scale_row.set_title("Display Scale")
        self.scale_row.set_subtitle("Normalized relative size on stream")
        self.scale_row.set_adjustment(Gtk.Adjustment(value=0.08, lower=0.02, upper=0.35, step_increment=0.01, page_increment=0.05))
        self.scale_row.set_digits(2)
        self.scale_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.scale_row)

        # Mass
        self.mass_row = Adw.SpinRow()
        self.mass_row.set_title("Physical Mass")
        self.mass_row.set_subtitle("Affects momentum and impact force on other bodies")
        self.mass_row.set_adjustment(Gtk.Adjustment(value=1.0, lower=0.1, upper=10.0, step_increment=0.1, page_increment=0.5))
        self.mass_row.set_digits(2)
        self.mass_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.mass_row)

        # Restitution (Bounciness)
        self.bounce_row = Adw.SpinRow()
        self.bounce_row.set_title("Bounciness (Restitution)")
        self.bounce_row.set_subtitle("0.0 = Dead thud, 1.0 = Maximum kinetic bounce")
        self.bounce_row.set_adjustment(Gtk.Adjustment(value=0.6, lower=0.0, upper=1.0, step_increment=0.05, page_increment=0.1))
        self.bounce_row.set_digits(2)
        self.bounce_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.bounce_row)

        # Rotational Speed
        self.spin_row = Adw.SpinRow()
        self.spin_row.set_title("Spin / Rotational Speed")
        self.spin_row.set_adjustment(Gtk.Adjustment(value=1.0, lower=0.0, upper=5.0, step_increment=0.2, page_increment=0.5))
        self.spin_row.set_digits(1)
        self.spin_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.spin_row)

        # Gravity Scale
        self.grav_row = Adw.SpinRow()
        self.grav_row.set_title("Gravity Scale")
        self.grav_row.set_subtitle("1.0 = Normal world gravity, 0.0 = Weightless")
        self.grav_row.set_adjustment(Gtk.Adjustment(value=1.0, lower=0.0, upper=3.0, step_increment=0.1, page_increment=0.5))
        self.grav_row.set_digits(2)
        self.grav_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.grav_row)

        # Lifetime
        self.life_row = Adw.SpinRow()
        self.life_row.set_title("Lifetime (Seconds)")
        self.life_row.set_subtitle("Time before smoothly fading and clearing from canvas")
        self.life_row.set_adjustment(Gtk.Adjustment(value=8.0, lower=2.0, upper=60.0, step_increment=1.0, page_increment=5.0))
        self.life_row.set_digits(1)
        self.life_row.connect("notify::value", self._on_prop_changed)
        self.props_group.add(self.life_row)

        # --- 3. Audio & Collision Sound Group ---
        self.audio_group = Adw.PreferencesGroup()
        self.audio_group.set_title("Collision Sound Effects")
        self.audio_group.set_description("Polyphonic Web Audio playback with dynamic limiter and pitch variation.")
        self.add(self.audio_group)

        # Sound Effect Combo (Built-ins: squish, bonk, thud, pop, clang)
        self.sound_presets = ["squish", "bonk", "thud", "pop", "clang"]
        self.sound_model = Gtk.StringList.new([s.capitalize() for s in self.sound_presets] + ["Custom Audio File…"])
        self.sound_row = Adw.ComboRow()
        self.sound_row.set_title("Impact Sound Effect")
        self.sound_row.set_model(self.sound_model)
        self.sound_row.connect("notify::selected", self._on_sound_preset_changed)
        self.audio_group.add(self.sound_row)

        # Sound Volume
        self.volume_row = Adw.SpinRow()
        self.volume_row.set_title("Playback Volume")
        self.volume_row.set_adjustment(Gtk.Adjustment(value=0.8, lower=0.0, upper=1.0, step_increment=0.05, page_increment=0.1))
        self.volume_row.set_digits(2)
        self.volume_row.connect("notify::value", self._on_prop_changed)
        self.audio_group.add(self.volume_row)

        # Pitch Randomization
        self.pitch_row = Adw.SpinRow()
        self.pitch_row.set_title("Pitch Variance")
        self.pitch_row.set_subtitle("Randomizes pitch to prevent repetitive ear fatigue")
        self.pitch_row.set_adjustment(Gtk.Adjustment(value=0.2, lower=0.0, upper=0.5, step_increment=0.05, page_increment=0.1))
        self.pitch_row.set_digits(2)
        self.pitch_row.connect("notify::value", self._on_prop_changed)
        self.audio_group.add(self.pitch_row)

        # Actions Row: Test Throw & Delete
        action_row = Adw.ActionRow()
        action_row.set_title("Test and Management")

        test_btn = Gtk.Button(label="Test Throw")
        test_btn.set_icon_name("media-playback-start-symbolic")
        test_btn.add_css_class("suggested-action")
        test_btn.connect("clicked", self._on_test_throw_clicked)
        action_row.add_suffix(test_btn)

        del_btn = Gtk.Button(label="Delete Item")
        del_btn.add_css_class("destructive-action")
        del_btn.connect("clicked", self._on_delete_item)
        action_row.add_suffix(del_btn)

        self.audio_group.add(action_row)

        # Initialize
        self.refresh_items()

    def refresh_items(self):
        self._updating_ui = True
        items_list = list(self.config_manager.items.values())
        names = [f"{it.name} ({it.id})" for it in items_list] if items_list else ["No Items"]
        model = Gtk.StringList.new(names)
        self.item_combo.set_model(model)

        if not self.selected_item_id and items_list:
            self.selected_item_id = items_list[0].id

        # Match combo selection
        for idx, it in enumerate(items_list):
            if it.id == self.selected_item_id:
                self.item_combo.set_selected(idx)
                break

        self._update_item_controls()
        self._updating_ui = False

    def _get_current_item(self) -> Optional[ThrowableItem]:
        if not self.selected_item_id:
            return None
        return self.config_manager.items.get(self.selected_item_id)

    def _update_item_controls(self):
        it = self._get_current_item()
        if not it:
            self.props_group.set_sensitive(False)
            self.audio_group.set_sensitive(False)
            return

        self.props_group.set_sensitive(True)
        self.audio_group.set_sensitive(True)
        self._updating_ui = True

        self.name_row.set_text(it.name)
        self.scale_row.set_value(it.scale)
        self.mass_row.set_value(it.mass)
        self.bounce_row.set_value(it.bounciness)
        self.spin_row.set_value(it.rotational_speed)
        self.grav_row.set_value(it.gravity_scale)
        self.life_row.set_value(it.lifetime)

        # Sound preset index
        if it.sound_effect in self.sound_presets:
            self.sound_row.set_selected(self.sound_presets.index(it.sound_effect))
        else:
            self.sound_row.set_selected(len(self.sound_presets)) # Custom

        self.volume_row.set_value(it.sound_volume)
        self.pitch_row.set_value(it.pitch_randomness)

        self._updating_ui = False

    def _on_item_selected(self, combo, pspec):
        if self._updating_ui:
            return
        idx = combo.get_selected()
        items_list = list(self.config_manager.items.values())
        if 0 <= idx < len(items_list):
            self.selected_item_id = items_list[idx].id
            self._update_item_controls()

    def _on_prop_changed(self, *args):
        if self._updating_ui:
            return
        it = self._get_current_item()
        if not it:
            return

        it.name = self.name_row.get_text() or it.name
        it.scale = self.scale_row.get_value()
        it.mass = self.mass_row.get_value()
        it.bounciness = self.bounce_row.get_value()
        it.rotational_speed = self.spin_row.get_value()
        it.gravity_scale = self.grav_row.get_value()
        it.lifetime = self.life_row.get_value()
        it.sound_volume = self.volume_row.get_value()
        it.pitch_randomness = self.pitch_row.get_value()

        self.config_manager.save()
        if self.on_items_updated:
            self.on_items_updated()

    def _on_sound_preset_changed(self, row, pspec):
        if self._updating_ui:
            return
        it = self._get_current_item()
        if not it:
            return

        idx = row.get_selected()
        if idx < len(self.sound_presets):
            it.sound_effect = self.sound_presets[idx]
            self.config_manager.save()
            if self.on_items_updated:
                self.on_items_updated()
        else:
            # Custom Audio file dialog
            dialog = Gtk.FileDialog()
            dialog.set_title("Select Custom Collision Audio (WAV, MP3, OGG)")
            filter_audio = Gtk.FileFilter()
            filter_audio.set_name("Audio Files")
            filter_audio.add_mime_type("audio/x-wav")
            filter_audio.add_mime_type("audio/mpeg")
            filter_audio.add_mime_type("audio/ogg")
            dialog.open(self.get_root(), None, self._on_audio_file_selected)

    def _on_audio_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                filename = os.path.basename(path)
                dest_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sounds")
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, filename)
                shutil.copy2(path, dest_path)

                it = self._get_current_item()
                if it:
                    it.sound_effect = f"/assets/sounds/{filename}"
                    self.config_manager.save()
                    if self.on_items_updated:
                        self.on_items_updated()
        except Exception as e:
            pass

    def _on_add_item_dialog(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Image for New Throwable Item")
        filter_img = Gtk.FileFilter()
        filter_img.set_name("Supported Images (PNG, WebP, GIF, SVG)")
        filter_img.add_mime_type("image/png")
        filter_img.add_mime_type("image/webp")
        filter_img.add_mime_type("image/gif")
        filter_img.add_mime_type("image/svg+xml")
        dialog.open(self.get_root(), None, self._on_image_file_selected)

    def _on_image_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                basename = os.path.basename(path)
                name_root = os.path.splitext(basename)[0]
                item_id = name_root.lower().replace(" ", "_")

                dest_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "items")
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, basename)
                shutil.copy2(path, dest_path)

                new_item = ThrowableItem(
                    id=item_id,
                    name=name_root.replace("_", " ").title(),
                    image_url=f"/assets/items/{basename}",
                    scale=0.08,
                    mass=1.0,
                    bounciness=0.6,
                    rotational_speed=1.0,
                    gravity_scale=1.0,
                    lifetime=8.0,
                    sound_effect="bonk",
                    sound_volume=0.85,
                    pitch_randomness=0.2
                )
                self.config_manager.items[item_id] = new_item
                self.selected_item_id = item_id
                self.config_manager.save()
                self.refresh_items()
                if self.on_items_updated:
                    self.on_items_updated()
        except Exception as e:
            pass

    def _on_delete_item(self, btn):
        it = self._get_current_item()
        if not it:
            return
        if it.id in self.config_manager.items:
            del self.config_manager.items[it.id]
            self.selected_item_id = None
            self.config_manager.save()
            self.refresh_items()
            if self.on_items_updated:
                self.on_items_updated()

    def _on_test_throw_clicked(self, btn):
        it = self._get_current_item()
        if it and self.on_test_throw:
            self.on_test_throw(it.id, 1)
