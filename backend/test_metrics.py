from speech_metrics import (
    calculate_words_per_minute
)

text = """
I usually spend my weekends with
my friends because we like visiting
different places around my hometown.
"""

result = calculate_words_per_minute(
    text,
    30
)

print(
    "WPM:",
    result
)
