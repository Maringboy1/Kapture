import subprocess
from PyQt6.QtWidgets import QSystemTrayIcon


def notify(title, body, icon=None, timeout=4000):
    try:
        cmd = ["notify-send", "-a", "Kapture", "-t", str(timeout)]
        if icon:
            cmd += ["-i", str(icon)]
        cmd += [title, body]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception:
        pass
    try:
        QSystemTrayIcon.showMessage(None, title, body, QSystemTrayIcon.MessageIcon.Information, timeout)
    except Exception:
        pass
