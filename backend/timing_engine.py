import time

class TimingEngine:
    PREPARATION_TIME = 60
    SPEAKING_TIME = 120

    def __init__(self):
        self.state = "idle"
        self.started_at = None
        self.duration = 0

    def start_preparation(self):
        self.state = "preparation"
        self.started_at = time.time()
        self.duration = self.PREPARATION_TIME

    def start_speaking(self):
        self.state = "speaking"
        self.started_at = time.time()
        self.duration = self.SPEAKING_TIME

    def elapsed(self):
        if self.started_at is None:
            return 0
        return int(time.time() - self.started_at)

    def remaining(self):
        remaining = self.duration - self.elapsed()
        return max(0, remaining)

    def is_finished(self):
        return self.remaining() <= 0

    def finish(self):
        self.state = "completed"
