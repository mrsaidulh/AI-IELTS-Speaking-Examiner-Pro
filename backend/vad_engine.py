import torch
from silero_vad import (
    load_silero_vad,
    get_speech_timestamps,
    read_audio
)


class VADEngine:

    def __init__(self):
        self.model = load_silero_vad()

    def detect(self, audio_path):
        wav = read_audio(
            audio_path,
            sampling_rate=16000
        )

        timestamps = get_speech_timestamps(
            wav,
            self.model,
            sampling_rate=16000
        )

        return timestamps


def samples_to_seconds(
    timestamp,
    sample_rate=16000
):
    return {
        "start": timestamp["start"] / sample_rate,
        "end": timestamp["end"] / sample_rate
    }
