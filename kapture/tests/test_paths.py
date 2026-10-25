import unittest
from pathlib import Path
from kapture.core.paths import SCREENSHOTS_DIR, VIDEOS_DIR
from kapture.core.config import Config


class TestPaths(unittest.TestCase):
    def test_default_output_dirs_are_home(self):
        self.assertEqual(SCREENSHOTS_DIR, Path.home())
        self.assertEqual(VIDEOS_DIR, Path.home())

    def test_default_config_dirs_are_home(self):
        cfg = Config()
        self.assertEqual(cfg.get("capture", "screenshots_dir"), str(Path.home()))
        self.assertEqual(cfg.get("capture", "videos_dir"), str(Path.home()))


if __name__ == "__main__":
    unittest.main()
