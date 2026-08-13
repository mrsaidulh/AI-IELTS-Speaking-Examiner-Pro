class SpeechSegment:

    def __init__(self):
        self.audio_chunks = []
        self.started = False

    def add_chunk(self, chunk: bytes):
        self.audio_chunks.append(chunk)

    def start(self):
        self.started = True

    def reset(self):
        self.audio_chunks = []
        self.started = False

    def get_audio(self) -> bytes:
        return b"".join(self.audio_chunks)
