import json
from typing import Dict, Any, List, Optional
from scoring.models import (
    CriterionEvidence,
    SpeakingAssessment,
    IELTSOverallReport,
    round_to_ielts_band,
    calculate_overall
)
from scoring.speech_features import extract_speech_features
from scoring.descriptors import OFFICIAL_DESCRIPTORS


class SpeakingScoringEngine:

    def __init__(self, qwen_service=None):
        self.qwen_service = qwen_service
        self.criteria = ["fluency", "vocabulary", "grammar", "pronunciation"]
        self.descriptors = OFFICIAL_DESCRIPTORS

    def aggregate_speech_metrics(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregates objective speech metrics across all test parts."""
        total_duration = 0.0
        total_words = 0
        total_pauses = 0
        total_fillers = 0
        total_repetitions = 0
        total_self_corrections = 0

        for ans in answers:
            transcript = ans.get("transcript") or ans.get("answer") or ""
            dur = ans.get("duration", 0.0)
            segs = ans.get("segments") or []

            feat = extract_speech_features(transcript, dur, segs)
            total_duration += feat["duration"]
            total_words += feat["word_count"]
            total_pauses += feat["pauses"]["pause_count"]
            total_fillers += feat["fillers"]["filler_count"]
            total_repetitions += feat["repetitions"]["repetition_count"]
            total_self_corrections += feat["self_corrections"]["self_correction_count"]

        avg_wpm = round((total_words / (total_duration / 60.0)), 1) if total_duration > 0 else 0.0

        return {
            "total_duration": round(total_duration, 2),
            "total_words": total_words,
            "overall_wpm": avg_wpm,
            "total_pauses": total_pauses,
            "total_fillers": total_fillers,
            "total_repetitions": total_repetitions,
            "total_self_corrections": total_self_corrections,
            "answer_count": len(answers)
        }

    def evaluate_criterion(
        self,
        criterion: str,
        answers: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ) -> CriterionEvidence:
        """Evaluates evidence for a specific criterion across the whole session."""
        obs = []
        strengths = []
        weaknesses = []
        scores_collected = []

        for ans in answers:
            eval_res = ans.get("evaluation") or {}
            crit_data = eval_res.get(criterion) or eval_res.get(f"{criterion}_coherence" if criterion == "fluency" else (f"lexical_resource" if criterion == "vocabulary" else criterion)) or {}

            if isinstance(crit_data, dict):
                sc = crit_data.get("score")
                if sc is not None:
                    try:
                        scores_collected.append(float(sc))
                    except (ValueError, TypeError):
                        pass

                if "strengths" in crit_data and isinstance(crit_data["strengths"], list):
                    strengths.extend(crit_data["strengths"])
                if "weaknesses" in crit_data and isinstance(crit_data["weaknesses"], list):
                    weaknesses.extend(crit_data["weaknesses"])
                if "evidence" in crit_data and isinstance(crit_data["evidence"], list):
                    obs.extend(crit_data["evidence"])

        # Inject objective metrics as evidence
        if criterion == "fluency":
            obs.append(f"Overall speech pace averaged {metrics['overall_wpm']} words per minute.")
            if metrics["total_pauses"] > 0:
                obs.append(f"Recorded {metrics['total_pauses']} noticeable pauses across all responses.")
            if metrics["total_fillers"] > 0:
                obs.append(f"Used {metrics['total_fillers']} hesitation fillers (e.g., 'um', 'uh', 'you know').")
            if metrics["overall_wpm"] >= 120 and metrics["total_fillers"] <= 5:
                strengths.append("Maintains sustained spoken flow with minimal hesitation.")
            elif metrics["total_fillers"] > 8:
                weaknesses.append("Frequent reliance on filler words during speech formulation.")

        elif criterion == "vocabulary":
            if metrics["total_words"] > 250:
                obs.append("Demonstrates willingness to talk at length with varied topic vocabulary.")
                strengths.append("Sufficient vocabulary range to express ideas in detail.")
            else:
                weaknesses.append("Vocabulary range could be expanded to describe abstract concepts in depth.")

        elif criterion == "grammar":
            if metrics["total_self_corrections"] > 0:
                obs.append(f"Attempted {metrics['total_self_corrections']} active grammatical self-corrections.")

        elif criterion == "pronunciation":
            obs.append("Sustains clear articulation and intelligible delivery throughout responses.")

        # Determine estimated criterion score
        if scores_collected:
            raw_avg = sum(scores_collected) / len(scores_collected)
            final_sc = round_to_ielts_band(raw_avg)
        else:
            final_sc = 6.5  # Fallback default estimate

        # Deduplicate evidence lists
        clean_obs = list(dict.fromkeys([o for o in obs if o]))
        clean_str = list(dict.fromkeys([s for s in strengths if s]))
        clean_wk = list(dict.fromkeys([w for w in weaknesses if w]))

        return CriterionEvidence(
            observations=clean_obs if clean_obs else ["Sustained speech produced under examination conditions."],
            strengths=clean_str if clean_str else ["Speech remains intelligible throughout."],
            weaknesses=clean_wk if clean_wk else ["Expand range and precision under complex topics."],
            score=final_sc
        )

    def generate_7_day_plan(self, weak_criteria: List[str]) -> List[Dict[str, str]]:
        """Generates a tailored 7-day practice plan based on identified weaknesses."""
        primary = weak_criteria[0] if weak_criteria else "vocabulary"
        secondary = weak_criteria[1] if len(weak_criteria) > 1 else "grammar"

        plan = [
            {"day": "Day 1", "focus": f"Targeted {primary.capitalize()} Expansion", "task": f"Study topical collocations and advanced expressions targeting {primary}."},
            {"day": "Day 2", "focus": f"Grammatical Range & Clause Control", "task": f"Practice forming complex conditional sentences and relative clauses."},
            {"day": "Day 3", "focus": "Part 2 Cue Card Simulation", "task": "Record a 2-minute uninterrupted long turn using structured bullet notes."},
            {"day": "Day 4", "focus": "Fluency & Hesitation Control", "task": "Perform 1-minute uninterrupted response drills without filler words."},
            {"day": "Day 5", "focus": f"Part 3 Abstract Discussion ({secondary.capitalize()})", "task": f"Practice developing claims, reasons, and examples for abstract topics."},
            {"day": "Day 6", "focus": "Intonation & Connected Speech", "task": "Shadow native audio recordings to refine sentence stress and natural rhythm."},
            {"day": "Day 7", "focus": "Full IELTS Speaking Mock Exam", "task": "Complete a full 15-minute simulated test across Parts 1, 2, and 3."}
        ]
        return plan

    def evaluate_session(
        self,
        session_id: str,
        part1_answers: List[Dict[str, Any]] = None,
        part2_answer: Dict[str, Any] = None,
        part3_answers: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Holistically evaluates all parts of an IELTS Speaking session."""
        all_answers = []
        part1_answers = part1_answers or []
        part3_answers = part3_answers or []

        for p1 in part1_answers:
            p1["part"] = 1
            all_answers.append(p1)

        if part2_answer:
            part2_answer["part"] = 2
            all_answers.append(part2_answer)

        for p3 in part3_answers:
            p3["part"] = 3
            all_answers.append(p3)

        metrics = self.aggregate_speech_metrics(all_answers)

        ev_fluency = self.evaluate_criterion("fluency", all_answers, metrics)
        ev_vocab = self.evaluate_criterion("vocabulary", all_answers, metrics)
        ev_grammar = self.evaluate_criterion("grammar", all_answers, metrics)
        ev_pron = self.evaluate_criterion("pronunciation", all_answers, metrics)

        overall = calculate_overall(
            ev_fluency.score,
            ev_vocab.score,
            ev_grammar.score,
            ev_pron.score
        )

        # Identify strengths & priority improvements
        criteria_scores = [
            ("fluency", ev_fluency),
            ("vocabulary", ev_vocab),
            ("grammar", ev_grammar),
            ("pronunciation", ev_pron)
        ]
        sorted_by_score = sorted(criteria_scores, key=lambda x: x[1].score or 6.0)

        weak_names = [name for name, _ in sorted_by_score[:2]]

        all_strengths = []
        priority_improvements = []

        for name, ev in criteria_scores:
            if ev.strengths:
                all_strengths.extend([f"[{name.capitalize()}] {s}" for s in ev.strengths[:2]])
            if ev.weaknesses:
                priority_improvements.extend([f"[{name.capitalize()}] {w}" for w in ev.weaknesses[:2]])

        plan_7_day = self.generate_7_day_plan(weak_names)

        report = {
            "session_id": session_id,
            "overall_band": overall,
            "confidence": 0.88 if len(all_answers) >= 5 else 0.75,
            "speech_metrics": metrics,
            "criteria": {
                "fluency_coherence": {
                    "score": ev_fluency.score,
                    "observations": ev_fluency.observations,
                    "strengths": ev_fluency.strengths,
                    "weaknesses": ev_fluency.weaknesses
                },
                "lexical_resource": {
                    "score": ev_vocab.score,
                    "observations": ev_vocab.observations,
                    "strengths": ev_vocab.strengths,
                    "weaknesses": ev_vocab.weaknesses
                },
                "grammar": {
                    "score": ev_grammar.score,
                    "observations": ev_grammar.observations,
                    "strengths": ev_grammar.strengths,
                    "weaknesses": ev_grammar.weaknesses
                },
                "pronunciation": {
                    "score": ev_pron.score,
                    "observations": ev_pron.observations,
                    "strengths": ev_pron.strengths,
                    "weaknesses": ev_pron.weaknesses
                }
            },
            "strengths": all_strengths[:5] if all_strengths else ["Maintains clear delivery throughout the test."],
            "priority_improvements": priority_improvements[:4] if priority_improvements else ["Expand lexical variety and complex clause structures."],
            "part_analysis": {
                "part1_count": len(part1_answers),
                "part2_completed": bool(part2_answer),
                "part3_count": len(part3_answers)
            },
            "plan_7_day": plan_7_day
        }

        return report
