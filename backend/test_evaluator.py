from evaluator import evaluate
from report import print_report


with open(
    "sample_transcript.txt",
    "r",
    encoding="utf-8"
) as f:

    transcript = f.read()


result = evaluate(transcript)

print_report(result)
