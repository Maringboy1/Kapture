import subprocess
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

from kapture.core import audio, windows
from kapture.core.geometry import even, clamp, rect_tuple
from kapture.core.paths import SCREENSHOTS_DIR, ensure_dirs
from kapture.core.logging import get_logger

log = get_logger("capture")


def _ffmpeg_png(args, timeout=20):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error"] + args + ["-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except Exception as e:
        return None, str(e)
    if r.returncode != 0 or not r.stdout:
        return None, r.stderr.decode("utf-8", "replace")
    return r.stdout, None


def capture_full(screen_index=0, cursor=True, delay=0):
    if delay and delay > 0:
        time.sleep(delay)
    from PyQt6.QtWidgets import QApplication
    screens = QApplication.screens()
    idx = clamp(screen_index, 0, max(0, len(screens) - 1))
    scr = screens[idx]
    g = scr.geometry()
    x, y, w, h = g.x(), g.y(), g.width(), g.height()
    args = ["-f", "x11grab", "-video_size", f"{w}x{h}", "-i", f":0.0+{x},{y}"]
    if not cursor:
        args = ["-f", "x11grab", "-draw_mouse", "0", "-video_size", f"{w}x{h}", "-i", f":0.0+{x},{y}"]
    return _ffmpeg_png(args)


def capture_region(rx, ry, rw, rh, cursor=False, delay=0):
    if delay and delay > 0:
        time.sleep(delay)
    # capture the region directly
    w, h = even(rw), even(rh)
    x, y = rx, ry
    args = ["-f", "x11grab", "-video_size", f"{w}x{h}", "-i", f":0.0+{x},{y}"]
    if not cursor:
        args = ["-f", "x11grab", "-draw_mouse", "0", "-video_size", f"{w}x{h}", "-i", f":0.0+{x},{y}"]
    data, err = _ffmpeg_png(args)
    if data is None and err:
        # fallback: capture virtual desktop then crop with PIL
        from kapture.core.geometry import union_rects
        import io
        from PIL import Image
        vg = virtual_geometry()
        vx, vy, vw, vh = vg
        args2 = ["-f", "x11grab", "-video_size", f"{vw}x{vh}", "-i", f":0.0+{vx},{vy}"]
        data2, err2 = _ffmpeg_png(args2)
        if data2 is None:
            return None, err2 or err
        im = Image.open(io.BytesIO(data2))
        crop = im.crop((rx - vx, ry - vy, rx - vx + rw, ry - vy + rh))
        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        return buf.getvalue(), None
    return data, err


def virtual_geometry():
    from PyQt6.QtWidgets import QApplication
    screens = QApplication.screens()
    rects = [(s.geometry().x(), s.geometry().y(), s.geometry().width(), s.geometry().height()) for s in screens]
    from kapture.core.geometry import union_rects
    return union_rects(rects)


def capture_window(wid, cursor=True, delay=0, include_titlebar=False):
    if delay and delay > 0:
        time.sleep(delay)
    if not windows.is_viewable(wid):
        return None, "window is not visible"
    args = ["-f", "x11grab", "-window_id", str(wid)]
    if not cursor:
        args += ["-draw_mouse", "0"]
    args += ["-i", ":0.0"]
    data, err = _ffmpeg_png(args)
    if data is None:
        # fallback crop from screen
        w = windows.window_by_id(wid)
        if w:
            x, y, ww, hh = w["x"], w["y"], w["w"], w["h"]
            # include titlebar via frame extents top
            if include_titlebar:
                fe = w.get("frame", (0, 0, 0, 0))
                y -= fe[2]
                hh += fe[2] + fe[3]
                x -= fe[0]
                ww += fe[0] + fe[1]
            return capture_region(x, y, ww, hh, cursor=cursor)
    return data, err


def save_bytes(data, directory, prefix="photo", ext="png", fmt=None):
    ensure_dirs()
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    i = 1
    while (d / f"{prefix}{i:02d}.{ext}").exists():
        i += 1
    path = d / f"{prefix}{i:02d}.{ext}"
    if fmt and fmt.lower() not in ("png",):
        img = bytes_to_qimage(data)
        img.save(str(path), fmt.upper())
    else:
        path.write_bytes(data)
    return path


def bytes_to_qimage(data):
    img = QImage()
    img.loadFromData(data)
    return img


class CaptureWorker(QThread):
    finished = pyqtSignal(object, object)  # (path_or_bytes, error)

    def __init__(self, mode, **kwargs):
        super().__init__()
        self.mode = mode
        self.kwargs = kwargs

    def run(self):
        try:
            delay = self.kwargs.get("delay", 0)
            if self.mode == "full":
                data, err = capture_full(self.kwargs.get("screen_index", 0), self.kwargs.get("cursor", True), delay)
            elif self.mode == "region":
                data, err = capture_region(self.kwargs["x"], self.kwargs["y"], self.kwargs["w"], self.kwargs["h"],
                                          self.kwargs.get("cursor", False), delay)
            elif self.mode == "window":
                data, err = capture_window(self.kwargs["wid"], self.kwargs.get("cursor", True), delay,
                                          self.kwargs.get("include_titlebar", False))
            else:
                data, err = None, "unknown mode"
            if err:
                self.finished.emit(None, err)
                return
            if self.kwargs.get("save", True):
                directory = self.kwargs.get("directory")
                path = save_bytes(data, directory or str(SCREENSHOTS_DIR), "screenshot", self.kwargs.get("ext", "png"))
                self.finished.emit(path, None)
            else:
                self.finished.emit(data, None)
        except Exception as e:
            log.exception("capture failed")
            self.finished.emit(None, str(e))
