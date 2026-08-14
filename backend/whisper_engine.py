from whisper_service import WhisperService

class WhisperEngine(WhisperService):
    def __init__(self, model_name=None, device=None, compute_type=None):
        super().__init__(model_size=model_name, device=device, compute_type=compute_type)

    def transcribe_legacy(self, audio_path, language="en"):
        result = self.transcribe(audio_path, language=language)
        return result["text"]
