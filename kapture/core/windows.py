from kapture.core.x11 import XDisplay

_display = None


def display():
    global _display
    if _display is None:
        _display = XDisplay()
    return _display


def list_windows():
    try:
        return display().list_windows()
    except Exception:
        return []


def window_by_id(wid):
    for w in list_windows():
        if w["id"] == wid:
            return w
    return None


def top_window_at(x, y):
    wins = list_windows()  # bottom->top
    # iterate top->bottom
    for w in reversed(wins):
        if w["x"] <= x < w["x"] + w["w"] and w["y"] <= y < w["y"] + w["h"]:
            return w
    return None


def is_viewable(wid):
    try:
        attrs = display().get_attributes(wid)
        return bool(attrs and attrs["map_state"] == 2)
    except Exception:
        return False


def window_geometry(wid):
    try:
        g = display().get_geometry(wid)
        if not g:
            return None
        x, y, w, h, bw, depth = g
        return x, y, w, h
    except Exception:
        return None


def current_desktop():
    try:
        return display().current_desktop()
    except Exception:
        return 0
