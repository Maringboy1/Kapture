import os
import subprocess
import tempfile
import time
import shutil
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal, QElapsedTimer, QTimer

from kapture.core import audio, windows
from kapture.core.geometry import even
from kapture.core.paths import TMP_DIR, VIDEOS_DIR, ensure_dirs
from kapture.core.logging import get_logger

log = get_logger("recorder")


def _proc_alive(p):
    return p is not None and p.poll() is None


class Segment:
    def __init__(self, path):
        self.path = path
        self.start = time.time()


class RecordingSession(QObject):
    tick = pyqtSignal(int)          # elapsed ms
    state_changed = pyqtSignal(str)  # recording/paused/stopped
    error = pyqtSignal(str)
    finished = pyqtSignal(str)       # output path

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.mode = "full"
        self.target = {}   # full: screen; region: rect; window: wid
        self.segments = []
        self.current_proc = None
        self.current_path = None
        self.state = "idle"
        self.paused = False
        self.auto_paused = False
        self.timer = QElapsedTimer()
        self.active_ms = 0
        self.segment_start_ms = 0
        self.session_dir = None
        self.output_path = None
        self._t = None
        self._tick_timer = QTimer()
        self._tick_timer.setInterval(250)
        self._tick_timer.timeout.connect(self._on_tick)
        self._watch_timer = QTimer()
        self._watch_timer.setInterval(500)
        self._watch_timer.timeout.connect(self._watch)
        self._last_window_geom = None
        self._last_window_state = None

    # ---------- public API ----------
    def start(self, mode, target):
        if self.state != "idle":
            return
        ensure_dirs()
        self.mode = mode
        self.target = target
        self.segments = []
        self.active_ms = 0
        self.session_dir = Path(tempfile.mkdtemp(prefix="session_", dir=str(TMP_DIR)))
        self.state = "recording"
        self.paused = False
        self.auto_paused = False
        self.timer.start()
        self.segment_start_ms = 0
        self._start_segment()
        self._tick_timer.start()
        if mode == "window":
            self._watch_timer.start()
            w = windows.window_by_id(target.get("wid"))
            if w:
                self._last_window_geom = (w["x"], w["y"], w["w"], w["h"])
        self.state_changed.emit("recording")

    def pause(self):
        if self.state != "recording" or self.paused:
            return
        self._stop_current_segment()
        self.active_ms += self.timer.elapsed() - self.segment_start_ms
        self.paused = True
        self.state = "paused"
        self.state_changed.emit("paused")

    def resume(self):
        if self.state != "paused":
            return
        self.paused = False
        self.state = "recording"
        self.segment_start_ms = self.timer.elapsed()
        self._start_segment()
        self.state_changed.emit("recording")

    def stop(self, cancel=False):
        if self.state == "idle":
            return
        self._tick_timer.stop()
        self._watch_timer.stop()
        if self.current_proc is not None:
            self._stop_current_segment()
            if not cancel and self.state == "recording":
                self.active_ms += self.timer.elapsed() - self.segment_start_ms
        if cancel:
            self._cleanup()
            self.state = "idle"
            self.state_changed.emit("stopped")
            return
        # finalize
        self.state = "finalizing"
        self.state_changed.emit("finalizing")
        out = self._finalize()
        self._cleanup(keep=(out is not None))
        self.state = "idle"
        if out:
            self.output_path = out
            self.finished.emit(out)
        else:
            self.error.emit("finalization failed")
            self.state_changed.emit("stopped")

    def elapsed_ms(self):
        if self.state == "recording":
            return self.active_ms + (self.timer.elapsed() - self.segment_start_ms)
        return self.active_ms

    # ---------- internals ----------
    def _start_segment(self):
        idx = len(self.segments)
        path = self.session_dir / f"segment_{idx}.mkv"
        self.current_path = path
        cmd = self._build_cmd(path)
        log.debug("ffmpeg cmd: %s", " ".join(cmd))
        try:
            self.current_proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=(self.session_dir / f"segment_{idx}.log").open("w"),
            )
        except Exception as e:
            self.error.emit(str(e))
            self.state = "idle"
            return
        self.segments.append(Segment(path))
        self.segment_start_ms = self.timer.elapsed()

    def _stop_current_segment(self):
        p = self.current_proc
        if p is None:
            return
        try:
            if p.stdin:
                p.stdin.write(b"q\n")
                p.stdin.flush()
        except Exception:
            pass
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.terminate()
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()
        self.current_proc = None

    def _build_cmd(self, out_path):
        cfg = self.cfg
        fps = int(cfg.get("recording", "fps", default=30))
        crf = int(cfg.get("recording", "crf", default=20))
        preset = cfg.get("recording", "preset", default="veryfast")
        cursor = bool(cfg.get("capture", "cursor", default=True))
        audio_mode = cfg.get("recording", "audio", default="desktop")
        mode = self.mode
        target = self.target

        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        # video input
        if mode == "full":
            from PyQt6.QtWidgets import QApplication
            screens = QApplication.screens()
            idx = int(cfg.get("capture", "screen_index", default=0))
            idx = max(0, min(len(screens) - 1, idx))
            g = screens[idx].geometry()
            x, y, w, h = g.x(), g.y(), g.width(), g.height()
            w, h = even(w), even(h)
            cmd += ["-thread_queue_size", "1024", "-f", "x11grab", "-framerate", str(fps)]
            if not cursor:
                cmd += ["-draw_mouse", "0"]
            cmd += ["-video_size", f"{w}x{h}", "-i", f":0.0+{x},{y}"]
        elif mode == "region":
            rx, ry, rw, rh = target["x"], target["y"], target["w"], target["h"]
            rw, rh = even(rw), even(rh)
            cmd += ["-thread_queue_size", "1024", "-f", "x11grab", "-framerate", str(fps)]
            if not cursor:
                cmd += ["-draw_mouse", "0"]
            cmd += ["-video_size", f"{rw}x{rh}", "-i", f":0.0+{rx},{ry}"]
        elif mode == "window":
            wid = target["wid"]
            cmd += ["-thread_queue_size", "1024", "-f", "x11grab", "-window_id", str(wid), "-framerate", str(fps)]
            if not cursor:
                cmd += ["-draw_mouse", "0"]
            cmd += ["-i", ":0.0"]

        # audio inputs
        audio_inputs = []
        if audio_mode in ("desktop", "both"):
            dev = self.cfg.get("recording", "desktop_device", default=None)
            src = dev if dev and any(s["name"] == dev for s in audio.list_sources()) else audio.desktop_source()
            if src:
                audio_inputs.append(("desktop", src))
        if audio_mode in ("mic", "both"):
            dev = self.cfg.get("recording", "mic_device", default=None)
            src = dev if dev and any(s["name"] == dev for s in audio.list_sources()) else audio.mic_source()
            if src:
                audio_inputs.append(("mic", src))
        for _, src in audio_inputs:
            cmd += ["-thread_queue_size", "512", "-f", "pulse", "-i", src]

        n_audio = len(audio_inputs)
        if n_audio >= 2:
            cmd += ["-filter_complex", f"[1:a][2:a]amix=inputs={n_audio}:duration=longest[aout]"]

        if mode == "window":
            cmd += ["-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2"]

        cmd += ["-map", "0:v"]
        if n_audio == 0:
            cmd += ["-an"]
        elif n_audio == 1:
            cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", "160k"]
        else:
            cmd += ["-map", "[aout]", "-c:a", "aac", "-b:a", "160k"]

        cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p"]
        cmd += ["-f", "matroska", str(out_path)]
        return cmd

    def _cleanup(self, keep=False):
        if self.session_dir and self.session_dir.exists():
            if not keep:
                shutil.rmtree(self.session_dir, ignore_errors=True)
            # if keep, leave for recovery

    def _finalize(self):
        # concat segments
        if not self.segments:
            return None
        valid = [s for s in self.segments if s.path.exists() and s.path.stat().st_size > 0]
        if not valid:
            return None
        out_dir = Path(self.cfg.get("capture", "videos_dir") or str(VIDEOS_DIR))
        out_dir.mkdir(parents=True, exist_ok=True)
        target_fmt = self.cfg.get("recording", "format", default="mp4").lower()
        if target_fmt == "webm":
            ext = "webm"
        elif target_fmt == "gif":
            ext = "gif"
        else:
            ext = "mp4"
        i = 1
        while (out_dir / f"video{i:02d}.{ext}").exists():
            i += 1
        out_path = out_dir / f"video{i:02d}.{ext}"

        # concat list
        list_file = self.session_dir / "concat.txt"
        with list_file.open("w") as f:
            for s in valid:
                f.write(f"file '{s.path.resolve()}'\n")

        # intermediate mkv
        inter = self.session_dir / "concat.mkv"
        rc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
             "-i", str(list_file), "-c", "copy", str(inter)],
            capture_output=True,
        )
        if rc.returncode != 0 or not inter.exists():
            # try re-encode
            rc = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                 "-i", str(list_file), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(inter)],
                capture_output=True,
            )
            if rc.returncode != 0 or not inter.exists():
                return None

        if target_fmt == "gif":
            # palette
            palette = self.session_dir / "palette.png"
            subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(inter),
                 "-vf", f"fps={self.cfg.get('recording','gif_fps',default=15)},scale={self.cfg.get('recording','gif_width',default=960)}:-1:flags=lanczos,palettegen",
                 str(palette)],
                capture_output=True,
            )
            rc = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(inter),
                 "-i", str(palette),
                 "-filter_complex", f"fps={self.cfg.get('recording','gif_fps',default=15)},scale={self.cfg.get('recording','gif_width',default=960)}:-1:flags=lanczos[x];[x][1:v]paletteuse",
                 str(out_path)],
                capture_output=True,
            )
        elif target_fmt == "webm":
            rc = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(inter),
                 "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-c:a", "libopus", "-b:a", "128k",
                 str(out_path)],
                capture_output=True,
            )
        else:
            rc = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(inter),
                 "-c", "copy", "-movflags", "+faststart", str(out_path)],
                capture_output=True,
            )
            if rc.returncode != 0:
                rc = subprocess.run(
                    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(inter),
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", str(self.cfg.get("recording","crf",default=20)),
                     "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out_path)],
                    capture_output=True,
                )

        if rc.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
            return None
        # validate
        vrc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=index", "-of", "csv=p=0", str(out_path)],
            capture_output=True, text=True,
        )
        if vrc.returncode != 0 or not vrc.stdout.strip():
            return None
        return str(out_path)

    def _on_tick(self):
        if self.state == "recording":
            self.tick.emit(self.elapsed_ms())

    def _watch(self):
        if self.mode != "window":
            return
        wid = self.target.get("wid")
        if not windows.is_viewable(wid):
            if not self.paused and self.state == "recording":
                self.auto_paused = True
                self.pause()
                from kapture.core.notify import notify
                notify("Kapture", "Window minimized - recording paused")
            return
        # auto-resume
        if self.paused and self.auto_paused:
            self.auto_paused = False
            self.resume()
        # resize detection
        w = windows.window_by_id(wid)
        if w:
            g = (w["x"], w["y"], w["w"], w["h"])
            if self._last_window_geom is not None and g != self._last_window_geom:
                # split segment
                if self.state == "recording" and not self.paused:
                    self._stop_current_segment()
                    self.active_ms += self.timer.elapsed() - self.segment_start_ms
                    self.segment_start_ms = self.timer.elapsed()
                    self._start_segment()
            self._last_window_geom = g

    def _cleanup(self, keep=False):
        if keep:
            return
        if self.session_dir and self.session_dir.exists():
            import shutil
            shutil.rmtree(self.session_dir, ignore_errors=True)
