import threading

from PyQt6.QtCore import QObject, pyqtSignal

from kapture.core.x11 import (
    XDisplay, ControlMask, ShiftMask, Mod1Mask, Mod2Mask, Mod4Mask, LockMask,
    KeyPress, GrabModeAsync,
)

MOD_MAP = {
    "Ctrl": ControlMask,
    "Control": ControlMask,
    "Alt": Mod1Mask,
    "Shift": ShiftMask,
    "Super": Mod4Mask,
    "Meta": Mod4Mask,
}


def parse_shortcut(text):
    parts = [p.strip() for p in text.split("+")]
    mods = 0
    key = ""
    for p in parts:
        if p in MOD_MAP:
            mods |= MOD_MAP[p]
        else:
            key = p
    return mods, key


class HotkeyManager(QObject):
    triggered = pyqtSignal(str)

    def __init__(self, shortcuts, parent=None):
        super().__init__(parent)
        self.shortcuts = shortcuts  # name -> text
        self._thread = None
        self._stop = threading.Event()
        self._display = None
        self.status = {}

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        try:
            disp = XDisplay()
        except Exception:
            self.status = {k: False for k in self.shortcuts}
            return
        self._display = disp
        root = disp.root()
        # build name -> (mods, keycode)
        mapping = {}
        for name, text in self.shortcuts.items():
            mods, key = parse_shortcut(text)
            ks = disp.string_to_keysym(key)
            if not ks and key.lower() == "print":
                ks = 0xff61
            kc = disp.keysym_to_keycode(ks) if ks else 0
            if not kc:
                self.status[name] = False
                continue
            mapping[name] = (mods, kc)
            # grab combos including lock/numlock
            combos = [mods, mods | LockMask, mods | Mod2Mask, mods | LockMask | Mod2Mask]
            ok_all = True
            for m in combos:
                disp.reset_error()
                _lib_grab = disp.grab_key(kc, m)
                if not _lib_grab:
                    ok_all = False
            self.status[name] = ok_all
        # event loop
        while not self._stop.is_set():
            ev = disp.next_event()
            if ev is None:
                self._stop.wait(0.05)
                continue
            if ev.type == KeyPress:
                kc = ev.xkey.keycode
                state = ev.xkey.state
                base_state = state & ~(LockMask | Mod2Mask)
                for name, (mods, keyc) in mapping.items():
                    if keyc == kc and mods == base_state:
                        self.triggered.emit(name)
        # cleanup
        for name, (mods, kc) in mapping.items():
            for m in (mods, mods | LockMask, mods | Mod2Mask, mods | LockMask | Mod2Mask):
                disp.ungrab_key(kc, m)
        disp.close()
