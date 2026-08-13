def calculate_words_per_minute(
    transcript,
    duration_seconds
):
    if duration_seconds <= 0:
        return 0

    words = len(
        transcript.split()
    )

    minutes = (
        duration_seconds / 60
    )

    return round(
        words / minutes,
        1
    )
