"""
Yeet - Spawn & Physics Rules View (Qt6 / KDE 6)
App ID: gay.geeks.Yeet
"""

from typing import Optional
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, Slot
from ..config import ConfigManager
from .widgets import KdeCard, FormRow

class PhysicsView(QtWidgets.QWidget):
    physicsUpdated = Signal()
    testThrowRequested = Signal(str, int, str, float, float)  # item_id, amount, direction, force, spread
    clearCanvasRequested = Signal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._updating_ui = False

        self.spawn_directions = ["random", "left", "right", "top", "bottom", "aimed", "rain", "spray"]
        self.dir_labels = [
            "Random Screen Edge",
            "Left Edge (Shoots Right)",
            "Right Edge (Shoots Left)",
            "Top Edge (Falls Down)",
            "Bottom Edge (Shoots Up)",
            "Aimed Arc (Direct at Avatar Target)",
            "Rain / Dropping (Top Grid)",
            "Point-Source Spray (Custom Emitter)"
        ]

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

        # --- 1. Spawn Behaviors and Trajectories Card ---
        spawn_card = KdeCard(
            title="Spawn Behaviors and Trajectories",
            subtitle="Control projectile spawn origins, ballistic trajectories aimed at your avatar, and barrage spread."
        )

        self.dir_combo = QtWidgets.QComboBox()
        self.dir_combo.addItems(self.dir_labels)
        self.dir_combo.setMinimumWidth(240)
        self.dir_combo.currentIndexChanged.connect(self._on_spawn_dir_changed)
        spawn_card.addWidget(FormRow("Default Spawn Mode", self.dir_combo, "Origin edge or trajectory algorithm"))

        self.force_spin = QtWidgets.QDoubleSpinBox()
        self.force_spin.setRange(0.2, 3.5)
        self.force_spin.setSingleStep(0.1)
        self.force_spin.setDecimals(2)
        self.force_spin.setMinimumWidth(120)
        self.force_spin.valueChanged.connect(self._on_physics_changed)
        spawn_card.addWidget(FormRow("Launch Velocity Multiplier", self.force_spin, "Scales projectile launch speed when thrown"))

        self.spread_spin = QtWidgets.QDoubleSpinBox()
        self.spread_spin.setRange(0.0, 90.0)
        self.spread_spin.setSingleStep(2.5)
        self.spread_spin.setDecimals(1)
        self.spread_spin.setSuffix("°")
        self.spread_spin.setMinimumWidth(120)
        self.spread_spin.valueChanged.connect(self._on_physics_changed)
        spawn_card.addWidget(FormRow("Spread Angle Variance", self.spread_spin, "Angular dispersion for multi-item barrages"))

        layout.addWidget(spawn_card)

        # --- 2. Point-Source Spray Emitter Card ---
        spray_card = KdeCard(
            title="Point-Source Spray Emitter",
            subtitle="Custom origin coordinates and angle when using Point-Source Spray mode."
        )

        self.spray_x_spin = QtWidgets.QDoubleSpinBox()
        self.spray_x_spin.setRange(0.0, 1.0)
        self.spray_x_spin.setSingleStep(0.05)
        self.spray_x_spin.setDecimals(2)
        self.spray_x_spin.setMinimumWidth(120)
        self.spray_x_spin.valueChanged.connect(self._on_spray_changed)
        spray_card.addWidget(FormRow("Emitter Origin X (Normalized)", self.spray_x_spin, "Horizontal origin point"))

        self.spray_y_spin = QtWidgets.QDoubleSpinBox()
        self.spray_y_spin.setRange(0.0, 1.0)
        self.spray_y_spin.setSingleStep(0.05)
        self.spray_y_spin.setDecimals(2)
        self.spray_y_spin.setMinimumWidth(120)
        self.spray_y_spin.valueChanged.connect(self._on_spray_changed)
        spray_card.addWidget(FormRow("Emitter Origin Y (Normalized)", self.spray_y_spin, "Vertical origin point"))

        self.spray_angle_spin = QtWidgets.QDoubleSpinBox()
        self.spray_angle_spin.setRange(-180.0, 180.0)
        self.spray_angle_spin.setSingleStep(5.0)
        self.spray_angle_spin.setDecimals(1)
        self.spray_angle_spin.setSuffix("°")
        self.spray_angle_spin.setMinimumWidth(120)
        self.spray_angle_spin.valueChanged.connect(self._on_spray_changed)
        spray_card.addWidget(FormRow("Spray Emitter Angle", self.spray_angle_spin, "0° = Right, 90° = Down, 180° = Left, -90° = Up"))

        layout.addWidget(spray_card)

        # --- 3. World Physics and Performance Card ---
        world_card = KdeCard(
            title="World Physics and Performance",
            subtitle="Global gravity, audio collision limits, and Matter.js engine constraints."
        )

        self.grav_y_spin = QtWidgets.QDoubleSpinBox()
        self.grav_y_spin.setRange(-2.0, 3.0)
        self.grav_y_spin.setSingleStep(0.1)
        self.grav_y_spin.setDecimals(2)
        self.grav_y_spin.setMinimumWidth(120)
        self.grav_y_spin.valueChanged.connect(self._on_gravity_changed)
        world_card.addWidget(FormRow("World Vertical Gravity (Y)", self.grav_y_spin, "1.0 = Standard downward gravity, 0.0 = Zero-G, -1.0 = Upward float"))

        self.debounce_spin = QtWidgets.QSpinBox()
        self.debounce_spin.setRange(10, 250)
        self.debounce_spin.setSingleStep(10)
        self.debounce_spin.setSuffix(" ms")
        self.debounce_spin.setMinimumWidth(120)
        self.debounce_spin.valueChanged.connect(self._on_physics_changed)
        world_card.addWidget(FormRow("Sound Debounce / Limiter", self.debounce_spin, "Minimum interval between impact sounds to prevent clipping"))

        self.max_items_spin = QtWidgets.QSpinBox()
        self.max_items_spin.setRange(20, 300)
        self.max_items_spin.setSingleStep(10)
        self.max_items_spin.setMinimumWidth(120)
        self.max_items_spin.valueChanged.connect(self._on_physics_changed)
        world_card.addWidget(FormRow("Max Simultaneous Items", self.max_items_spin, "Recycles oldest items to maintain smooth 60 FPS in OBS"))

        self.debug_check = QtWidgets.QCheckBox("Show Target Boundaries in OBS")
        self.debug_check.toggled.connect(self._on_debug_toggled)
        world_card.addWidget(FormRow("Collider Wireframes", self.debug_check, "Renders visual wireframes in OBS to help align with your avatar"))

        layout.addWidget(world_card)

        # --- 4. Test Throw Playground Card ---
        test_card = KdeCard(
            title="Test Throw Playground",
            subtitle="Instantly test launching throws into your live OBS overlay."
        )

        self.test_item_combo = QtWidgets.QComboBox()
        self.test_item_combo.setMinimumWidth(240)
        test_card.addWidget(FormRow("Throw Item", self.test_item_combo, "Select item or random barrage"))

        self.test_amount_spin = QtWidgets.QSpinBox()
        self.test_amount_spin.setRange(1, 50)
        self.test_amount_spin.setValue(5)
        self.test_amount_spin.setMinimumWidth(120)
        test_card.addWidget(FormRow("Throw Amount", self.test_amount_spin, "Number of items to spawn in barrage"))

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(8)

        launch_btn = QtWidgets.QPushButton("Launch Throw!")
        launch_btn.setIcon(QtGui.QIcon.fromTheme("media-playback-start"))
        launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        launch_btn.setStyleSheet("""
            QPushButton {
                background-color: #3daee9;
                color: #ffffff;
                font-weight: 600;
                padding: 7px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        launch_btn.clicked.connect(self._on_launch_test)
        btn_row.addWidget(launch_btn)

        clear_btn = QtWidgets.QPushButton("Clear Canvas")
        clear_btn.setIcon(QtGui.QIcon.fromTheme("edit-clear"))
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #da4453;
                color: #ffffff;
                font-weight: 600;
                padding: 7px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        clear_btn.clicked.connect(self._on_clear_test)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        test_card.addLayout(btn_row)

        layout.addWidget(test_card)
        layout.addStretch()

        self.refresh_from_config()

    def refresh_from_config(self):
        self._updating_ui = True
        p = self.config_manager.physics

        if p.default_spawn_direction in self.spawn_directions:
            self.dir_combo.setCurrentIndex(self.spawn_directions.index(p.default_spawn_direction))
        else:
            self.dir_combo.setCurrentIndex(0)

        self.force_spin.setValue(p.default_force)
        self.spread_spin.setValue(p.default_spread)
        self.spray_x_spin.setValue(p.spawn_point[0] if len(p.spawn_point) > 0 else 0.0)
        self.spray_y_spin.setValue(p.spawn_point[1] if len(p.spawn_point) > 1 else 0.5)
        self.spray_angle_spin.setValue(p.spray_angle)

        self.grav_y_spin.setValue(p.gravity[1] if len(p.gravity) > 1 else 1.0)
        self.debounce_spin.setValue(p.sound_debounce_ms)
        self.max_items_spin.setValue(p.max_active_items)
        self.debug_check.setChecked(p.debug_boundaries)

        # Update test item combo
        self.test_item_combo.clear()
        self.test_item_combo.addItem("🎲 Random Item", "random")
        self.test_item_combo.addItem("🔀 Random Mix (All Items)", "random_mix")
        for it in self.config_manager.items.values():
            lbl = f"{it.name} [{it.group}]" if it.group else it.name
            self.test_item_combo.addItem(lbl, it.id)

        self._updating_ui = False

    def _on_spawn_dir_changed(self, idx: int):
        if self._updating_ui:
            return
        self.config_manager.physics.default_spawn_direction = self.spawn_directions[idx]
        self.config_manager.save()
        self.physicsUpdated.emit()

    def _on_physics_changed(self, *args):
        if self._updating_ui:
            return
        p = self.config_manager.physics
        p.default_force = self.force_spin.value()
        p.default_spread = self.spread_spin.value()
        p.sound_debounce_ms = self.debounce_spin.value()
        p.max_active_items = self.max_items_spin.value()
        self.config_manager.save()
        self.physicsUpdated.emit()

    def _on_spray_changed(self, *args):
        if self._updating_ui:
            return
        p = self.config_manager.physics
        p.spawn_point = [self.spray_x_spin.value(), self.spray_y_spin.value()]
        p.spray_angle = self.spray_angle_spin.value()
        self.config_manager.save()
        self.physicsUpdated.emit()

    def _on_gravity_changed(self, *args):
        if self._updating_ui:
            return
        self.config_manager.physics.gravity = [0.0, self.grav_y_spin.value()]
        self.config_manager.save()
        self.physicsUpdated.emit()

    def _on_debug_toggled(self, active: bool):
        if self._updating_ui:
            return
        self.config_manager.physics.debug_boundaries = active
        self.config_manager.save()
        self.physicsUpdated.emit()

    def _on_launch_test(self):
        item_id = self.test_item_combo.currentData() or "random"
        amount = self.test_amount_spin.value()
        direction = self.spawn_directions[self.dir_combo.currentIndex()]
        force = self.force_spin.value()
        spread = self.spread_spin.value()
        self.testThrowRequested.emit(item_id, amount, direction, force, spread)

    def _on_clear_test(self):
        self.clearCanvasRequested.emit()
