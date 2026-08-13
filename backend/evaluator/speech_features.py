def count_words(text: str) -> int:
    if not text:
        return 0
    return len(text.strip().split())


def calculate_words_per_minute(word_count: int, duration: float) -> float:
    if duration <= 0:
        return 0.0
    return round((word_count / duration) * 60.0, 1)


def build_speech_features(answer: str, duration: float, segments: list = None) -> dict:
    w_count = count_words(answer)
    wpm = calculate_words_per_minute(w_count, duration)
    num_segments = len(segments) if segments else 0

    return {
        "word_count": w_count,
        "duration": round(duration, 2),
        "words_per_minute": wpm,
        "segment_count": num_segments
    }
