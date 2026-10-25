import subprocess

from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QMimeData


def set_image(qimage):
    cb = QApplication.clipboard()
    cb.setImage(qimage)
    # xclip fallback for persistence
    try:
        ba = qimage_to_png_bytes(qimage)
        if ba:
            p = subprocess.Popen(
                ["xclip", "-selection", "clipboard", "-t", "image/png"],
                stdin=subprocess.PIPE,
            )
            p.stdin.write(ba)
            p.stdin.close()
    except Exception:
        pass


def qimage_to_png_bytes(qimage):
    from PyQt6.QtCore import QBuffer, QIODevice
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    qimage.save(buf, "PNG")
    return bytes(buf.data())


def set_text(text):
    QApplication.clipboard().setText(text)


def open_path(path):
    import os
    if os.name == "nt":
        os.startfile(path)
    else:
        subprocess.Popen(["xdg-open", str(path)])
