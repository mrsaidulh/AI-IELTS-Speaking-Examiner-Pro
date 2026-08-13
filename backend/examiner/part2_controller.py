import time
import random
import uuid
from examiner.part2 import Part2State, PART_2_CONFIG
from examiner.cue_cards import CUE_CARDS
from examiner.session import IELTSSession, SessionState


class Part2Controller:
    PREPARATION_TIME = PART_2_CONFIG.get("preparation_time", 60)
    LONG_TURN_TIME = PART_2_CONFIG.get("long_turn_time", 120)

    def __init__(self, cue_cards=None, evaluator=None, session_id=None):
        self.cue_cards = cue_cards or CUE_CARDS
        self.evaluator = evaluator
        self.session_id = session_id or str(uuid.uuid4())
        self.session = IELTSSession(candidate_name="Candidate")
        self.session.state = SessionState.PART_2

        self.current_card = None
        self.used_cards = set()
        self.state = Part2State.INTRODUCTION

        # Server-side authoritative timers using time.monotonic()
        self.preparation_started_at = None
        self.long_turn_started_at = None
        
        self.evaluations = []
        self.history = []

    def select_cue_card(self):
        available = [card for card in self.cue_cards if card["id"] not in self.used_cards]
        if not available:
            self.used_cards.clear()
            available = self.cue_cards

        self.current_card = random.choice(available)
        self.used_cards.add(self.current_card["id"])
        self.state = Part2State.CUE_CARD

        self.history.append({
            "role": "examiner",
            "text": f"Part 2 Cue Card: {self.current_card['prompt']}",
            "cue_card": self.current_card
        })

        return self.current_card

    def start_preparation(self):
        self.state = Part2State.PREPARATION
        self.preparation_started_at = time.monotonic()
        return {
            "type": "timer_started",
            "timer": "preparation",
            "duration": self.PREPARATION_TIME,
            "started_at": self.preparation_started_at
        }

    def get_preparation_remaining(self):
        if self.preparation_started_at is None:
            return self.PREPARATION_TIME
        elapsed = time.monotonic() - self.preparation_started_at
        return max(0.0, self.PREPARATION_TIME - elapsed)

    def is_preparation_finished(self):
        return self.get_preparation_remaining() <= 0

    def finish_preparation(self):
        self.state = Part2State.READY
        return {
            "type": "preparation_complete",
            "message": "Preparation time is complete. You may start speaking now."
        }

    def start_long_turn(self):
        self.state = Part2State.LONG_TURN
        self.long_turn_started_at = time.monotonic()
        return {
            "type": "timer_started",
            "timer": "long_turn",
            "duration": self.LONG_TURN_TIME,
            "started_at": self.long_turn_started_at
        }

    def get_long_turn_remaining(self):
        if self.long_turn_started_at is None:
            return self.LONG_TURN_TIME
        elapsed = time.monotonic() - self.long_turn_started_at
        return max(0.0, self.LONG_TURN_TIME - elapsed)

    def is_long_turn_expired(self):
        return self.get_long_turn_remaining() <= 0

    def evaluate_task_coverage(self, transcript: str, card: dict) -> dict:
        if not transcript or not card:
            return {"score": 0.0, "covered_points": [], "missing_points": card.get("points", []) if card else []}

        low_transcript = transcript.lower()
        points = card.get("points", [])
        covered = []
        missing = []

        for p in points:
            keywords = [w for w in p.lower().replace("and explain ", "").split() if len(w) > 3]
            match_count = sum(1 for kw in keywords if kw in low_transcript)
            if match_count >= 1 or len(keywords) == 0:
                covered.append(p)
            else:
                missing.append(p)

        score = round(len(covered) / max(1, len(points)), 2)
        return {
            "score": score,
            "covered_points": covered,
            "missing_points": missing
        }

    def process_long_turn_answer(self, transcript: str, duration: float, segments: list = None):
        self.state = Part2State.FINISHING
        card = self.current_card or {}
        
        task_coverage = self.evaluate_task_coverage(transcript, card)

        self.history.append({
            "role": "candidate",
            "text": transcript,
            "duration": duration
        })

        rec = self.session.record_answer(transcript, duration)

        evaluation_result = None
        if self.evaluator:
            prompt_context = f"Cue Card: {card.get('prompt', '')}\nPoints: {', '.join(card.get('points', []))}"
            try:
                evaluation_result = self.evaluator.evaluate_answer(
                    question=prompt_context,
                    answer=transcript,
                    duration=duration,
                    segments=segments
                )
                if isinstance(evaluation_result, dict):
                    evaluation_result["task_coverage"] = task_coverage

                self.evaluations.append({
                    "cue_card": card,
                    "transcript": transcript,
                    "duration": duration,
                    "task_coverage": task_coverage,
                    "evaluation": evaluation_result
                })
            except Exception as e:
                print(f"Part 2 evaluation error: {e}")

        self.state = Part2State.COMPLETED

        return {
            "record": rec,
            "task_coverage": task_coverage,
            "evaluation": evaluation_result
        }

    def is_completed(self):
        return self.state == Part2State.COMPLETED

    def build_event(self, event_type: str, payload: dict = None) -> dict:
        event = {
            "type": event_type,
            "session_id": self.session_id,
            "part": "part2",
            "state": self.state.value if isinstance(self.state, Part2State) else str(self.state)
        }
        if payload:
            event.update(payload)
        return event
