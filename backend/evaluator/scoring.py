def calculate_ielts_band(scores: list) -> float:
    """
    Calculates overall IELTS band score from individual criteria scores.
    Applies standard IELTS rounding logic:
    - .25 rounds up to .5
    - .75 rounds up to next whole band
    """
    valid_scores = [float(s) for s in scores if s is not None and isinstance(s, (int, float))]
    if not valid_scores:
        return 6.0  # Default fallback band if no valid scores provided

    avg = sum(valid_scores) / len(valid_scores)
    whole = int(avg)
    fraction = avg - whole

    if fraction < 0.25:
        return float(whole)
    elif fraction < 0.75:
        return float(whole) + 0.5
    else:
        return float(whole + 1)
