"""
Yeet - Target Setup & Boundary Configuration View (Qt6 / KDE 6)
App ID: gay.geeks.Yeet
"""

import uuid
from typing import Optional
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, Slot
from ..config import ConfigManager
from ..models import Target
from .mapper_canvas import MapperCanvas
from .widgets import KdeCard, FormRow

class TargetView(QtWidgets.QWidget):
    targetsUpdated = Signal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._updating_ui = False

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area for responsive sizing
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        main_layout.addWidget(scroll)

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        scroll.setWidget(container)

        # --- 1. Coordinate Mapper Card ---
        mapper_card = KdeCard(
            title="Coordinate Mapper",
            subtitle="Configure normalized 2D collision boundaries. Drag center to move, corners to resize, top arm to rotate."
        )

        # Canvas Toolbar
        toolbar_layout = QtWidgets.QHBoxLayout()
        toolbar_layout.setSpacing(8)

        # Add Target Menu Button
        self.add_btn = QtWidgets.QPushButton("Add Target…")
        self.add_btn.setIcon(QtGui.QIcon.fromTheme("list-add"))
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet("""
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

        add_menu = QtWidgets.QMenu(self.add_btn)
        add_menu.addAction(QtGui.QIcon.fromTheme("draw-ellipse"), "Capsule / Pill (VTuber Torso)", lambda: self._on_add_target("capsule"))
        add_menu.addAction(QtGui.QIcon.fromTheme("draw-rectangle"), "Rectangle / Box", lambda: self._on_add_target("box"))
        add_menu.addAction(QtGui.QIcon.fromTheme("draw-circle"), "Circle / Ellipse", lambda: self._on_add_target("circle"))
        add_menu.addAction(QtGui.QIcon.fromTheme("draw-polygon"), "Custom Polygon (Convex Hull)", lambda: self._on_add_target("polygon"))
        self.add_btn.setMenu(add_menu)
        toolbar_layout.addWidget(self.add_btn)

        # Grid Checkbox
        self.grid_check = QtWidgets.QCheckBox("Show Grid")
        self.grid_check.setChecked(True)
        self.grid_check.toggled.connect(self._on_toggle_grid)
        toolbar_layout.addWidget(self.grid_check)

        # Trajectory Checkbox
        self.traj_check = QtWidgets.QCheckBox("Show Trajectory")
        self.traj_check.setChecked(True)
        self.traj_check.toggled.connect(self._on_toggle_trajectory)
        toolbar_layout.addWidget(self.traj_check)

        toolbar_layout.addStretch()

        # Backdrop buttons
        self.backdrop_btn = QtWidgets.QPushButton("Set Backdrop…")
        self.backdrop_btn.setIcon(QtGui.QIcon.fromTheme("image-x-generic"))
        self.backdrop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.backdrop_btn.clicked.connect(self._on_load_backdrop)
        toolbar_layout.addWidget(self.backdrop_btn)

        self.clear_backdrop_btn = QtWidgets.QPushButton("Clear Backdrop")
        self.clear_backdrop_btn.setIcon(QtGui.QIcon.fromTheme("edit-clear"))
        self.clear_backdrop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_backdrop_btn.clicked.connect(self._on_clear_backdrop)
        self.clear_backdrop_btn.setVisible(False)
        toolbar_layout.addWidget(self.clear_backdrop_btn)

        mapper_card.addLayout(toolbar_layout)

        # Mapper Canvas
        self.canvas = MapperCanvas()
        self.canvas.targetChanged.connect(self._on_canvas_target_changed)
        self.canvas.targetSelected.connect(self._on_canvas_target_selected)
        mapper_card.addWidget(self.canvas)

        layout.addWidget(mapper_card)

        # --- 2. Selected Target Properties Card ---
        self.props_card = KdeCard(
            title="Selected Target Properties",
            subtitle="Adjust dimensions, position, restitution, and collision parameters for the active target."
        )

        # Target Selector Dropdown
        self.target_selector = QtWidgets.QComboBox()
        self.target_selector.setMinimumWidth(220)
        self.target_selector.currentIndexChanged.connect(self._on_target_selection_changed)
        self.props_card.addWidget(FormRow("Active Target", self.target_selector, "Select target to edit"))

        # Target Label
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setMinimumWidth(220)
        self.name_edit.textChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Target Label", self.name_edit, "Identifier shown on canvas"))

        # Shape Type Combo
        self.shape_combo = QtWidgets.QComboBox()
        self.shape_combo.addItems(["Capsule (Pill)", "Box (Rectangle)", "Circle", "Polygon"])
        self.shape_combo.setMinimumWidth(220)
        self.shape_combo.currentIndexChanged.connect(self._on_shape_type_changed)
        self.props_card.addWidget(FormRow("Collision Shape", self.shape_combo, "Geometric boundary type"))

        # Position X
        self.pos_x_spin = QtWidgets.QDoubleSpinBox()
        self.pos_x_spin.setRange(0.0, 1.0)
        self.pos_x_spin.setSingleStep(0.01)
        self.pos_x_spin.setDecimals(3)
        self.pos_x_spin.setMinimumWidth(120)
        self.pos_x_spin.valueChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Position X (Normalized)", self.pos_x_spin, "0.0 (Left) to 1.0 (Right)"))

        # Position Y
        self.pos_y_spin = QtWidgets.QDoubleSpinBox()
        self.pos_y_spin.setRange(0.0, 1.0)
        self.pos_y_spin.setSingleStep(0.01)
        self.pos_y_spin.setDecimals(3)
        self.pos_y_spin.setMinimumWidth(120)
        self.pos_y_spin.valueChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Position Y (Normalized)", self.pos_y_spin, "0.0 (Top) to 1.0 (Bottom)"))

        # Width
        self.width_spin = QtWidgets.QDoubleSpinBox()
        self.width_spin.setRange(0.02, 1.0)
        self.width_spin.setSingleStep(0.01)
        self.width_spin.setDecimals(3)
        self.width_spin.setMinimumWidth(120)
        self.width_spin.valueChanged.connect(self._on_prop_changed)
        self.width_row = FormRow("Width (Normalized)", self.width_spin, "Relative width on canvas")
        self.props_card.addWidget(self.width_row)

        # Height
        self.height_spin = QtWidgets.QDoubleSpinBox()
        self.height_spin.setRange(0.02, 1.0)
        self.height_spin.setSingleStep(0.01)
        self.height_spin.setDecimals(3)
        self.height_spin.setMinimumWidth(120)
        self.height_spin.valueChanged.connect(self._on_prop_changed)
        self.height_row = FormRow("Height (Normalized)", self.height_spin, "Relative height on canvas")
        self.props_card.addWidget(self.height_row)

        # Radius (for Circle)
        self.radius_spin = QtWidgets.QDoubleSpinBox()
        self.radius_spin.setRange(0.01, 0.5)
        self.radius_spin.setSingleStep(0.01)
        self.radius_spin.setDecimals(3)
        self.radius_spin.setMinimumWidth(120)
        self.radius_spin.valueChanged.connect(self._on_prop_changed)
        self.radius_row = FormRow("Radius (Normalized)", self.radius_spin, "For circle targets")
        self.props_card.addWidget(self.radius_row)

        # Rotation
        self.rotation_spin = QtWidgets.QDoubleSpinBox()
        self.rotation_spin.setRange(-180.0, 180.0)
        self.rotation_spin.setSingleStep(1.0)
        self.rotation_spin.setDecimals(1)
        self.rotation_spin.setSuffix("°")
        self.rotation_spin.setMinimumWidth(120)
        self.rotation_spin.valueChanged.connect(self._on_prop_changed)
        self.rotation_row = FormRow("Rotation", self.rotation_spin, "Orientation in degrees")
        self.props_card.addWidget(self.rotation_row)

        # Restitution (Bounciness)
        self.bounce_spin = QtWidgets.QDoubleSpinBox()
        self.bounce_spin.setRange(0.0, 1.0)
        self.bounce_spin.setSingleStep(0.05)
        self.bounce_spin.setDecimals(2)
        self.bounce_spin.setMinimumWidth(120)
        self.bounce_spin.valueChanged.connect(self._on_prop_changed)
        self.props_card.addWidget(FormRow("Restitution (Bounciness)", self.bounce_spin, "0.0 = Absorb impact, 1.0 = Elastic super bounce"))

        # Remove Target Action Row
        del_btn = QtWidgets.QPushButton("Remove Target")
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
        del_btn.clicked.connect(self._on_delete_target)
        self.props_card.addWidget(FormRow("Delete Active Target", del_btn, "Remove this collision boundary permanently"))

        layout.addWidget(self.props_card)
        layout.addStretch()

        # Initialize
        self.refresh_from_config()

    def refresh_from_config(self):
        self._updating_ui = True
        targets = self.config_manager.targets

        self.target_selector.clear()
        if targets:
            for t in targets:
                self.target_selector.addItem(t.name, t.id)
        else:
            self.target_selector.addItem("No Targets", None)

        selected_id = self.canvas.selected_target_id
        if not selected_id and targets:
            selected_id = targets[0].id

        self.canvas.setTargets(targets, selected_id)

        # Match combo selection
        for idx in range(self.target_selector.count()):
            if self.target_selector.itemData(idx) == selected_id:
                self.target_selector.setCurrentIndex(idx)
                break

        self._update_property_controls()
        self._updating_ui = False

    def _update_property_controls(self):
        tgt = self.canvas.getSelectedTarget()
        if not tgt:
            self.props_card.setEnabled(False)
            return

        self.props_card.setEnabled(True)
        self._updating_ui = True

        self.name_edit.setText(tgt.name)
        type_indices = {"capsule": 0, "box": 1, "circle": 2, "polygon": 3}
        self.shape_combo.setCurrentIndex(type_indices.get(tgt.type, 0))

        self.pos_x_spin.setValue(tgt.x)
        self.pos_y_spin.setValue(tgt.y)
        self.width_spin.setValue(tgt.width)
        self.height_spin.setValue(tgt.height)
        self.radius_spin.setValue(tgt.radius)
        self.rotation_spin.setValue(tgt.rotation)
        self.bounce_spin.setValue(tgt.bounciness)

        # Visibility based on shape
        is_circle = (tgt.type == "circle")
        is_poly = (tgt.type == "polygon")
        self.radius_row.setVisible(is_circle)
        self.width_row.setVisible(not is_circle and not is_poly)
        self.height_row.setVisible(not is_circle and not is_poly)
        self.rotation_row.setVisible(not is_circle)

        self._updating_ui = False

    def _on_canvas_target_changed(self, target: Target):
        if not self._updating_ui:
            self._update_property_controls()
            self.config_manager.save()
            self.targetsUpdated.emit()

    def _on_canvas_target_selected(self, target_id: str):
        if self._updating_ui:
            return
        for idx in range(self.target_selector.count()):
            if self.target_selector.itemData(idx) == target_id:
                self.target_selector.setCurrentIndex(idx)
                break
        self._update_property_controls()

    def _on_target_selection_changed(self, idx: int):
        if self._updating_ui:
            return
        target_id = self.target_selector.itemData(idx)
        if target_id:
            self.canvas.selectTarget(target_id)
            self._update_property_controls()

    def _on_shape_type_changed(self, idx: int):
        if self._updating_ui:
            return
        tgt = self.canvas.getSelectedTarget()
        if not tgt:
            return

        shape_types = ["capsule", "box", "circle", "polygon"]
        tgt.type = shape_types[idx]
        if tgt.type == "polygon" and not tgt.points:
            tgt.points = [
                [tgt.x, tgt.y - 0.15],
                [tgt.x - 0.12, tgt.y + 0.15],
                [tgt.x + 0.12, tgt.y + 0.15]
            ]

        self.canvas.update()
        self._update_property_controls()
        self.config_manager.save()
        self.targetsUpdated.emit()

    def _on_prop_changed(self, *args):
        if self._updating_ui:
            return
        tgt = self.canvas.getSelectedTarget()
        if not tgt:
            return

        tgt.name = self.name_edit.text() or "Target"
        tgt.x = self.pos_x_spin.value()
        tgt.y = self.pos_y_spin.value()
        tgt.width = self.width_spin.value()
        tgt.height = self.height_spin.value()
        tgt.radius = self.radius_spin.value()
        tgt.rotation = self.rotation_spin.value()
        tgt.bounciness = self.bounce_spin.value()

        # Update label in target_selector combo
        curr_idx = self.target_selector.currentIndex()
        if curr_idx >= 0:
            self.target_selector.setItemText(curr_idx, tgt.name)

        self.canvas.update()
        self.config_manager.save()
        self.targetsUpdated.emit()

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
        self.canvas.selectTarget(new_id)
        self.targetsUpdated.emit()

    def _on_delete_target(self):
        tgt = self.canvas.getSelectedTarget()
        if not tgt:
            return

        # Confirm removal with KDE message box
        reply = QtWidgets.QMessageBox.question(
            self,
            "Remove Target",
            f"Are you sure you want to remove target '{tgt.name}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        self.config_manager.targets = [t for t in self.config_manager.targets if t.id != tgt.id]
        self.config_manager.save()
        self.refresh_from_config()
        self.targetsUpdated.emit()

    def _on_toggle_grid(self, active: bool):
        self.canvas.setShowGrid(active)

    def _on_toggle_trajectory(self, active: bool):
        self.canvas.setShowTrajectory(active)

    def _on_load_backdrop(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Stream Screenshot or Avatar Backdrop",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp);;All Files (*)"
        )
        if filename:
            pixmap = QtGui.QPixmap(filename)
            if not pixmap.isNull():
                self.canvas.setBackdropPixmap(pixmap)
                self.clear_backdrop_btn.setVisible(True)

    def _on_clear_backdrop(self):
        self.canvas.setBackdropPixmap(None)
        self.clear_backdrop_btn.setVisible(False)
