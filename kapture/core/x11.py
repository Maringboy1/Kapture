import ctypes
import ctypes.util
import threading

_lib = ctypes.CDLL(ctypes.util.find_library("X11"))

# basic types
XID = ctypes.c_ulong
Window = ctypes.c_ulong
Display_p = ctypes.c_void_p
Atom = ctypes.c_ulong

_lib.XOpenDisplay.restype = Display_p
_lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
_lib.XCloseDisplay.argtypes = [Display_p]
_lib.XDefaultRootWindow.restype = Window
_lib.XGetSelectionOwner.restype = Window
_lib.XGetSelectionOwner.argtypes = [Display_p, Atom]
_lib.XDefaultRootWindow.argtypes = [Display_p]
_lib.XInternAtom.restype = Atom
_lib.XInternAtom.argtypes = [Display_p, ctypes.c_char_p, ctypes.c_int]
_lib.XGetWindowProperty.restype = ctypes.c_int
_lib.XGetWindowProperty.argtypes = [
    Display_p, Window, Atom, ctypes.c_long, ctypes.c_long, ctypes.c_int,
    Atom, ctypes.POINTER(Atom), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
    ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),
]
_lib.XFree.argtypes = [ctypes.c_void_p]
_lib.XGetWindowAttributes.restype = ctypes.c_int
_lib.XGetGeometry.restype = ctypes.c_int
_lib.XGetGeometry.argtypes = [
    Display_p, Window, ctypes.POINTER(Window), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.c_uint),
]
_lib.XQueryTree.restype = ctypes.c_int
_lib.XQueryTree.argtypes = [
    Display_p, Window, ctypes.POINTER(Window), ctypes.POINTER(Window),
    ctypes.POINTER(ctypes.POINTER(Window)), ctypes.POINTER(ctypes.c_uint),
]
_lib.XFetchName.restype = ctypes.c_int
_lib.XFetchName.argtypes = [Display_p, Window, ctypes.POINTER(ctypes.c_char_p)]
_lib.XGetWMName.restype = None
_lib.XSync.argtypes = [Display_p, ctypes.c_int]
_lib.XSetErrorHandler.restype = ctypes.c_void_p
_lib.XSetErrorHandler.argtypes = [ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)]
_lib.XGrabKey.argtypes = [Display_p, ctypes.c_int, ctypes.c_uint, Window, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.XUngrabKey.argtypes = [Display_p, ctypes.c_int, ctypes.c_uint, Window]
_lib.XKeysymToKeycode.restype = ctypes.c_uint
_lib.XKeysymToKeycode.argtypes = [Display_p, ctypes.c_ulong]
_lib.XStringToKeysym.restype = ctypes.c_ulong
_lib.XStringToKeysym.argtypes = [ctypes.c_char_p]
_lib.XkbKeycodeToKeysym.restype = ctypes.c_ulong
_lib.XkbKeycodeToKeysym.argtypes = [Display_p, ctypes.c_uint, ctypes.c_int, ctypes.c_int]
_lib.XNextEvent.argtypes = [Display_p, ctypes.c_void_p]
_lib.XPending.restype = ctypes.c_int
_lib.XPending.argtypes = [Display_p]
_lib.XSelectInput.argtypes = [Display_p, Window, ctypes.c_long]
_lib.XQueryPointer.restype = ctypes.c_int
_lib.XQueryPointer.argtypes = [
    Display_p, Window, ctypes.POINTER(Window), ctypes.POINTER(Window),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint),
]

XK = {
    "Print": 0xff61,
}

# event structs (minimal)
class XAnyEvent(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("serial", ctypes.c_ulong),
                ("send_event", ctypes.c_int), ("display", Display_p),
                ("window", Window)]


class XKeyEvent(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("serial", ctypes.c_ulong),
                ("send_event", ctypes.c_int), ("display", Display_p),
                ("window", Window), ("root", Window), ("subwindow", Window),
                ("time", ctypes.c_ulong), ("x", ctypes.c_int), ("y", ctypes.c_int),
                ("x_root", ctypes.c_int), ("y_root", ctypes.c_int),
                ("state", ctypes.c_uint), ("keycode", ctypes.c_uint),
                ("same_screen", ctypes.c_int)]


class XEvent(ctypes.Union):
    _fields_ = [("type", ctypes.c_int), ("xany", XAnyEvent), ("xkey", XKeyEvent)]


# X constants
PropertyChangeMask = 0
KeyPressMask = 1 << 0
KeyReleaseMask = 1 << 1
ButtonPressMask = 1 << 2
PointerMotionMask = 1 << 6
ExposureMask = 1 << 15
StructureNotifyMask = 1 << 17
SubstructureNotifyMask = 1 << 19

AnyPropertyType = 0
XA_WINDOW = 33
XA_STRING = 31
XA_ATOM = 4
XA_CARDINAL = 6
PropModeReplace = 0
GrabModeAsync = 1
KeyPress = 2
KeyRelease = 3
MapNotify = 19
UnmapNotify = 18
ConfigureNotify = 22
IsViewable = 2
IsUnmapped = 0
IsUnviewable = 1

ControlMask = 1 << 2
ShiftMask = 1 << 0
Mod1Mask = 1 << 3
Mod2Mask = 1 << 4
Mod4Mask = 1 << 6
LockMask = 1 << 1

_NET_WM_WINDOW_TYPE = b"_NET_WM_WINDOW_TYPE"
_NET_WM_WINDOW_TYPE_NORMAL = b"_NET_WM_WINDOW_TYPE_NORMAL"
_NET_WM_WINDOW_TYPE_DIALOG = b"_NET_WM_WINDOW_TYPE_DIALOG"
_NET_WM_WINDOW_TYPE_UTILITY = b"_NET_WM_WINDOW_TYPE_UTILITY"
_NET_WM_WINDOW_TYPE_SPLASH = b"_NET_WM_WINDOW_TYPE_SPLASH"
_NET_WM_STATE = b"_NET_WM_STATE"
_NET_WM_STATE_HIDDEN = b"_NET_WM_STATE_HIDDEN"
_NET_WM_NAME = b"_NET_WM_NAME"
_NET_CLIENT_LIST_STACKING = b"_NET_CLIENT_LIST_STACKING"
_NET_CLIENT_LIST = b"_NET_CLIENT_LIST"
_NET_CURRENT_DESKTOP = b"_NET_CURRENT_DESKTOP"
_NET_DESKTOP_VIEWPORT = b"_NET_DESKTOP_VIEWPORT"
_NET_FRAME_EXTENTS = b"_NET_FRAME_EXTENTS"
WM_NAME = b"WM_NAME"
WM_CLASS = b"WM_CLASS"


class X11Error(Exception):
    pass


class XDisplay:
    def __init__(self):
        self.d = _lib.XOpenDisplay(None)
        if not self.d:
            raise X11Error("cannot open X display")
        self._err_lock = threading.Lock()
        self._err_flag = False

        @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
        def handler(disp, event):
            self._err_flag = True
            return 0

        self._handler = handler
        _lib.XSetErrorHandler(handler)

    def close(self):
        try:
            _lib.XCloseDisplay(self.d)
        except Exception:
            pass

    def sync(self, discard=False):
        _lib.XSync(self.d, 1 if discard else 0)

    def reset_error(self):
        self._err_flag = False

    def had_error(self):
        return self._err_flag

    def intern(self, name, only_if_exists=0):
        return _lib.XInternAtom(self.d, name if isinstance(name, bytes) else name.encode(), only_if_exists)

    def root(self):
        return _lib.XDefaultRootWindow(self.d)

    def get_property(self, window, atom_name, atom_type=None, max_items=4096):
        atom = self.intern(atom_name) if isinstance(atom_name, (str, bytes)) else atom_name
        if atom_type is None:
            atom_type = 0  # AnyPropertyType
        elif isinstance(atom_type, (str, bytes)):
            atom_type = self.intern(atom_type)
        actual_type = Atom()
        actual_format = ctypes.c_int()
        nitems = ctypes.c_ulong()
        bytes_after = ctypes.c_ulong()
        data = ctypes.POINTER(ctypes.c_ubyte)()
        status = _lib.XGetWindowProperty(
            self.d, window, atom, 0, max_items, 0, atom_type,
            ctypes.byref(actual_type), ctypes.byref(actual_format),
            ctypes.byref(nitems), ctypes.byref(bytes_after), ctypes.byref(data),
        )
        if status != 0 or not data:
            if data:
                _lib.XFree(data)
            return None, None
        fmt = actual_format.value
        n = nitems.value
        at = actual_type.value
        if fmt == 32:
            arr = ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))
            values = [arr[i] for i in range(n)]
        elif fmt == 16:
            arr = ctypes.cast(data, ctypes.POINTER(ctypes.c_ushort))
            values = [arr[i] for i in range(n)]
        elif fmt == 8:
            values = [data[i] for i in range(n)]
        else:
            values = []
        _lib.XFree(data)
        return at, values

    def get_text_property(self, window, atom_name):
        at, values = self.get_property(window, atom_name, None)
        if not values:
            return None
        # try as string list of bytes
        try:
            # values are ints (char codes) when fmt 8
            if all(isinstance(v, int) and v < 256 for v in values):
                raw = bytes(values).split(b"\x00")[0]
                try:
                    return raw.decode("utf-8", "replace")
                except Exception:
                    return raw.decode("latin-1", "replace")
        except Exception:
            pass
        return None

    def get_window_name(self, window):
        # _NET_WM_NAME first
        name = self.get_text_property(window, _NET_WM_NAME)
        if name:
            return name
        # WM_NAME
        cname = ctypes.c_char_p()
        if _lib.XFetchName(self.d, window, ctypes.byref(cname)) and cname.value:
            try:
                return cname.value.decode("utf-8", "replace")
            except Exception:
                return cname.value.decode("latin-1", "replace")
        return ""

    def get_wm_class(self, window):
        at, values = self.get_property(window, WM_CLASS, XA_STRING)
        if not values:
            return "", ""
        # WM_CLASS is two null-terminated strings
        raw = bytes(values)
        parts = raw.split(b"\x00")
        inst = parts[0].decode("utf-8", "replace") if len(parts) > 0 else ""
        cls = parts[1].decode("utf-8", "replace") if len(parts) > 1 else ""
        return inst, cls

    def get_geometry(self, window):
        root_ret = Window()
        x = ctypes.c_int()
        y = ctypes.c_int()
        w = ctypes.c_uint()
        h = ctypes.c_uint()
        bw = ctypes.c_uint()
        depth = ctypes.c_uint()
        ok = _lib.XGetGeometry(self.d, window, ctypes.byref(root_ret),
                                ctypes.byref(x), ctypes.byref(y),
                                ctypes.byref(w), ctypes.byref(h),
                                ctypes.byref(bw), ctypes.byref(depth))
        if not ok:
            return None
        return (x.value, y.value, w.value, h.value, bw.value, depth.value)

    def get_attributes(self, window):
        class XWindowAttributes(ctypes.Structure):
            _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int),
                        ("width", ctypes.c_int), ("height", ctypes.c_int),
                        ("border_width", ctypes.c_int), ("depth", ctypes.c_int),
                        ("visual", ctypes.c_void_p), ("root", Window),
                        ("class", ctypes.c_int), ("bit_gravity", ctypes.c_int),
                        ("win_gravity", ctypes.c_int), ("backing_store", ctypes.c_int),
                        ("backing_planes", ctypes.c_ulong), ("backing_pixel", ctypes.c_ulong),
                        ("save_under", ctypes.c_int), ("colormap", ctypes.c_ulong),
                        ("map_installed", ctypes.c_int), ("map_state", ctypes.c_int),
                        ("all_event_masks", ctypes.c_long), ("your_event_mask", ctypes.c_long),
                        ("do_not_propagate_mask", ctypes.c_long), ("override_redirect", ctypes.c_int),
                        ("screen", ctypes.c_void_p)]
        attrs = XWindowAttributes()
        ok = _lib.XGetWindowAttributes(self.d, window, ctypes.byref(attrs))
        if not ok:
            return None
        return {"map_state": attrs.map_state, "override_redirect": attrs.override_redirect,
                "x": attrs.x, "y": attrs.y, "width": attrs.width, "height": attrs.height}

    def get_window_type(self, window):
        at, values = self.get_property(window, _NET_WM_WINDOW_TYPE, XA_ATOM)
        if not values:
            return None
        # map atom to name by reverse intern (best effort: compare known)
        names = []
        for v in values:
            # find which known atom matches
            for nm in (_NET_WM_WINDOW_TYPE_NORMAL, _NET_WM_WINDOW_TYPE_DIALOG,
                       _NET_WM_WINDOW_TYPE_UTILITY, _NET_WM_WINDOW_TYPE_SPLASH):
                if self.intern(nm) == v:
                    names.append(nm.decode())
        return names

    def get_frame_extents(self, window):
        at, values = self.get_property(window, _NET_FRAME_EXTENTS, XA_CARDINAL)
        if values and len(values) >= 4:
            left, right, top, bottom = values[:4]
            return (left, right, top, bottom)
        return (0, 0, 0, 0)

    def get_desktop(self, window):
        at, values = self.get_property(window, b"_NET_WM_DESKTOP", XA_CARDINAL)
        if values:
            return values[0]
        return 0

    def current_desktop(self):
        at, values = self.get_property(self.root(), _NET_CURRENT_DESKTOP, XA_CARDINAL)
        if values:
            return values[0]
        return 0

    def list_windows(self):
        # returns list of dicts in bottom->top order
        atom = self.intern(_NET_CLIENT_LIST_STACKING)
        at, values = self.get_property(self.root(), _NET_CLIENT_LIST_STACKING, XA_WINDOW)
        if not values:
            atom = self.intern(_NET_CLIENT_LIST)
            at, values = self.get_property(self.root(), _NET_CLIENT_LIST, XA_WINDOW)
        if not values:
            return []
        cur_desk = self.current_desktop()
        out = []
        for wid in values:
            attrs = self.get_attributes(wid)
            if not attrs:
                continue
            if attrs["map_state"] != IsViewable:
                continue
            wtype = self.get_window_type(wid)
            if wtype is None:
                wtype = []
            if not any(t.endswith("NORMAL") or t.endswith("DIALOG") or t.endswith("UTILITY") or t.endswith("SPLASH") for t in wtype):
                # allow unknown type windows with name
                pass
            if wtype and not any(t.endswith(("NORMAL", "DIALOG", "UTILITY", "SPLASH")) for t in wtype):
                continue
            desk = self.get_desktop(wid)
            if desk != cur_desk and desk != 0xFFFFFFFF:
                continue
            name = self.get_window_name(wid)
            inst, cls = self.get_wm_class(wid)
            if cls.lower() in ("xfce4-panel", "kapture", "desktop"):
                continue
            if "desktop" in wtype and "NORMAL" not in str(wtype):
                pass
            geom = self.get_geometry(wid)
            if not geom:
                continue
            x, y, w, h, bw, depth = geom
            if w < 20 or h < 20:
                continue
            if cls.lower() == "desktop" or (name.lower() == "desktop" and wtype and "DESKTOP" in str(wtype).upper()):
                continue
            # frame extents
            fe = self.get_frame_extents(wid)
            out.append({
                "id": wid,
                "name": name or "(unnamed)",
                "class": cls,
                "instance": inst,
                "type": wtype,
                "desktop": desk,
                "x": x, "y": y, "w": w, "h": h,
                "frame": fe,
            })
        return out

    def grab_key(self, keycode, modifiers):
        self.reset_error()
        _lib.XGrabKey(self.d, keycode, modifiers, self.root(), 0, GrabModeAsync, GrabModeAsync)
        _lib.XSync(self.d, 0)
        return not self.had_error()

    def ungrab_key(self, keycode, modifiers):
        _lib.XUngrabKey(self.d, keycode, modifiers, self.root())

    def keysym_to_keycode(self, keysym):
        return _lib.XKeysymToKeycode(self.d, keysym)

    def string_to_keysym(self, s):
        return _lib.XStringToKeysym(s.encode())

    def query_pointer(self):
        root = self.root()
        ret_root = Window()
        ret_child = Window()
        rx = ctypes.c_int()
        ry = ctypes.c_int()
        wx = ctypes.c_int()
        wy = ctypes.c_int()
        mask = ctypes.c_uint()
        ok = _lib.XQueryPointer(self.d, root, ctypes.byref(ret_root), ctypes.byref(ret_child),
                                ctypes.byref(rx), ctypes.byref(ry), ctypes.byref(wx), ctypes.byref(wy),
                                ctypes.byref(mask))
        if not ok:
            return None
        return (rx.value, ry.value, ret_child.value, mask.value)

    def next_event(self, timeout=0.1):
        # returns XEvent or None
        if _lib.XPending(self.d) == 0:
            return None
        ev = XEvent()
        _lib.XNextEvent(self.d, ctypes.byref(ev))
        return ev

    def select_input(self, window, mask):
        _lib.XSelectInput(self.d, window, mask)
