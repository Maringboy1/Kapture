import json
import shutil
from pathlib import Path

from kapture.core.paths import CONFIG_FILE, SCREENSHOTS_DIR, VIDEOS_DIR, ensure_dirs

DEFAULT_CONFIG = {
    "version": 1,
    "ui": {
        "theme": "dark",
        "accent": "#3b82f6",
        "popup_x": None,
        "popup_y": None,
        "popup_pinned": False,
        "reduced_motion": False,
        "window_decorations": False,
    },
    "capture": {
        "screenshots_dir": str(SCREENSHOTS_DIR),
        "videos_dir": str(VIDEOS_DIR),
        "cursor": True,
        "delay": 0,
        "format": "png",
        "jpeg_quality": 95,
        "screen_index": 0,
    },
    "recording": {
        "fps": 30,
        "crf": 20,
        "preset": "veryfast",
        "audio": "desktop",
        "show_hud": True,
        "hide_hud_fullscreen": True,
        "max_duration": 0,
        "include_titlebar": False,
        "gif_fps": 15,
        "gif_width": 960,
    },
    "hotkeys": {
        "enabled": True,
        "full": "Super+Print",
        "region": "Ctrl+Alt+S",
        "window": "Ctrl+Alt+W",
        "record": "Ctrl+Alt+R",
    },
    "annotator": {
        "color": "#ff3b30",
        "width": 3,
        "font_size": 18,
    },
}


class Config:
    def __init__(self):
        ensure_dirs()
        self.data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        try:
            if CONFIG_FILE.exists():
                raw = json.loads(CONFIG_FILE.read_text())
                self._merge(self.data, raw)
        except Exception:
            self.data = dict(DEFAULT_CONFIG)

    def _merge(self, base, incoming):
        for k, v in incoming.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                self._merge(base[k], v)
            else:
                base[k] = v

    def save(self):
        ensure_dirs()
        tmp = CONFIG_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2))
        shutil.move(str(tmp), str(CONFIG_FILE))

    def get(self, *keys, default=None):
        cur = self.data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def set(self, *keys, value):
        cur = self.data
        for k in keys[:-1]:
            cur = cur.setdefault(k, {})
        cur[keys[-1]] = value
        self.save()
