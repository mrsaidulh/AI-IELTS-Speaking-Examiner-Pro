class AnswerBuffer:

    def __init__(self):
        self.chunks = []

    def add(self, chunk: bytes):
        self.chunks.append(chunk)

    def get_bytes(self) -> bytes:
        return b"".join(self.chunks)

    def clear(self):
        self.chunks = []

    def size(self) -> int:
        return sum(len(chunk) for chunk in self.chunks)
