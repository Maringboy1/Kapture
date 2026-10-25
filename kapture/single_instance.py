import json

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstance(QObject):
    message_received = pyqtSignal(dict)

    def __init__(self, key="kapture-single"):
        super().__init__()
        self.key = key
        self.server = None
        self.is_primary = False

    def start_primary(self):
        QLocalServer.removeServer(self.key)
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._on_conn)
        self.is_primary = self.server.listen(self.key)
        return self.is_primary

    def _on_conn(self):
        sock = self.server.nextPendingConnection()
        if sock is None:
            return
        sock.readyRead.connect(lambda s=sock: self._read(s))

    def _read(self, sock):
        data = bytes(sock.readAll())
        try:
            msg = json.loads(data.decode("utf-8", "replace"))
        except Exception:
            msg = {"raw": data.decode("utf-8", "replace", errors="replace")}
        self.message_received.emit(msg)
        sock.write(b'{"ok":true}')
        sock.flush()

    @staticmethod
    def send(msg, timeout=3000):
        sock = QLocalSocket()
        sock.connectToServer("kapture-single")
        if not sock.waitForConnected(timeout):
            return False, "not running"
        sock.write(json.dumps(msg).encode())
        sock.flush()
        sock.waitForReadyRead(timeout)
        resp = bytes(sock.readAll()).decode("utf-8", errors="replace")
        sock.disconnectFromServer()
        return True, resp

    @staticmethod
    def is_running():
        sock = QLocalSocket()
        sock.connectToServer("kapture-single")
        ok = sock.waitForConnected(500)
        if ok:
            sock.disconnectFromServer()
        return ok
