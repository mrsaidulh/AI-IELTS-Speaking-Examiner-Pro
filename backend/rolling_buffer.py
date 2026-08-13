from collections import deque


class RollingBuffer:

    def __init__(self, max_chunks=5):
        self.buffer = deque(maxlen=max_chunks)

    def add(self, chunk: bytes):
        self.buffer.append(chunk)

    def get(self) -> list:
        return list(self.buffer)

    def clear(self):
        self.buffer.clear()
