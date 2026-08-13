import re


def speech_rate(word_count: int, duration_seconds: float) -> float:
    """Calculates words per minute (WPM)."""
    if duration_seconds <= 0:
        return 0.0
    return round((word_count / (duration_seconds / 60.0)), 1)


def detect_pauses(segments: list = None) -> dict:
    """
    Analyzes inter-segment gaps to categorize pause patterns.
    - Short pause: 0.5s - 1.0s
    - Medium pause: 1.0s - 2.5s
    - Long pause: > 2.5s
    """
    if not segments or len(segments) < 2:
        return {
            "pause_count": 0,
            "short_pauses": 0,
            "medium_pauses": 0,
            "long_pauses": 0,
            "total_pause_duration": 0.0,
            "avg_pause_duration": 0.0
        }

    pauses = []
    short_cnt = 0
    med_cnt = 0
    long_cnt = 0

    for i in range(len(segments) - 1):
        prev_end = segments[i].get("end", 0.0)
        next_start = segments[i + 1].get("start", 0.0)
        gap = next_start - prev_end

        if gap >= 0.5:
            pauses.append(gap)
            if gap < 1.0:
                short_cnt += 1
            elif gap <= 2.5:
                med_cnt += 1
            else:
                long_cnt += 1

    tot_duration = sum(pauses)
    avg_duration = round(tot_duration / len(pauses), 2) if pauses else 0.0

    return {
        "pause_count": len(pauses),
        "short_pauses": short_cnt,
        "medium_pauses": med_cnt,
        "long_pauses": long_cnt,
        "total_pause_duration": round(tot_duration, 2),
        "avg_pause_duration": avg_duration
    }


def detect_fillers(transcript: str) -> dict:
    """Detects hesitation markers and discourse fillers."""
    if not transcript:
        return {"filler_count": 0, "detected_fillers": [], "filler_density": 0.0}

    fillers_pattern = r"\b(um|uh|er|you know|like|actually|i mean|sort of|kind of|well)\b"
    matches = re.findall(fillers_pattern, transcript.lower())

    words = transcript.strip().split()
    word_cnt = len(words)
    density = round((len(matches) / word_cnt) * 100, 1) if word_cnt > 0 else 0.0

    return {
        "filler_count": len(matches),
        "detected_fillers": list(set(matches)),
        "filler_density": density
    }


def detect_repetitions(transcript: str) -> dict:
    """Detects phrase repetitions (e.g., 'i think... i think')."""
    if not transcript:
        return {"repetition_count": 0, "repeated_phrases": []}

    rep_pattern = r"\b(\w+(?:\s+\w+){0,2})\s+\1\b"
    matches = re.findall(rep_pattern, transcript.lower())

    return {
        "repetition_count": len(matches),
        "repeated_phrases": list(set(matches))
    }


def detect_self_corrections(transcript: str) -> dict:
    """Detects self-correction expressions."""
    if not transcript:
        return {"self_correction_count": 0, "expressions": []}

    sc_pattern = r"\b(actually|i mean|sorry|rather|what i meant was|or rather)\b"
    matches = re.findall(sc_pattern, transcript.lower())

    return {
        "self_correction_count": len(matches),
        "expressions": list(set(matches))
    }


def extract_speech_features(transcript: str, duration: float, segments: list = None) -> dict:
    """Aggregates objective speech metrics for evidence generation."""
    words = transcript.strip().split() if transcript else []
    word_count = len(words)
    wpm = speech_rate(word_count, duration)
    pauses = detect_pauses(segments)
    fillers = detect_fillers(transcript)
    repetitions = detect_repetitions(transcript)
    self_corrections = detect_self_corrections(transcript)

    return {
        "duration": round(duration, 2),
        "word_count": word_count,
        "speech_rate_wpm": wpm,
        "pauses": pauses,
        "fillers": fillers,
        "repetitions": repetitions,
        "self_corrections": self_corrections
    }
