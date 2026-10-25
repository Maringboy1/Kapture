import os
import sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from kapture.core.paths import ensure_dirs, TMP_DIR
from kapture.core import audio, windows
from kapture.core.geometry import even
from kapture.core.capture import _ffmpeg_png, virtual_geometry


def _check(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, str(e)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return ok


def run_self_test():
    ensure_dirs()
    app = QApplication(sys.argv)
    results = []

    def c1():
        # ffmpeg
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True)
        return r.returncode == 0, "ffmpeg available"

    def c2():
        data, err = _ffmpeg_png(["-f", "x11grab", "-video_size", "320x240", "-i", ":0.0+0,0"])
        return data is not None and len(data) > 100, (err or "screen capture ok")

    def c3():
        # window capture on active window
        import subprocess as sp
        wid = sp.check_output(["xdotool", "getactivewindow"]).decode().strip()
        data, err = _ffmpeg_png(["-f", "x11grab", "-window_id", wid, "-i", ":0.0"])
        return data is not None and len(data) > 100, (err or f"window {wid} ok")

    def c4():
        # even pad
        return even(863) == 862 and even(1919) == 1918, "even() ok"

    def c5():
        # audio
        srcs = audio.list_sources()
        return len(srcs) > 0, f"{len(srcs)} pulse sources"

    def c6():
        # desktop monitor
        d = audio.desktop_source()
        return d is not None, (d or "no desktop source")

    def c7():
        # compositor
        from kapture.core.x11 import XDisplay
        disp = XDisplay()
        root = disp.root()
        from kapture.core.x11 import _lib
        # check _NET_WM_CM_S0 owner
        atom = disp.intern(b"_NET_WM_CM_S0")
        at, vals = disp.get_property(root, b"_NET_WM_CM_S0", None)
        # get selection owner via XGetSelectionOwner
        owner = _lib.XGetSelectionOwner(disp.d, atom)
        disp.close()
        return owner != 0, f"compositor owner {hex(owner)}"

    def c8():
        # tray available
        from PyQt6.QtWidgets import QSystemTrayIcon
        return QSystemTrayIcon.isSystemTrayAvailable(), "system tray"

    def c9():
        # hotkey grab test
        from kapture.core.x11 import XDisplay
        disp = XDisplay()
        # try grab F12 (unlikely used)
        ks = disp.string_to_keysym("F12")
        kc = disp.keysym_to_keycode(ks) if ks else 0
        ok = False
        if kc:
            ok = disp.grab_key(kc, 0)
            disp.ungrab_key(kc, 0)
        disp.close()
        return ok, "XGrabKey works"

    def c10():
        # dirs writable
        p = TMP_DIR / "selftest.tmp"
        p.write_text("ok")
        p.unlink()
        return True, "state dir writable"

    def c11():
        # windows enumeration
        ws = windows.list_windows()
        return len(ws) >= 0, f"{len(ws)} windows"

    def c12():
        # virtual geometry
        vg = virtual_geometry()
        return vg is not None and vg[2] > 0, str(vg)

    checks = [
        ("ffmpeg", c1), ("screen capture", c2), ("window capture", c3),
        ("even sizing", c4), ("audio sources", c5), ("desktop audio", c6),
        ("compositor", c7), ("system tray", c8), ("hotkey grab", c9),
        ("state dir", c10), ("window enumeration", c11), ("virtual geometry", c12),
    ]
    for name, fn in checks:
        results.append(_check(name, fn))

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n{passed}/{total} checks passed")
    return 0 if passed == total else 1
