import librosa
import numpy as np


class AudioAnalyzer:

    def __init__(self, audio_path):
        self.audio_path = audio_path
        self.audio = None
        self.sample_rate = None
        self.duration = 0

    def load(self):
        self.audio, self.sample_rate = librosa.load(
            self.audio_path,
            sr=None,
            mono=True
        )
        self.duration = len(self.audio) / self.sample_rate

    def get_duration(self):
        if self.audio is None:
            self.load()
        return round(self.duration, 2)

    def calculate_wpm(self, transcript):
        if self.duration <= 0:
            return 0
        words = len(transcript.split())
        minutes = self.duration / 60
        return round(words / minutes, 1)

    def detect_speech_segments(self, top_db=30):
        if self.audio is None:
            self.load()
        intervals = librosa.effects.split(
            self.audio,
            top_db=top_db
        )
        return intervals

    def analyze_pauses(self, intervals):
        pauses = []
        for i in range(1, len(intervals)):
            previous_end = intervals[i - 1][1]
            current_start = intervals[i][0]
            pause_samples = current_start - previous_end
            pause_seconds = pause_samples / self.sample_rate
            pauses.append(pause_seconds)
        return pauses

    def pause_statistics(self, pauses):
        if not pauses:
            return {
                "count": 0,
                "average": 0,
                "long_pauses": 0,
                "very_long_pauses": 0
            }

        long_pauses = sum(1 for pause in pauses if pause >= 0.7)
        very_long_pauses = sum(1 for pause in pauses if pause >= 1.5)

        return {
            "count": len(pauses),
            "average": round(float(np.mean(pauses)), 2),
            "long_pauses": long_pauses,
            "very_long_pauses": very_long_pauses
        }

    def speech_percentage(self, intervals):
        speech_samples = sum(end - start for start, end in intervals)
        speech_seconds = speech_samples / self.sample_rate

        if self.duration == 0:
            return 0

        return round((speech_seconds / self.duration) * 100, 1)

    def analyze_pitch(self):
        if self.audio is None:
            self.load()

        f0 = librosa.yin(
            self.audio,
            fmin=65,
            fmax=400,
            sr=self.sample_rate
        )

        f0 = f0[np.isfinite(f0)]

        if len(f0) == 0:
            return {
                "mean": 0,
                "minimum": 0,
                "maximum": 0
            }

        return {
            "mean": round(float(np.mean(f0)), 2),
            "minimum": round(float(np.min(f0)), 2),
            "maximum": round(float(np.max(f0)), 2)
        }

    def pitch_variation(self):
        pitch = self.analyze_pitch()
        if pitch["mean"] == 0:
            return 0
        return round(pitch["maximum"] - pitch["minimum"], 2)

    def analyze(self, transcript):
        self.load()
        intervals = self.detect_speech_segments()
        pauses = self.analyze_pauses(intervals)
        statistics = self.pause_statistics(pauses)
        pitch = self.analyze_pitch()
        p_var = round(pitch["maximum"] - pitch["minimum"], 2) if pitch["mean"] > 0 else 0

        return {
            "duration": self.get_duration(),
            "wpm": self.calculate_wpm(transcript),
            "speech_percentage": self.speech_percentage(intervals),
            "pause_statistics": statistics,
            "speech_segments": len(intervals),
            "pitch_analysis": pitch,
            "pitch_variation": p_var
        }
