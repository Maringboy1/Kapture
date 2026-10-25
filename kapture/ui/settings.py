from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox, QCheckBox, QFileDialog,
    QFormLayout, QGroupBox,
)

from kapture.ui.icons import icon as I


class SettingsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle("Kapture Settings")
        self.resize(720, 520)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        top = QHBoxLayout()
        self.list = QListWidget()
        self.list.setFixedWidth(150)
        for name in ("General", "Capture", "Recording", "Audio", "Hotkeys", "Appearance", "About"):
            self.list.addItem(name)
        top.addWidget(self.list)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._general_page())
        self.stack.addWidget(self._capture_page())
        self.stack.addWidget(self._recording_page())
        self.stack.addWidget(self._audio_page())
        self.stack.addWidget(self._hotkeys_page())
        self.stack.addWidget(self._appearance_page())
        self.stack.addWidget(self._about_page())
        top.addWidget(self.stack, 1)
        outer.addLayout(top)
        self.list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.list.setCurrentRow(0)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(close_btn)
        outer.addLayout(btns)
        # attach to last page? Instead add bottom bar
        wrapper = QVBoxLayout()
        # restructure: put stack+buttons in vertical
        pass

    def _page(self):
        w = QWidget()
        return w, QVBoxLayout(w)

    def _general_page(self):
        w, v = self._page()
        g = QGroupBox("General")
        f = QFormLayout(g)
        self.screenshots_dir = QLineEdit(self.cfg.get("capture", "screenshots_dir", default=""))
        b = QPushButton("Browse")
        b.clicked.connect(lambda: self._browse(self.screenshots_dir))
        row = QHBoxLayout()
        row.addWidget(self.screenshots_dir)
        row.addWidget(b)
        w2 = QWidget()
        w2.setLayout(row)
        f.addRow("Screenshots folder", w2)
        self.videos_dir = QLineEdit(self.cfg.get("capture", "videos_dir", default=""))
        b2 = QPushButton("Browse")
        b2.clicked.connect(lambda: self._browse(self.videos_dir))
        row2 = QHBoxLayout()
        row2.addWidget(self.videos_dir)
        row2.addWidget(b2)
        w3 = QWidget()
        w3.setLayout(row2)
        f.addRow("Videos folder", w3)
        self.reduced_motion = QCheckBox("Reduce motion")
        self.reduced_motion.setChecked(self.cfg.get("ui", "reduced_motion", default=False))
        f.addRow("", self.reduced_motion)
        v.addWidget(g)
        v.addStretch()
        return w

    def _capture_page(self):
        w, v = self._page()
        g = QGroupBox("Capture")
        f = QFormLayout(g)
        self.cursor_cb = QCheckBox("Include cursor by default")
        self.cursor_cb.setChecked(self.cfg.get("capture", "cursor", default=True))
        f.addRow("", self.cursor_cb)
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 30)
        self.delay_spin.setValue(self.cfg.get("capture", "delay", default=0))
        f.addRow("Default delay (s)", self.delay_spin)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpg", "webp"])
        self.format_combo.setCurrentText(self.cfg.get("capture", "format", default="png"))
        f.addRow("Image format", self.format_combo)
        v.addWidget(g)
        v.addStretch()
        return w

    def _recording_page(self):
        w, v = self._page()
        g = QGroupBox("Recording")
        f = QFormLayout(g)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(10, 60)
        self.fps_spin.setValue(self.cfg.get("recording", "fps", default=30))
        f.addRow("FPS", self.fps_spin)
        self.crf_spin = QSpinBox()
        self.crf_spin.setRange(10, 40)
        self.crf_spin.setValue(self.cfg.get("recording", "crf", default=20))
        f.addRow("CRF", self.crf_spin)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium"])
        self.preset_combo.setCurrentText(self.cfg.get("recording", "preset", default="veryfast"))
        f.addRow("Preset", self.preset_combo)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mkv", "webm", "gif"])
        self.format_combo.setCurrentText(self.cfg.get("recording", "format", default="mp4"))
        f.addRow("Format", self.format_combo)
        self.maxdur_spin = QSpinBox()
        self.maxdur_spin.setRange(0, 36000)
        self.maxdur_spin.setValue(self.cfg.get("recording", "max_duration", default=0))
        self.maxdur_spin.setSuffix(" s (0=unlimited)")
        f.addRow("Max duration", self.maxdur_spin)
        self.hud_cb = QCheckBox("Show HUD")
        self.hud_cb.setChecked(self.cfg.get("recording", "show_hud", default=True))
        f.addRow("", self.hud_cb)
        self.hidehud_full_cb = QCheckBox("Hide HUD for fullscreen recording")
        self.hidehud_full_cb.setChecked(self.cfg.get("recording", "hide_hud_fullscreen", default=True))
        f.addRow("", self.hidehud_full_cb)
        v.addWidget(g)
        v.addStretch()
        return w

    def _audio_page(self):
        w, v = self._page()
        g = QGroupBox("Audio")
        f = QFormLayout(g)
        self.audio_combo = QComboBox()
        self.audio_combo.addItems(["none", "desktop", "mic", "both"])
        self.audio_combo.setCurrentText(self.cfg.get("recording", "audio", default="desktop"))
        f.addRow("Source", self.audio_combo)
        from kapture.core import audio
        devs = audio.list_sources()
        self.desktop_dev = QComboBox()
        self.desktop_dev.addItems([s["name"] for s in audio.monitor_sources()])
        cur = audio.desktop_source()
        if cur:
            self.desktop_dev.setCurrentText(cur)
        f.addRow("Desktop device", self.desktop_dev)
        self.mic_dev = QComboBox()
        self.mic_dev.addItems([s["name"] for s in audio.mic_sources()])
        curm = audio.mic_source()
        if curm:
            self.mic_dev.setCurrentText(curm)
        f.addRow("Mic device", self.mic_dev)
        v.addWidget(g)
        v.addStretch()
        return w

    def _hotkeys_page(self):
        w, v = self._page()
        g = QGroupBox("Hotkeys")
        f = QFormLayout(g)
        self.hk_enabled = QCheckBox("Enable global hotkeys")
        self.hk_enabled.setChecked(self.cfg.get("hotkeys", "enabled", default=True))
        f.addRow("", self.hk_enabled)
        self.hk_full = QLineEdit(self.cfg.get("hotkeys", "full", default="Super+Print"))
        f.addRow("Full screenshot", self.hk_full)
        self.hk_region = QLineEdit(self.cfg.get("hotkeys", "region", default="Ctrl+Alt+S"))
        f.addRow("Region screenshot", self.hk_region)
        self.hk_window = QLineEdit(self.cfg.get("hotkeys", "window", default="Ctrl+Alt+W"))
        f.addRow("Window screenshot", self.hk_window)
        self.hk_record = QLineEdit(self.cfg.get("hotkeys", "record", default="Ctrl+Alt+R"))
        f.addRow("Toggle recording", self.hk_record)
        note = QLabel("If a key is already grabbed by XFCE, Kapture disables it and shows a toast. No XFCE settings are changed.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#9aa4b2; font-size:9pt;")
        f.addRow("", note)
        v.addWidget(g)
        v.addStretch()
        return w

    def _appearance_page(self):
        w, v = self._page()
        g = QGroupBox("Appearance")
        f = QFormLayout(g)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.cfg.get("ui", "theme", default="dark"))
        f.addRow("Theme", self.theme_combo)
        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["#3b82f6", "#8b5cf6", "#22c55e", "#f97316", "#ef4444", "#06b6d4"])
        self.accent_combo.setCurrentText(self.cfg.get("ui", "accent", default="#3b82f6"))
        f.addRow("Accent", self.accent_combo)
        v.addWidget(g)
        v.addStretch()
        return w

    def _about_page(self):
        w, v = self._page()
        v.addWidget(QLabel("Kapture 1.0.0"))
        v.addWidget(QLabel("Modern screenshot and screen recording for Kali Linux (X11)."))
        v.addWidget(QLabel("Dependencies: PyQt6, Pillow, numpy, ffmpeg, xdotool, wmctrl, xclip (all preinstalled)."))
        v.addStretch()
        return w

    def _browse(self, edit):
        d = QFileDialog.getExistingDirectory(self, "Select folder", edit.text())
        if d:
            edit.setText(d)

    def _save(self):
        self.cfg.set("capture", "screenshots_dir", value=self.screenshots_dir.text())
        self.cfg.set("capture", "videos_dir", value=self.videos_dir.text())
        self.cfg.set("capture", "cursor", value=self.cursor_cb.isChecked())
        self.cfg.set("capture", "delay", value=self.delay_spin.value())
        self.cfg.set("capture", "format", value=self.format_combo.currentText())
        self.cfg.set("recording", "fps", value=self.fps_spin.value())
        self.cfg.set("recording", "crf", value=self.crf_spin.value())
        self.cfg.set("recording", "preset", value=self.preset_combo.currentText())
        self.cfg.set("recording", "format", value=self.format_combo.currentText())
        self.cfg.set("recording", "max_duration", value=self.maxdur_spin.value())
        self.cfg.set("recording", "show_hud", value=self.hud_cb.isChecked())
        self.cfg.set("recording", "hide_hud_fullscreen", value=self.hidehud_full_cb.isChecked())
        self.cfg.set("recording", "audio", value=self.audio_combo.currentText())
        self.cfg.set("recording", "desktop_device", value=self.desktop_dev.currentText())
        self.cfg.set("recording", "mic_device", value=self.mic_dev.currentText())
        self.cfg.set("hotkeys", "enabled", value=self.hk_enabled.isChecked())
        self.cfg.set("hotkeys", "full", value=self.hk_full.text())
        self.cfg.set("hotkeys", "region", value=self.hk_region.text())
        self.cfg.set("hotkeys", "window", value=self.hk_window.text())
        self.cfg.set("hotkeys", "record", value=self.hk_record.text())
        self.cfg.set("ui", "theme", value=self.theme_combo.currentText())
        self.cfg.set("ui", "accent", value=self.accent_combo.currentText())
        self.cfg.set("ui", "reduced_motion", value=self.reduced_motion.isChecked())
        self.accept()
