"""
Yeet - Qt6 / KDE 6 Automated Test Suite
"""

import os
import sys
import tempfile
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create an isolated temporary directory for test configuration
# MUST be set before importing yeet or creating ConfigManager so real user config (~/.config/yeet) is never touched
_test_tmp_dir = tempfile.TemporaryDirectory()
os.environ["XDG_CONFIG_HOME"] = _test_tmp_dir.name

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

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "daemon") and cls.daemon:
            cls.daemon.stop()
        if hasattr(cls, "win") and cls.win:
            cls.win.close()
        _test_tmp_dir.cleanup()

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

        # Clean up added target so tests remain idempotent
        self.cfg.targets.remove(new_target)
        self.cfg.save()
        tv.refresh_from_config()
        self.assertEqual(len(self.cfg.targets), initial_len)

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

    def test_item_ids_api(self):
        import asyncio
        from unittest.mock import MagicMock
        import json

        # Test default comma-separated list
        req = MagicMock()
        req.query = {}
        res = asyncio.run(self.daemon.handle_get_item_ids(req))
        self.assertEqual(res.status, 200)
        self.assertEqual(res.content_type, "text/plain")
        expected_ids = list(self.cfg.items.keys())
        self.assertEqual(res.text, ", ".join(expected_ids))

        # Test custom separator (e.g. ?sep=,)
        req_sep = MagicMock()
        req_sep.query = {"sep": ","}
        res_sep = asyncio.run(self.daemon.handle_get_item_ids(req_sep))
        self.assertEqual(res_sep.text, ",".join(expected_ids))

        # Test group filtering (e.g. ?group=food)
        req_grp = MagicMock()
        req_grp.query = {"group": "food"}
        res_grp = asyncio.run(self.daemon.handle_get_item_ids(req_grp))
        food_ids = [it.id for it in self.cfg.items.values() if it.group == "food"]
        self.assertEqual(res_grp.text, ", ".join(food_ids))

        # Test JSON format (e.g. ?format=json)
        req_json = MagicMock()
        req_json.query = {"format": "json"}
        res_json = asyncio.run(self.daemon.handle_get_item_ids(req_json))
        data = json.loads(res_json.body.decode("utf-8"))
        self.assertEqual(data["ids"], expected_ids)
        self.assertEqual(data["count"], len(expected_ids))

        # Test handle_get_items with format=csv
        req_items_csv = MagicMock()
        req_items_csv.query = {"format": "csv"}
        res_items_csv = asyncio.run(self.daemon.handle_get_items(req_items_csv))
        self.assertEqual(res_items_csv.text, ", ".join(expected_ids))

    def test_about_dialog(self):
        dialog = AboutDialog(self.win)
        self.assertEqual(dialog.windowTitle(), "About Yeet")

if __name__ == "__main__":
    unittest.main()
