import json
import os
import socket
import threading
import queue
import time


class TCPWriter:
    def __init__(self, host="127.0.0.1"):
        self.host = host
        self.port = 6000
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def send(self, data: dict):
        """Queue the data for async sending."""
        self.q.put(data)

    def set_port(self, port: int):
        if self.port != port:
            self.port = port

    def _worker(self):
        """Background thread that sends queued log entries."""
        sock = None
        while True:
            data = self.q.get()
            if data is None:
                if sock:
                    sock.close()
                break
            try:
                if sock is None:
                    sock = socket.create_connection((self.host, self.port))
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                message = f"{json.dumps(data)}\n"
                sock.sendall(message.encode())
                time.sleep(0.1)
            except Exception as e:
                sock = None
                time.sleep(1)
