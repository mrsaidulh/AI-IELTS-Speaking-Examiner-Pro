import random
import re
from examiner.templates import QUESTION_TEMPLATES, TRANSITIONS


class Part3Strategy:

    def determine_next_type(self, current_type: str = "general") -> str:
        allowed = TRANSITIONS.get(current_type, ["opinion", "comparison", "future"])
        return random.choice(allowed)

    def validate_question(self, question: str, topic: str, used_questions: set) -> bool:
        if not question or not isinstance(question, str):
            return False

        q_clean = question.strip()
        words = q_clean.split()

        # Length constraint
        if len(words) < 4 or len(words) > 35:
            return False

        # Must end with question mark
        if not q_clean.endswith("?"):
            return False

        # Reject overly personal Part 1 style phrasing
        personal_patterns = [
            r"\bdo you like\b", r"\bwhere do you\b", r"\bwhat is your favorite\b",
            r"\btell me about your\b", r"\bwhat did you do\b"
        ]
        for pat in personal_patterns:
            if re.search(pat, q_clean.lower()):
                return False

        # Duplicate check (exact and normalized)
        norm_q = q_clean.lower().replace("?", "").strip()
        for used in used_questions:
            if norm_q == used.lower().replace("?", "").strip():
                return False

        return True

    def get_template_fallback(self, topic_title: str, target_type: str) -> str:
        templates = QUESTION_TEMPLATES.get(target_type, QUESTION_TEMPLATES["comparison"])
        tmpl = random.choice(templates)
        return tmpl.format(topic=topic_title.lower())
