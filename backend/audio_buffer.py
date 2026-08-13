from collections import deque


class RollingBuffer:
    def __init__(self, max_frames: int = 15):
        self.frames = deque(maxlen=max_frames)

    def add(self, frame: bytes):
        self.frames.append(frame)

    def get(self) -> list:
        return list(self.frames)

    def clear(self):
        self.frames.clear()
