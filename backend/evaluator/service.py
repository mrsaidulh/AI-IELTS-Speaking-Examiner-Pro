import json
import re
from evaluator.models import CriterionEvaluation, IELTSEvaluation
from evaluator.prompts import EVALUATOR_SYSTEM_PROMPT, build_evaluation_prompt
from evaluator.speech_features import build_speech_features
from evaluator.scoring import calculate_ielts_band


class IELTSEvaluator:

    def __init__(self, qwen_service):
        self.qwen = qwen_service

    def evaluate_answer(self, question: str, answer: str, duration: float, segments: list = None) -> IELTSEvaluation:
        speech_feats = build_speech_features(answer, duration, segments)
        prompt = build_evaluation_prompt(question, answer, duration, speech_feats)

        raw_res = self.qwen.generate(prompt, system_prompt=EVALUATOR_SYSTEM_PROMPT)

        parsed_data = self._parse_json_response(raw_res)

        # Extract criteria objects
        fc_data = parsed_data.get("fluency_coherence", {})
        lr_data = parsed_data.get("lexical_resource", {})
        gra_data = parsed_data.get("grammatical_range_accuracy", {})
        pron_data = parsed_data.get("pronunciation", {})

        fluency_crit = CriterionEvaluation(
            score=fc_data.get("score", 6.5),
            strengths=fc_data.get("strengths", []),
            weaknesses=fc_data.get("weaknesses", []),
            evidence=fc_data.get("evidence", [])
        )
        lexical_crit = CriterionEvaluation(
            score=lr_data.get("score", 6.5),
            strengths=lr_data.get("strengths", []),
            weaknesses=lr_data.get("weaknesses", []),
            evidence=lr_data.get("evidence", [])
        )
        grammar_crit = CriterionEvaluation(
            score=gra_data.get("score", 6.0),
            strengths=gra_data.get("strengths", []),
            weaknesses=gra_data.get("weaknesses", []),
            evidence=gra_data.get("evidence", [])
        )
        pron_crit = CriterionEvaluation(
            score=pron_data.get("score", None),
            strengths=pron_data.get("strengths", []),
            weaknesses=pron_data.get("weaknesses", []),
            evidence=pron_data.get("evidence", [])
        )

        # Deterministic scoring calculation
        collected_scores = [fluency_crit.score, lexical_crit.score, grammar_crit.score, pron_crit.score]
        computed_overall = calculate_ielts_band(collected_scores)

        feedback_list = parsed_data.get("feedback", [
            "Elaborate on your points with extra detail and examples.",
            "Maintain a steady speaking pace with clear sentence linkage."
        ])

        return IELTSEvaluation(
            fluency=fluency_crit,
            lexical_resource=lexical_crit,
            grammar=grammar_crit,
            pronunciation=pron_crit,
            overall_band=computed_overall,
            feedback=feedback_list
        )

    def _parse_json_response(self, text: str) -> dict:
        if not text:
            return {}

        # Strip markdown code blocks if present
        clean_text = text.strip()
        if "```" in clean_text:
            clean_text = re.sub(r"```json\s*", "", clean_text)
            clean_text = re.sub(r"```\s*", "", clean_text)
        clean_text = clean_text.strip()

        try:
            return json.loads(clean_text)
        except Exception:
            # Match JSON object with regex if extra text exists
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            return {}
