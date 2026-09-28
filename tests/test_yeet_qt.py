"""
Yeet - Qt6 / KDE 6 Automated Test Suite
"""

import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure offscreen Qt platform for headless testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from yeet.config import ConfigManager
from yeet.server import ServerDaemon
from yeet.app import YeetApplication
from yeet.ui.window import YeetWindow
from yeet.ui.about_dialog import AboutDialog
from yeet.models import Target
from PySide6.QtCore import QPointF

class TestYeetQt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = YeetApplication(["yeet", "-platform", "offscreen"])
        cls.cfg = ConfigManager()
        cls.daemon = ServerDaemon(cls.cfg)
        cls.win = YeetWindow(cls.cfg, cls.daemon)

    def test_window_initialization(self):
        self.assertIsNotNone(self.win)
        self.assertEqual(self.win.view_stack.count(), 4)
        self.assertEqual(self.win.nav_list.count(), 4)

    def test_target_manipulation(self):
        tv = self.win.target_view
        initial_len = len(self.cfg.targets)
        tv._on_add_target("box")
        self.assertEqual(len(self.cfg.targets), initial_len + 1)

        new_target = self.cfg.targets[-1]
        self.assertEqual(new_target.type, "box")

        # Edit property via spinbox
        tv.canvas.selectTarget(new_target.id)
        tv.pos_x_spin.setValue(0.65)
        self.assertAlmostEqual(new_target.x, 0.65)

        # Hit test
        w = float(tv.canvas.width())
        h = float(tv.canvas.height())
        target, handle = tv.canvas._hit_test(QPointF(new_target.x * w, new_target.y * h), w, h)
        self.assertIsNotNone(target)

    def test_items_view(self):
        iv = self.win.items_view
        it = iv._get_current_item()
        self.assertIsNotNone(it)
        orig_scale = it.scale
        iv.scale_spin.setValue(0.14)
        self.assertEqual(it.scale, 0.14)
        iv.scale_spin.setValue(orig_scale)

    def test_physics_view(self):
        pv = self.win.physics_view
        pv.dir_combo.setCurrentIndex(1)  # left
        self.assertEqual(self.cfg.physics.default_spawn_direction, "left")
        pv.force_spin.setValue(2.5)
        self.assertEqual(self.cfg.physics.default_force, 2.5)

    def test_server_view_and_webhooks(self):
        sv = self.win.server_view
        expected_url = f"http://{self.cfg.server.host}:{self.cfg.server.port}/overlay"
        self.assertEqual(sv.get_overlay_url(), expected_url)

        sv.wh_enabled_check.setChecked(True)
        self.assertTrue(self.cfg.webhooks.enabled)

    def test_about_dialog(self):
        dialog = AboutDialog(self.win)
        self.assertEqual(dialog.windowTitle(), "About Yeet")

if __name__ == "__main__":
    unittest.main()
