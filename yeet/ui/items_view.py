"""
Yeet - Throwable Items Management View (Qt6 / KDE 6)
App ID: gay.geeks.Yeet
"""

import os
import shutil
from typing import Optional
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, Slot
from ..config import ConfigManager
from ..models import ThrowableItem
from .widgets import KdeCard, FormRow

class ItemsView(QtWidgets.QWidget):
    itemsUpdated = Signal()
    testThrowRequested = Signal(str, int)  # item_id, amount

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._updating_ui = False
        self.selected_item_id: Optional[str] = None
        self.sound_presets = ["squish", "bonk", "thud", "pop", "clang"]

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

        # --- 1. Throwable Inventory Card ---
        inv_card = KdeCard(
            title="Throwable Inventory",
            subtitle="Manage 2D projectile presets, physical properties, restitution, and collision sound effects."
        )

        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setSpacing(8)

        add_btn = QtWidgets.QPushButton("Add New Item…")
        add_btn.setIcon(QtGui.QIcon.fromTheme("list-add"))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self._on_add_item_dialog)
        toolbar.addWidget(add_btn)

        toolbar.addStretch()
        inv_card.addLayout(toolbar)

        self.item_combo = QtWidgets.QComboBox()
        self.item_combo.setMinimumWidth(240)
        self.item_combo.currentIndexChanged.connect(self._on_item_selected)
        inv_card.addWidget(FormRow("Selected Item", self.item_combo, "Choose an item from your inventory to edit"))

        layout.addWidget(inv_card)

        # --- 2. Item Physics and Visuals Card ---
        self.props_card = KdeCard(
            title="Item Physics and Visuals",
            subtitle="Adjust size, mass, bounciness, and aerodynamic behavior for the selected item."
        )

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setMinimumWidth(220)
        self.name_edit.textChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Display Name", self.name_edit, "User-visible name in overlay and logs"))

        self.group_edit = QtWidgets.QLineEdit()
        self.group_edit.setMinimumWidth(220)
        self.group_edit.textChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Item Group / Tag", self.group_edit, "Category for barrage grouping (e.g. food, summer, toys)"))

        self.scale_spin = QtWidgets.QDoubleSpinBox()
        self.scale_spin.setRange(0.02, 0.35)
        self.scale_spin.setSingleStep(0.01)
        self.scale_spin.setDecimals(2)
        self.scale_spin.setMinimumWidth(120)
        self.scale_spin.valueChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Display Scale", self.scale_spin, "Normalized size relative to canvas width"))

        self.mass_spin = QtWidgets.QDoubleSpinBox()
        self.mass_spin.setRange(0.1, 10.0)
        self.mass_spin.setSingleStep(0.1)
        self.mass_spin.setDecimals(2)
        self.mass_spin.setMinimumWidth(120)
        self.mass_spin.valueChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Physical Mass", self.mass_spin, "Affects impact momentum and deflection force"))

        self.bounce_spin = QtWidgets.QDoubleSpinBox()
        self.bounce_spin.setRange(0.0, 1.0)
        self.bounce_spin.setSingleStep(0.05)
        self.bounce_spin.setDecimals(2)
        self.bounce_spin.setMinimumWidth(120)
        self.bounce_spin.valueChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Bounciness (Restitution)", self.bounce_spin, "0.0 = Dead thud, 1.0 = Maximum kinetic bounce"))

        self.spin_spin = QtWidgets.QDoubleSpinBox()
        self.spin_spin.setRange(0.0, 5.0)
        self.spin_spin.setSingleStep(0.2)
        self.spin_spin.setDecimals(1)
        self.spin_spin.setMinimumWidth(120)
        self.spin_spin.valueChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Spin / Rotational Speed", self.spin_spin, "Torque multiplier applied during flight"))

        self.grav_spin = QtWidgets.QDoubleSpinBox()
        self.grav_spin.setRange(0.0, 3.0)
        self.grav_spin.setSingleStep(0.1)
        self.grav_spin.setDecimals(2)
        self.grav_spin.setMinimumWidth(120)
        self.grav_spin.valueChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Gravity Scale", self.grav_spin, "1.0 = Normal world gravity, 0.0 = Weightless floating"))

        self.life_spin = QtWidgets.QDoubleSpinBox()
        self.life_spin.setRange(2.0, 60.0)
        self.life_spin.setSingleStep(1.0)
        self.life_spin.setDecimals(1)
        self.life_spin.setSuffix(" s")
        self.life_spin.setMinimumWidth(120)
        self.life_spin.valueChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Lifetime", self.life_spin, "Seconds on screen before fading and being recycled"))

        layout.addWidget(self.props_card)

        # --- 3. Collision Sound Effects Card ---
        self.audio_card = KdeCard(
            title="Collision Sound Effects",
            subtitle="Polyphonic Web Audio playback with procedural synthesizers or custom audio files."
        )

        self.sound_combo = QtWidgets.QComboBox()
        self.sound_combo.addItems([s.capitalize() for s in self.sound_presets] + ["Custom Audio File…"])
        self.sound_combo.setMinimumWidth(220)
        self.sound_combo.currentIndexChanged.connect(self._on_sound_preset_changed)
        self.audio_card.addWidget(FormRow("Impact Sound Effect", self.sound_combo, "Procedural sound type or custom WAV/MP3 sample"))

        self.volume_spin = QtWidgets.QDoubleSpinBox()
        self.volume_spin.setRange(0.0, 1.0)
        self.volume_spin.setSingleStep(0.05)
        self.volume_spin.setDecimals(2)
        self.volume_spin.setMinimumWidth(120)
        self.volume_spin.valueChanged.connect(self._on_prop_changed)
        self.audio_card.addWidget(FormRow("Playback Volume", self.volume_spin, "Sound level on collision (0.0 to 1.0)"))

        self.pitch_spin = QtWidgets.QDoubleSpinBox()
        self.pitch_spin.setRange(0.0, 0.5)
        self.pitch_spin.setSingleStep(0.05)
        self.pitch_spin.setDecimals(2)
        self.pitch_spin.setMinimumWidth(120)
        self.pitch_spin.valueChanged.connect(self._on_prop_changed)
        self.audio_card.addWidget(FormRow("Pitch Variance", self.pitch_spin, "Randomizes pitch on every hit to prevent ear fatigue"))

        # Management Buttons Row
        actions_box = QtWidgets.QHBoxLayout()
        actions_box.setSpacing(8)

        test_btn = QtWidgets.QPushButton("Test Throw")
        test_btn.setIcon(QtGui.QIcon.fromTheme("media-playback-start"))
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet("""
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
        test_btn.clicked.connect(self._on_test_throw_clicked)
        actions_box.addWidget(test_btn)

        del_btn = QtWidgets.QPushButton("Delete Item")
        del_btn.setIcon(QtGui.QIcon.fromTheme("edit-delete"))
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
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
        del_btn.clicked.connect(self._on_delete_item)
        actions_box.addWidget(del_btn)

        actions_box.addStretch()
        self.audio_card.addLayout(actions_box)

        layout.addWidget(self.audio_card)
        layout.addStretch()

        self.refresh_items()

    def refresh_items(self):
        self._updating_ui = True
        items_list = list(self.config_manager.items.values())

        self.item_combo.clear()
        if items_list:
            for it in items_list:
                label = f"{it.name} [{it.group}]" if it.group else it.name
                self.item_combo.addItem(label, it.id)
        else:
            self.item_combo.addItem("No Items", None)

        if not self.selected_item_id and items_list:
            self.selected_item_id = items_list[0].id

        for idx in range(self.item_combo.count()):
            if self.item_combo.itemData(idx) == self.selected_item_id:
                self.item_combo.setCurrentIndex(idx)
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
            self.props_card.setEnabled(False)
            self.audio_card.setEnabled(False)
            return

        self.props_card.setEnabled(True)
        self.audio_card.setEnabled(True)
        self._updating_ui = True

        self.name_edit.setText(it.name)
        self.group_edit.setText(it.group or "default")
        self.scale_spin.setValue(it.scale)
        self.mass_spin.setValue(it.mass)
        self.bounce_spin.setValue(it.bounciness)
        self.spin_spin.setValue(it.rotational_speed)
        self.grav_spin.setValue(it.gravity_scale)
        self.life_spin.setValue(it.lifetime)

        if it.sound_effect in self.sound_presets:
            self.sound_combo.setCurrentIndex(self.sound_presets.index(it.sound_effect))
        else:
            self.sound_combo.setCurrentIndex(len(self.sound_presets))

        self.volume_spin.setValue(it.sound_volume)
        self.pitch_spin.setValue(it.pitch_randomness)

        self._updating_ui = False

    def _on_item_selected(self, idx: int):
        if self._updating_ui:
            return
        item_id = self.item_combo.itemData(idx)
        if item_id:
            self.selected_item_id = item_id
            self._update_item_controls()

    def _on_prop_changed(self, *args):
        if self._updating_ui:
            return
        it = self._get_current_item()
        if not it:
            return

        it.name = self.name_edit.text() or it.name
        it.group = self.group_edit.text().strip() or "default"
        it.scale = self.scale_spin.value()
        it.mass = self.mass_spin.value()
        it.bounciness = self.bounce_spin.value()
        it.rotational_speed = self.spin_spin.value()
        it.gravity_scale = self.grav_spin.value()
        it.lifetime = self.life_spin.value()
        it.sound_volume = self.volume_spin.value()
        it.pitch_randomness = self.pitch_spin.value()

        # Update combo box label
        curr_idx = self.item_combo.currentIndex()
        if curr_idx >= 0:
            label = f"{it.name} [{it.group}]" if it.group else it.name
            self.item_combo.setItemText(curr_idx, label)

        self.config_manager.save()
        self.itemsUpdated.emit()

    def _on_sound_preset_changed(self, idx: int):
        if self._updating_ui:
            return
        it = self._get_current_item()
        if not it:
            return

        if idx < len(self.sound_presets):
            it.sound_effect = self.sound_presets[idx]
            self.config_manager.save()
            self.itemsUpdated.emit()
        else:
            # Pick custom audio file
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Select Custom Collision Audio",
                "",
                "Audio Files (*.wav *.mp3 *.ogg);;All Files (*)"
            )
            if filename:
                basename = os.path.basename(filename)
                dest_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sounds"))
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, basename)
                shutil.copy2(filename, dest_path)

                it.sound_effect = f"/assets/sounds/{basename}"
                self.config_manager.save()
                self.itemsUpdated.emit()

    def _on_add_item_dialog(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Image for New Throwable Item",
            "",
            "Supported Images (*.png *.webp *.gif *.svg);;All Files (*)"
        )
        if filename:
            basename = os.path.basename(filename)
            name_root = os.path.splitext(basename)[0]
            item_id = name_root.lower().replace(" ", "_")

            dest_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "items"))
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, basename)
            shutil.copy2(filename, dest_path)

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
            self.itemsUpdated.emit()

    def _on_delete_item(self):
        it = self._get_current_item()
        if not it:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Item",
            f"Are you sure you want to delete item '{it.name}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        if it.id in self.config_manager.items:
            del self.config_manager.items[it.id]
            self.selected_item_id = None
            self.config_manager.save()
            self.refresh_items()
            self.itemsUpdated.emit()

    def _on_test_throw_clicked(self):
        it = self._get_current_item()
        if it:
            self.testThrowRequested.emit(it.id, 1)
