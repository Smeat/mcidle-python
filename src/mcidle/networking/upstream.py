import threading

from multiprocessing import Queue

class UpstreamThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self._queue = Queue()
        self.socket = None
        self.socket_lock = threading.RLock()
        self.running = True

    def set_socket(self, socket):
        self.clear()
        with self.socket_lock:
            self.socket = socket

    def connected(self):
        with self.socket_lock:
            return self.socket is not None

    def put(self, b):
        self._queue.put(b)

    def clear(self):
        while not self._queue.empty():
            self._queue.get()

    def stop(self):
        self.set_socket(None)
        self.running = False

    def run(self):
        while self.running:
            pkt = self._queue.get(True)
            # Acquire the lock since socket can be None when set in another thread
            with self.socket_lock:
                # if the socket is set, the queue is cleared anyways, so just ignoring the packet is fine
                if self.socket:
                    while True:
                        # This will throw queue.Empty if no item is left. Cant use empty() since it is unreliable
                        try:
                            self.socket.send(pkt)
                        except Exception as _:
                            pass # Keep on throwing exceptions until we get a new socket
