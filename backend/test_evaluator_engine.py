from evaluator.models import IELTSEvaluation, CriterionEvaluation
from evaluator.speech_features import count_words, calculate_words_per_minute, build_speech_features
from evaluator.scoring import calculate_ielts_band
from evaluator.service import IELTSEvaluator
from llm.qwen import QwenService

print("Testing Lesson 29 — IELTS Evaluation Engine with Qwen...")

# Test 1: Speech metrics feature extraction
sample_answer = "I am from Mymensingh, which is a peaceful and scenic city in Bangladesh. I really enjoy living there because of the welcoming community."
duration = 8.5

feats = build_speech_features(sample_answer, duration)
print("\n--- Speech Features ---")
print("Word Count:", feats["word_count"])
print("Duration:", feats["duration"], "s")
print("Words Per Minute:", feats["words_per_minute"])
assert feats["word_count"] > 15
assert feats["words_per_minute"] > 100

# Test 2: Deterministic IELTS band calculation rounding
scores = [6.5, 6.5, 6.0, None]
band = calculate_ielts_band(scores)
print("\n--- Deterministic Band Calculation ---")
print(f"Criteria Scores: {scores} -> Overall Band: {band}")
assert band == 6.5  # (6.5 + 6.5 + 6.0)/3 = 6.333 -> .25 to .75 rounds to .5 -> 6.5

# Test 3: Evaluator Service execution with QwenService fallback
qwen = QwenService()
evaluator = IELTSEvaluator(qwen_service=qwen)

result: IELTSEvaluation = evaluator.evaluate_answer(
    question="Where are you from?",
    answer=sample_answer,
    duration=duration
)

print("\n--- Evaluation Result Summary ---")
print("Overall Band:", result.overall_band)
print("Fluency Score:", result.fluency.score, "| Strengths:", result.fluency.strengths)
print("Lexical Score:", result.lexical_resource.score, "| Evidence:", result.lexical_resource.evidence)
print("Grammar Score:", result.grammar.score, "| Strengths:", result.grammar.strengths)
print("Pronunciation Score:", result.pronunciation.score, "(Null audio proof verification)")
print("Feedback:", result.feedback)

print("\nLesson 29 Evaluation Engine Test Passed Successfully!")
