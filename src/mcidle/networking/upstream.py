import threading

from multiprocessing import Queue


class UpstreamThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self._queue = Queue()
        self.socket = None
        self.socket_lock = threading.RLock()
        self.running = True
        self._queue_cv = threading.Condition()

    def set_socket(self, socket):
        self.clear()
        with self.socket_lock:
            self.socket = socket

    def connected(self):
        with self.socket_lock:
            return self.socket is not None

    def put(self, b):
        self._queue.put(b)
        with self._queue_cv:
            self._queue_cv.notifyAll()

    def clear(self):
        while not self._queue.empty():
            self._queue.get()

    def stop(self):
        self.set_socket(None)
        self.running = False

    def run(self):
        while self.running:
            while self._queue.empty():
                # Can't use queue.get(True) since the socket might be invalid.
                with self._queue_cv:
                    self._queue_cv.wait()
            # Acquire the lock since socket can be None when set in another thread
            with self.socket_lock:
                if self.socket:
                    while not self._queue.empty():
                        pkt = self._queue.get()
                        try:
                            self.socket.send(pkt)
                        except Exception as _:
                            pass # Keep on throwing exceptions until we get a new socket
