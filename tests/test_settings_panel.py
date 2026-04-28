from __future__ import annotations

import os
import sys
import unittest

from PyQt6.QtWidgets import QApplication

from personacore.gui.widgets.settings_panel import SettingsPanel

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class SettingsPanelTests(unittest.TestCase):
    _app: QApplication | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def test_panel_constructs_backend_combo(self) -> None:
        panel = SettingsPanel()

        self.assertEqual(panel.get_selected_backend(), "demo")
        self.assertEqual(panel._seed_spin.minimum(), -1)
        self.assertEqual(panel._seed_spin.maximum(), 2**31 - 1)

    def test_unavailable_backend_items_are_disabled(self) -> None:
        panel = SettingsPanel()

        panel.set_backends([
            ("demo", "Demo", True),
            ("zeroscope", "Zeroscope", False),
        ])

        unavailable_item = panel._backend_model.item(1)
        self.assertIsNotNone(unavailable_item)
        self.assertFalse(unavailable_item.isEnabled())

    def test_generation_params_keep_resolution_tuple_flat(self) -> None:
        panel = SettingsPanel()
        params = panel.build_generation_params("a test prompt")

        self.assertEqual(params.resolution, (512, 512))
        self.assertEqual(params.width, 512)
        self.assertEqual(params.height, 512)


if __name__ == "__main__":
    unittest.main()
