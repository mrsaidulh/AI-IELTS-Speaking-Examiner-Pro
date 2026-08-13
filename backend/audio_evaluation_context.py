class AudioEvaluationContext:

    def __init__(self, transcript, audio_metrics):
        self.transcript = transcript
        self.audio_metrics = audio_metrics

    def build(self):
        return {
            "transcript": self.transcript,
            "audio_metrics": self.audio_metrics
        }
