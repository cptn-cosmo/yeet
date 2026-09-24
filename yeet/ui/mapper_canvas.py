"""
Yeet - Interactive 2D Coordinate Mapper Canvas (GTK4 + Cairo)
App ID: gay.geeks.Yeet
"""

import math
from typing import List, Optional, Callable, Tuple
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import cairo

from ..models import Target

class MapperCanvas(Gtk.DrawingArea):
    def __init__(self, on_target_changed: Optional[Callable[[Target], None]] = None):
        super().__init__()
        self.on_target_changed = on_target_changed
        self.targets: List[Target] = []
        self.selected_target_id: Optional[str] = None
        self.active_spawn_direction: str = "random"
        self.show_grid: bool = True
        self.show_trajectory: bool = True
        self.background_pixbuf = None

        # Drag state tracking
        self.active_drag_handle = None  # None, 'center', 'resize_se', 'rotate', 'poly_vertex_<i>'
        self.drag_start_x = 0.0
        self.drag_start_y = 0.0
        self.initial_target_state = {}

        self.set_content_width(640)
        self.set_content_height(360)
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.set_focusable(True)

        self.set_draw_func(self._draw_func)

        # Gestures for mouse interaction
        click_gesture = Gtk.GestureClick.new()
        click_gesture.set_button(0)  # All mouse buttons
        click_gesture.connect("pressed", self._on_pressed)
        self.add_controller(click_gesture)

        drag_gesture = Gtk.GestureDrag.new()
        drag_gesture.connect("drag-begin", self._on_drag_begin)
        drag_gesture.connect("drag-update", self._on_drag_update)
        drag_gesture.connect("drag-end", self._on_drag_end)
        self.add_controller(drag_gesture)

        motion_controller = Gtk.EventControllerMotion.new()
        motion_controller.connect("motion", self._on_motion)
        self.add_controller(motion_controller)

    def set_targets(self, targets: List[Target], selected_id: Optional[str] = None):
        self.targets = targets
        if selected_id:
            self.selected_target_id = selected_id
        elif targets and not self.selected_target_id:
            self.selected_target_id = targets[0].id
        self.queue_draw()

    def get_selected_target(self) -> Optional[Target]:
        for t in self.targets:
            if t.id == self.selected_target_id:
                return t
        return None

    def select_target(self, target_id: str):
        self.selected_target_id = target_id
        self.queue_draw()

    def set_spawn_direction(self, direction: str):
        self.active_spawn_direction = direction
        self.queue_draw()

    # --- Coordinate Conversion Helpers ---
    def _norm_to_px(self, nx: float, ny: float, w: int, h: int) -> Tuple[float, float]:
        return nx * w, ny * h

    def _px_to_norm(self, px: float, py: float, w: int, h: int) -> Tuple[float, float]:
        return max(0.0, min(1.0, px / w)), max(0.0, min(1.0, py / h))

    # --- GTK4 Drawing Routine ---
    def _draw_func(self, area, cr: cairo.Context, width: int, height: int):
        # 1. Background Fill (Dark Slate Stream Layout)
        cr.set_source_rgb(0.12, 0.12, 0.16)
        cr.paint()

        # Custom Background Image (Stream Screenshot) if loaded
        if self.background_pixbuf:
            cr.save()
            Gdk.cairo_set_source_pixbuf(cr, self.background_pixbuf, 0, 0)
            cr.paint()
            cr.restore()

        # 2. Grid Guidelines (10% increments)
        if self.show_grid:
            cr.save()
            cr.set_source_rgba(0.9, 0.9, 1.0, 0.08)
            cr.set_line_width(1.0)
            cr.set_dash([4.0, 4.0])

            for i in range(1, 10):
                gx = (i / 10.0) * width
                gy = (i / 10.0) * height
                # Vertical grid lines
                cr.move_to(gx, 0)
                cr.line_to(gx, height)
                # Horizontal grid lines
                cr.move_to(0, gy)
                cr.line_to(width, gy)
            cr.stroke()

            # Center Crosshair
            cr.set_source_rgba(0.35, 0.55, 0.95, 0.25)
            cr.set_dash([])
            cr.set_line_width(1.5)
            cr.move_to(width * 0.5, 0)
            cr.line_to(width * 0.5, height)
            cr.move_to(0, height * 0.5)
            cr.line_to(width, height * 0.5)
            cr.stroke()
            cr.restore()

        # 3. Spawn Zone Indicators
        self._draw_spawn_zones(cr, width, height)

        # 4. Trajectory Preview Guide
        if self.show_trajectory:
            self._draw_trajectory(cr, width, height)

        # 5. Render Targets
        for tgt in self.targets:
            is_selected = (tgt.id == self.selected_target_id)
            self._draw_target(cr, tgt, width, height, is_selected)

        # 6. Stream Resolution & Aspect Ratio Badge
        cr.save()
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.45)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(11.0)
        cr.move_to(12, 22)
        cr.show_text(f"16:9 Stream Viewport (OBS) | Normalized Rel [0.0 - 1.0]")
        cr.restore()

    def _draw_spawn_zones(self, cr: cairo.Context, w: int, h: int):
        cr.save()
        dir_name = self.active_spawn_direction.lower()

        # Highlight active spawn edge or emitter
        cr.set_source_rgba(0.96, 0.83, 0.18, 0.4)
        cr.set_line_width(4.0)

        if dir_name in ['left', 'random']:
            cr.move_to(2, 0); cr.line_to(2, h); cr.stroke()
        if dir_name in ['right', 'random']:
            cr.move_to(w - 2, 0); cr.line_to(w - 2, h); cr.stroke()
        if dir_name in ['top', 'random', 'rain']:
            cr.move_to(0, 2); cr.line_to(w, 2); cr.stroke()
        if dir_name in ['bottom', 'random']:
            cr.move_to(0, h - 2); cr.line_to(w, h - 2); cr.stroke()

        cr.restore()

    def _draw_trajectory(self, cr: cairo.Context, w: int, h: int):
        selected = self.get_selected_target()
        if not selected:
            return

        tx, ty = self._norm_to_px(selected.x, selected.y, w, h)
        dir_name = self.active_spawn_direction.lower()

        # Origin point based on spawn direction
        if dir_name == 'left':
            ox, oy = 0, ty
        elif dir_name == 'right':
            ox, oy = w, ty
        elif dir_name in ['top', 'rain']:
            ox, oy = tx, 0
        elif dir_name == 'bottom':
            ox, oy = tx, h
        else:
            ox, oy = 0, ty

        cr.save()
        cr.set_source_rgba(0.96, 0.83, 0.18, 0.6)
        cr.set_line_width(2.0)
        cr.set_dash([6.0, 4.0])

        # Quadratic ballistic curve
        cx = (ox + tx) * 0.5
        cy = min(oy, ty) - 40
        cr.move_to(ox, oy)
        cr.curve_to(cx, cy, cx, ty, tx, ty)
        cr.stroke()

        # Arrowhead at target
        cr.set_dash([])
        cr.set_source_rgba(0.96, 0.83, 0.18, 0.8)
        cr.arc(tx, ty, 5.0, 0, 2 * math.pi)
        cr.fill()
        cr.restore()

    def _draw_target(self, cr: cairo.Context, tgt: Target, w: int, h: int, is_selected: bool):
        cx, cy = self._norm_to_px(tgt.x, tgt.y, w, h)
        tw = tgt.width * w
        th = tgt.height * h

        cr.save()
        cr.translate(cx, cy)
        cr.rotate(math.radians(tgt.rotation))

        # Target colors
        if is_selected:
            fill_rgba = (0.21, 0.52, 0.89, 0.28)
            stroke_rgba = (0.38, 0.63, 0.92, 0.95)
            stroke_width = 2.5
        else:
            fill_rgba = (0.47, 0.49, 0.60, 0.15)
            stroke_rgba = (0.58, 0.60, 0.70, 0.5)
            stroke_width = 1.5

        cr.set_source_rgba(*fill_rgba)
        cr.set_line_width(stroke_width)

        if tgt.type == "box":
            cr.rectangle(-tw * 0.5, -th * 0.5, tw, th)
            cr.fill_preserve()
            cr.set_source_rgba(*stroke_rgba)
            cr.stroke()

        elif tgt.type == "circle":
            r = tgt.radius * min(w, h)
            cr.arc(0, 0, r, 0, 2 * math.pi)
            cr.fill_preserve()
            cr.set_source_rgba(*stroke_rgba)
            cr.stroke()

        elif tgt.type == "capsule":
            # VTuber Pill / Capsule (pill shape)
            r = min(tw, th) * 0.5
            cr.new_sub_path()
            if th >= tw:
                # Vertical capsule
                half_body_h = (th * 0.5) - r
                cr.arc(0, -half_body_h, r, math.pi, 0)
                cr.line_to(r, half_body_h)
                cr.arc(0, half_body_h, r, 0, math.pi)
                cr.line_to(-r, -half_body_h)
            else:
                # Horizontal capsule
                half_body_w = (tw * 0.5) - r
                cr.arc(half_body_w, 0, r, -math.pi / 2, math.pi / 2)
                cr.line_to(-half_body_w, r)
                cr.arc(-half_body_w, 0, r, math.pi / 2, 3 * math.pi / 2)
                cr.line_to(half_body_w, -r)
            cr.close_path()
            cr.fill_preserve()
            cr.set_source_rgba(*stroke_rgba)
            cr.stroke()

        elif tgt.type == "polygon":
            points = tgt.points
            if len(points) >= 3:
                cr.new_sub_path()
                # Points are normalized relative to canvas, convert relative to target center
                for i, pt in enumerate(points):
                    px, py = self._norm_to_px(pt[0], pt[1], w, h)
                    # Translate to center-relative
                    lx, ly = px - cx, py - cy
                    if i == 0:
                        cr.move_to(lx, ly)
                    else:
                        cr.line_to(lx, ly)
                cr.close_path()
                cr.fill_preserve()
                cr.set_source_rgba(*stroke_rgba)
                cr.stroke()

        # Target Name Label
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.85 if is_selected else 0.5)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(12.0)
        extents = cr.text_extents(tgt.name)
        cr.move_to(-extents.width * 0.5, extents.height * 0.5)
        cr.show_text(tgt.name)

        # Draw Interactive Handles if Selected
        if is_selected:
            self._draw_handles(cr, tgt, tw, th, w, h)

        cr.restore()

    def _draw_handles(self, cr: cairo.Context, tgt: Target, tw: float, th: float, w: int, h: int):
        handle_color = (0.21, 0.82, 0.48, 1.0)
        handle_radius = 5.5

        # 1. Center Handle (Drag to move)
        cr.set_source_rgba(*handle_color)
        cr.arc(0, 0, 4.0, 0, 2 * math.pi)
        cr.fill()

        # 2. Resize Corner Handle (Bottom-Right)
        if tgt.type in ["box", "capsule"]:
            cr.arc(tw * 0.5, th * 0.5, handle_radius, 0, 2 * math.pi)
            cr.fill_preserve()
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
            cr.set_line_width(1.5)
            cr.stroke()

        elif tgt.type == "circle":
            r = tgt.radius * min(w, h)
            cr.arc(r, 0, handle_radius, 0, 2 * math.pi)
            cr.fill_preserve()
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
            cr.set_line_width(1.5)
            cr.stroke()

        elif tgt.type == "polygon":
            cx, cy = self._norm_to_px(tgt.x, tgt.y, w, h)
            for i, pt in enumerate(tgt.points):
                px, py = self._norm_to_px(pt[0], pt[1], w, h)
                lx, ly = px - cx, py - cy
                cr.arc(lx, ly, handle_radius, 0, 2 * math.pi)
                cr.fill_preserve()
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
                cr.set_line_width(1.5)
                cr.stroke()

        # 3. Rotation Handle (Top arm)
        cr.set_source_rgba(0.38, 0.63, 0.92, 0.8)
        cr.set_line_width(1.5)
        handle_y = -th * 0.5 - 20 if tgt.type != "circle" else -tgt.radius * min(w, h) - 20
        cr.move_to(0, -th * 0.5 if tgt.type != "circle" else -tgt.radius * min(w, h))
        cr.line_to(0, handle_y)
        cr.stroke()

        cr.set_source_rgba(0.38, 0.63, 0.92, 1.0)
        cr.arc(0, handle_y, handle_radius, 0, 2 * math.pi)
        cr.fill_preserve()
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
        cr.stroke()

    # --- Mouse Interaction Handling ---
    def _hit_test(self, px: float, py: float, w: int, h: int) -> Tuple[Optional[Target], Optional[str]]:
        # Test selected target handles first
        selected = self.get_selected_target()
        if selected:
            cx, cy = self._norm_to_px(selected.x, selected.y, w, h)
            tw = selected.width * w
            th = selected.height * h

            # Rotate coordinates back for handle testing
            rad = -math.radians(selected.rotation)
            dx = px - cx
            dy = py - cy
            rx = dx * math.cos(rad) - dy * math.sin(rad)
            ry = dx * math.sin(rad) + dy * math.cos(rad)

            # Check Rotation Handle
            rot_y = -th * 0.5 - 20 if selected.type != "circle" else -selected.radius * min(w, h) - 20
            if math.hypot(rx, ry - rot_y) <= 12:
                return selected, "rotate"

            # Check Resize Handle
            if selected.type in ["box", "capsule"]:
                if math.hypot(rx - tw * 0.5, ry - th * 0.5) <= 12:
                    return selected, "resize_se"
            elif selected.type == "circle":
                r = selected.radius * min(w, h)
                if math.hypot(rx - r, ry) <= 12:
                    return selected, "resize_se"
            elif selected.type == "polygon":
                for i, pt in enumerate(selected.points):
                    vx, vy = self._norm_to_px(pt[0], pt[1], w, h)
                    if math.hypot(px - vx, py - vy) <= 12:
                        return selected, f"poly_vertex_{i}"

            # Check Center Handle / Target Area
            if math.hypot(rx, ry) <= 12:
                return selected, "center"

        # Check all targets for body click
        for tgt in reversed(self.targets):
            cx, cy = self._norm_to_px(tgt.x, tgt.y, w, h)
            tw = tgt.width * w
            th = tgt.height * h
            rad = -math.radians(tgt.rotation)
            dx = px - cx
            dy = py - cy
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

    def _on_pressed(self, gesture, n_press, x, y):
        w = self.get_width()
        h = self.get_height()
        target, handle = self._hit_test(x, y, w, h)

        if target:
            self.select_target(target.id)
            if n_press == 2 and target.type == "polygon":
                # Double click adds a new vertex to polygon
                nx, ny = self._px_to_norm(x, y, w, h)
                target.points.append([round(nx, 3), round(ny, 3)])
                self.queue_draw()
                if self.on_target_changed:
                    self.on_target_changed(target)

    def _on_drag_begin(self, gesture, start_x, start_y):
        w = self.get_width()
        h = self.get_height()
        target, handle = self._hit_test(start_x, start_y, w, h)

        if target:
            self.select_target(target.id)
            self.active_drag_handle = handle or "body"
            self.drag_start_x = start_x
            self.drag_start_y = start_y
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

    def _on_drag_update(self, gesture, offset_x, offset_y):
        if not self.active_drag_handle:
            return

        target = self.get_selected_target()
        if not target:
            return

        w = self.get_width()
        h = self.get_height()
        st = self.initial_target_state

        if self.active_drag_handle in ["center", "body"]:
            # Move entire target
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
            cx, cy = self._norm_to_px(target.x, target.y, w, h)
            curr_x = self.drag_start_x + offset_x
            curr_y = self.drag_start_y + offset_y
            angle = math.degrees(math.atan2(curr_y - cy, curr_x - cx)) + 90
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

        self.queue_draw()
        if self.on_target_changed:
            self.on_target_changed(target)

    def _on_drag_end(self, gesture, offset_x, offset_y):
        self.active_drag_handle = None

    def _on_motion(self, controller, x, y):
        # Update cursor on handle hover
        w = self.get_width()
        h = self.get_height()
        target, handle = self._hit_test(x, y, w, h)

        if handle == "rotate":
            self.set_cursor(Gdk.Cursor.new_from_name("crosshair", None))
        elif handle == "resize_se":
            self.set_cursor(Gdk.Cursor.new_from_name("nwse-resize", None))
        elif handle in ["center", "body"]:
            self.set_cursor(Gdk.Cursor.new_from_name("grab", None))
        elif handle and handle.startswith("poly_vertex_"):
            self.set_cursor(Gdk.Cursor.new_from_name("move", None))
        else:
            self.set_cursor(None)
