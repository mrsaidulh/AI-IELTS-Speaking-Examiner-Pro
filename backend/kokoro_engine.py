from speech.kokoro_service import KokoroService


class KokoroEngine:

    def __init__(
        self,
        base_url="http://localhost:8880"
    ):
        self.service = KokoroService(base_url=base_url)

    def synthesize(
        self,
        text,
        output_path
    ):
        return self.service.synthesize_file(text, output_path)
