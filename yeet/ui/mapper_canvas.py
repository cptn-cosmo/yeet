"""
Yeet - Interactive 2D Coordinate Mapper Canvas (Qt6 + QPainter)
App ID: gay.geeks.Yeet
"""

import math
from typing import List, Optional, Tuple
from ..qt_compat import QtCore, QtGui, QtWidgets, Qt, Signal, QPoint, QPointF, QRect, QRectF
from ..models import Target

class MapperCanvas(QtWidgets.QWidget):
    targetChanged = Signal(object)    # Emits Target
    targetSelected = Signal(str)      # Emits target ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(480, 270)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)

        self.targets: List[Target] = []
        self.selected_target_id: Optional[str] = None
        self.active_spawn_direction: str = "random"
        self.show_grid: bool = True
        self.show_trajectory: bool = True
        self.background_pixmap: Optional[QtGui.QPixmap] = None

        # Drag state tracking
        self.active_drag_handle: Optional[str] = None
        self.drag_start_pos = QPointF(0.0, 0.0)
        self.initial_target_state = {}

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(640, 360)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        return int(w * 9 / 16)

    def setTargets(self, targets: List[Target], selected_id: Optional[str] = None):
        self.targets = targets
        if selected_id:
            self.selected_target_id = selected_id
        elif targets and not self.selected_target_id:
            self.selected_target_id = targets[0].id
        self.update()

    def getSelectedTarget(self) -> Optional[Target]:
        for t in self.targets:
            if t.id == self.selected_target_id:
                return t
        return None

    def selectTarget(self, target_id: str):
        if self.selected_target_id != target_id:
            self.selected_target_id = target_id
            self.targetSelected.emit(target_id)
            self.update()

    def setSpawnDirection(self, direction: str):
        self.active_spawn_direction = direction
        self.update()

    def setShowGrid(self, show: bool):
        self.show_grid = show
        self.update()

    def setShowTrajectory(self, show: bool):
        self.show_trajectory = show
        self.update()

    def setBackdropPixmap(self, pixmap: Optional[QtGui.QPixmap]):
        self.background_pixmap = pixmap
        self.update()

    # --- Coordinate Conversion ---
    def _norm_to_px(self, nx: float, ny: float, w: float, h: float) -> QPointF:
        return QPointF(nx * w, ny * h)

    def _px_to_norm(self, px: float, py: float, w: float, h: float) -> Tuple[float, float]:
        return max(0.0, min(1.0, px / w)), max(0.0, min(1.0, py / h))

    # --- Paint Event ---
    def paintEvent(self, event: QtGui.QPaintEvent):
        w = float(self.width())
        h = float(self.height())

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing, True)

        # 1. Background Fill (Dark Slate Stream Viewport)
        painter.fillRect(self.rect(), QtGui.QColor(28, 30, 38))

        # Backdrop Screenshot if loaded
        if self.background_pixmap and not self.background_pixmap.isNull():
            scaled = self.background_pixmap.scaled(
                int(w), int(h),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)

        # 2. Grid Guidelines (10% increments)
        if self.show_grid:
            self._draw_grid(painter, w, h)

        # 3. Spawn Zone Edge Indicators
        self._draw_spawn_zones(painter, w, h)

        # 4. Trajectory Preview Guide
        if self.show_trajectory:
            self._draw_trajectory(painter, w, h)

        # 5. Render Targets
        for tgt in self.targets:
            is_selected = (tgt.id == self.selected_target_id)
            self._draw_target(painter, tgt, w, h, is_selected)

        # 6. Stream Resolution & Aspect Ratio Badge
        painter.save()
        painter.setPen(QtGui.QColor(255, 255, 255, 140))
        font = painter.font()
        font.setPixelSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(14, 22, "16:9 Stream Viewport (OBS) | Normalized Rel [0.0 - 1.0]")
        painter.restore()

        # Canvas Border
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 30), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def _draw_grid(self, painter: QtGui.QPainter, w: float, h: float):
        painter.save()
        grid_pen = QtGui.QPen(QtGui.QColor(230, 230, 255, 20), 1.0, Qt.PenStyle.DashLine)
        grid_pen.setDashPattern([4, 4])
        painter.setPen(grid_pen)

        for i in range(1, 10):
            gx = (i / 10.0) * w
            gy = (i / 10.0) * h
            painter.drawLine(QPointF(gx, 0), QPointF(gx, h))
            painter.drawLine(QPointF(0, gy), QPointF(w, gy))

        # Center Crosshair
        center_pen = QtGui.QPen(QtGui.QColor(61, 174, 233, 70), 1.5)
        painter.setPen(center_pen)
        painter.drawLine(QPointF(w * 0.5, 0), QPointF(w * 0.5, h))
        painter.drawLine(QPointF(0, h * 0.5), QPointF(w, h * 0.5))
        painter.restore()

    def _draw_spawn_zones(self, painter: QtGui.QPainter, w: float, h: float):
        painter.save()
        dir_name = self.active_spawn_direction.lower()
        pen = QtGui.QPen(QtGui.QColor(246, 187, 66, 140), 4.0)
        painter.setPen(pen)

        if dir_name in ['left', 'random']:
            painter.drawLine(QPointF(2, 0), QPointF(2, h))
        if dir_name in ['right', 'random']:
            painter.drawLine(QPointF(w - 2, 0), QPointF(w - 2, h))
        if dir_name in ['top', 'random', 'rain']:
            painter.drawLine(QPointF(0, 2), QPointF(w, 2))
        if dir_name in ['bottom', 'random']:
            painter.drawLine(QPointF(0, h - 2), QPointF(w, h - 2))

        painter.restore()

    def _draw_trajectory(self, painter: QtGui.QPainter, w: float, h: float):
        selected = self.getSelectedTarget()
        if not selected:
            return

        target_pos = self._norm_to_px(selected.x, selected.y, w, h)
        tx, ty = target_pos.x(), target_pos.y()
        dir_name = self.active_spawn_direction.lower()

        if dir_name == 'left':
            ox, oy = 0.0, ty
        elif dir_name == 'right':
            ox, oy = w, ty
        elif dir_name in ['top', 'rain']:
            ox, oy = tx, 0.0
        elif dir_name == 'bottom':
            ox, oy = tx, h
        else:
            ox, oy = 0.0, ty

        painter.save()
        traj_pen = QtGui.QPen(QtGui.QColor(246, 187, 66, 180), 2.0, Qt.PenStyle.DashLine)
        traj_pen.setDashPattern([6, 4])
        painter.setPen(traj_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QtGui.QPainterPath()
        path.moveTo(ox, oy)
        cx = (ox + tx) * 0.5
        cy = min(oy, ty) - 40.0
        path.quadTo(cx, cy, tx, ty)
        painter.drawPath(path)

        # Arrowhead / impact dot at target
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(246, 187, 66, 220))
        painter.drawEllipse(QPointF(tx, ty), 5.0, 5.0)
        painter.restore()

    def _draw_target(self, painter: QtGui.QPainter, tgt: Target, w: float, h: float, is_selected: bool):
        center = self._norm_to_px(tgt.x, tgt.y, w, h)
        cx, cy = center.x(), center.y()
        tw = tgt.width * w
        th = tgt.height * h

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(tgt.rotation)

        if is_selected:
            fill_color = QtGui.QColor(61, 174, 233, 65)     # Breeze highlight blue fill
            stroke_color = QtGui.QColor(61, 174, 233, 240)  # Bright blue border
            stroke_width = 2.5
        else:
            fill_color = QtGui.QColor(127, 140, 141, 35)
            stroke_color = QtGui.QColor(189, 195, 199, 120)
            stroke_width = 1.5

        pen = QtGui.QPen(stroke_color, stroke_width)
        painter.setPen(pen)
        painter.setBrush(fill_color)

        if tgt.type == "box":
            painter.drawRect(QRectF(-tw * 0.5, -th * 0.5, tw, th))

        elif tgt.type == "circle":
            r = tgt.radius * min(w, h)
            painter.drawEllipse(QPointF(0, 0), r, r)

        elif tgt.type == "capsule":
            # VTuber Capsule / Pill shape
            r = min(tw, th) * 0.5
            path = QtGui.QPainterPath()
            if th >= tw:
                # Vertical capsule
                half_body_h = (th * 0.5) - r
                path.moveTo(-r, -half_body_h)
                path.arcTo(QRectF(-r, -half_body_h - r, 2 * r, 2 * r), 180, -180)
                path.lineTo(r, half_body_h)
                path.arcTo(QRectF(-r, half_body_h - r, 2 * r, 2 * r), 0, -180)
                path.closeSubpath()
            else:
                # Horizontal capsule
                half_body_w = (tw * 0.5) - r
                path.moveTo(-half_body_w, -r)
                path.lineTo(half_body_w, -r)
                path.arcTo(QRectF(half_body_w - r, -r, 2 * r, 2 * r), 90, -180)
                path.lineTo(-half_body_w, r)
                path.arcTo(QRectF(-half_body_w - r, -r, 2 * r, 2 * r), 270, -180)
                path.closeSubpath()
            painter.drawPath(path)

        elif tgt.type == "polygon":
            points = tgt.points
            if len(points) >= 3:
                poly = QtGui.QPolygonF()
                for pt in points:
                    px, py = pt[0] * w, pt[1] * h
                    poly.append(QPointF(px - cx, py - cy))
                painter.drawPolygon(poly)

        # Target Name Label
        painter.setPen(QtGui.QColor(255, 255, 255, 220 if is_selected else 130))
        font = painter.font()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        fm = QtGui.QFontMetrics(font)
        text_w = fm.horizontalAdvance(tgt.name)
        text_h = fm.height()
        painter.drawText(int(-text_w * 0.5), int(text_h * 0.3), tgt.name)

        # Draw Interactive Handles if Selected
        if is_selected:
            self._draw_handles(painter, tgt, tw, th, w, h)

        painter.restore()

    def _draw_handles(self, painter: QtGui.QPainter, tgt: Target, tw: float, th: float, w: float, h: float):
        handle_color = QtGui.QColor(39, 174, 96)   # Positive green handle
        handle_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 230), 1.5)

        # 1. Center Handle (Move)
        painter.setPen(handle_pen)
        painter.setBrush(handle_color)
        painter.drawEllipse(QPointF(0, 0), 4.5, 4.5)

        # 2. Resize Handle (Bottom-Right / Radius)
        painter.setBrush(QtGui.QColor(61, 174, 233))
        if tgt.type in ["box", "capsule"]:
            painter.drawEllipse(QPointF(tw * 0.5, th * 0.5), 5.5, 5.5)
        elif tgt.type == "circle":
            r = tgt.radius * min(w, h)
            painter.drawEllipse(QPointF(r, 0), 5.5, 5.5)
        elif tgt.type == "polygon":
            center = self._norm_to_px(tgt.x, tgt.y, w, h)
            for pt in tgt.points:
                px, py = pt[0] * w, pt[1] * h
                painter.drawEllipse(QPointF(px - center.x(), py - center.y()), 5.5, 5.5)

        # 3. Rotation Handle (Top arm)
        rot_arm_y = -th * 0.5 - 22.0 if tgt.type != "circle" else -tgt.radius * min(w, h) - 22.0
        start_y = -th * 0.5 if tgt.type != "circle" else -tgt.radius * min(w, h)

        arm_pen = QtGui.QPen(QtGui.QColor(61, 174, 233, 190), 1.5)
        painter.setPen(arm_pen)
        painter.drawLine(QPointF(0, start_y), QPointF(0, rot_arm_y))

        painter.setPen(handle_pen)
        painter.setBrush(QtGui.QColor(61, 174, 233))
        painter.drawEllipse(QPointF(0, rot_arm_y), 5.5, 5.5)

    # --- Mouse Interaction & Hit Testing ---
    def _hit_test(self, pos: QPointF, w: float, h: float) -> Tuple[Optional[Target], Optional[str]]:
        selected = self.getSelectedTarget()
        if selected:
            center = self._norm_to_px(selected.x, selected.y, w, h)
            cx, cy = center.x(), center.y()
            tw = selected.width * w
            th = selected.height * h

            # Rotate click position relative to target center
            rad = -math.radians(selected.rotation)
            dx = pos.x() - cx
            dy = pos.y() - cy
            rx = dx * math.cos(rad) - dy * math.sin(rad)
            ry = dx * math.sin(rad) + dy * math.cos(rad)

            # Check Rotation Handle
            rot_y = -th * 0.5 - 22.0 if selected.type != "circle" else -selected.radius * min(w, h) - 22.0
            if math.hypot(rx, ry - rot_y) <= 13:
                return selected, "rotate"

            # Check Resize Handle
            if selected.type in ["box", "capsule"]:
                if math.hypot(rx - tw * 0.5, ry - th * 0.5) <= 13:
                    return selected, "resize_se"
            elif selected.type == "circle":
                r = selected.radius * min(w, h)
                if math.hypot(rx - r, ry) <= 13:
                    return selected, "resize_se"
            elif selected.type == "polygon":
                for i, pt in enumerate(selected.points):
                    vx, vy = pt[0] * w, pt[1] * h
                    if math.hypot(pos.x() - vx, pos.y() - vy) <= 13:
                        return selected, f"poly_vertex_{i}"

            # Check Center Handle
            if math.hypot(rx, ry) <= 12:
                return selected, "center"

        # Check all targets for body click
        for tgt in reversed(self.targets):
            center = self._norm_to_px(tgt.x, tgt.y, w, h)
            cx, cy = center.x(), center.y()
            tw = tgt.width * w
            th = tgt.height * h
            rad = -math.radians(tgt.rotation)
            dx = pos.x() - cx
            dy = pos.y() - cy
            rx = dx * math.cos(rad) - dy * math.sin(rad)
            ry = dx * math.sin(rad) + dy * math.cos(rad)

            if tgt.type == "circle":
                r = tgt.radius * min(w, h)
                if math.hypot(rx, ry) <= r:
                    return tgt, "body"
            elif tgt.type in ["box", "capsule"]:
                if abs(rx) <= tw * 0.5 and abs(ry) <= th * 0.5:
                    return tgt, "body"
            elif tgt.type == "polygon":
                if math.hypot(dx, dy) <= 40:
                    return tgt, "body"

        return None, None

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        pos = event.position()
        w = float(self.width())
        h = float(self.height())
        target, handle = self._hit_test(pos, w, h)

        if event.button() == Qt.MouseButton.LeftButton:
            if target:
                self.selectTarget(target.id)
                self.active_drag_handle = handle or "body"
                self.drag_start_pos = pos
                self.initial_target_state = {
                    "x": target.x,
                    "y": target.y,
                    "width": target.width,
                    "height": target.height,
                    "radius": target.radius,
                    "rotation": target.rotation,
                    "points": [list(p) for p in target.points],
                }
            else:
                self.active_drag_handle = None

        elif event.button() == Qt.MouseButton.RightButton:
            # Context menu or remove vertex if right clicked on polygon vertex
            if target and handle and handle.startswith("poly_vertex_") and target.type == "polygon":
                idx = int(handle.split("_")[-1])
                if len(target.points) > 3:
                    target.points.pop(idx)
                    self.update()
                    self.targetChanged.emit(target)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            w = float(self.width())
            h = float(self.height())
            target, handle = self._hit_test(pos, w, h)

            if target and target.type == "polygon":
                # Double click inserts a new vertex to polygon
                nx, ny = self._px_to_norm(pos.x(), pos.y(), w, h)
                target.points.append([round(nx, 3), round(ny, 3)])
                self.update()
                self.targetChanged.emit(target)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        pos = event.position()
        w = float(self.width())
        h = float(self.height())

        if self.active_drag_handle and event.buttons() & Qt.MouseButton.LeftButton:
            target = self.getSelectedTarget()
            if not target:
                return

            offset_x = pos.x() - self.drag_start_pos.x()
            offset_y = pos.y() - self.drag_start_pos.y()
            st = self.initial_target_state

            if self.active_drag_handle in ["center", "body"]:
                dnx = offset_x / w
                dny = offset_y / h
                target.x = max(0.05, min(0.95, round(st["x"] + dnx, 3)))
                target.y = max(0.05, min(0.95, round(st["y"] + dny, 3)))

            elif self.active_drag_handle == "resize_se":
                if target.type == "circle":
                    dr = (offset_x + offset_y) / (2 * min(w, h))
                    target.radius = max(0.02, min(0.45, round(st["radius"] + dr, 3)))
                else:
                    dw = (offset_x * 2) / w
                    dh = (offset_y * 2) / h
                    target.width = max(0.05, min(0.8, round(st["width"] + dw, 3)))
                    target.height = max(0.05, min(0.8, round(st["height"] + dh, 3)))

            elif self.active_drag_handle == "rotate":
                center = self._norm_to_px(target.x, target.y, w, h)
                angle = math.degrees(math.atan2(pos.y() - center.y(), pos.x() - center.x())) + 90
                target.rotation = round((angle + 180) % 360 - 180, 1)

            elif self.active_drag_handle.startswith("poly_vertex_"):
                idx = int(self.active_drag_handle.split("_")[-1])
                if idx < len(target.points):
                    dnx = offset_x / w
                    dny = offset_y / h
                    init_pt = st["points"][idx]
                    target.points[idx] = [
                        max(0.0, min(1.0, round(init_pt[0] + dnx, 3))),
                        max(0.0, min(1.0, round(init_pt[1] + dny, 3))),
                    ]

            self.update()
            self.targetChanged.emit(target)
            return

        # Update hover cursor
        target, handle = self._hit_test(pos, w, h)
        if handle == "rotate":
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif handle == "resize_se":
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif handle in ["center", "body"]:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif handle and handle.startswith("poly_vertex_"):
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self.active_drag_handle = None
