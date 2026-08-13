import re
from dataclasses import dataclass
from typing import Optional, List
from examiner.enums import Part, ExaminerState


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str
    sanitized_text: str
    fallback_text: Optional[str] = None


class ExaminerOutputValidator:
    """
    Defense-in-Depth Validation Layer for LLM Examiner responses.
    Validates generated text against IELTS examination constraints before TTS synthesis.
    """
    
    @staticmethod
    def validate_examiner_output(
        text: str,
        current_part: int,
        current_state: str,
        expected_question: Optional[str] = None
    ) -> ValidationResult:
        if not text or not text.strip():
            fallback = expected_question or "Could you please continue?"
            return ValidationResult(
                is_valid=False,
                reason="Empty text received from LLM",
                sanitized_text=fallback,
                fallback_text=fallback
            )

        # 1. Strip markdown clutter & quotes
        clean_text = text.strip().replace('```', '').replace('"', '').strip()

        # 2. Check for multiple questions in single turn
        question_marks = clean_text.count("?")
        if question_marks > 1:
            # Extract first question sentence
            sentences = re.split(r'(?<=[.!?])\s+', clean_text)
            q_sentences = [s for s in sentences if '?' in s]
            sanitized = q_sentences[0] if q_sentences else clean_text
            return ValidationResult(
                is_valid=False,
                reason=f"Multiple questions detected ({question_marks} question marks). Truncated to single question.",
                sanitized_text=sanitized,
                fallback_text=sanitized
            )

        # 3. Check for illegal state/part transitions in generated text
        low_text = clean_text.lower()
        if current_part == 1 and ("part 3" in low_text or "part 2" in low_text and current_state != ExaminerState.PART1.value):
            if "move to part 2" in low_text and current_state == ExaminerState.PART1.value:
                pass # Legitimate transition announcement
            elif "part 3" in low_text:
                fallback = expected_question or "Let's continue with our discussion."
                return ValidationResult(
                    is_valid=False,
                    reason="Unauthorized Part 3 jump detected during Part 1",
                    sanitized_text=fallback,
                    fallback_text=fallback
                )

        # 4. Check for length constraints (> 120 words for standard examiner questions)
        word_count = len(clean_text.split())
        if word_count > 120 and current_state != ExaminerState.PART2_PREPARATION.value:
            # Truncate to first 2-3 sentences
            sentences = re.split(r'(?<=[.!?])\s+', clean_text)
            truncated = " ".join(sentences[:2])
            return ValidationResult(
                is_valid=False,
                reason=f"Examiner output exceeded word limit ({word_count} words). Truncated.",
                sanitized_text=truncated,
                fallback_text=truncated
            )

        return ValidationResult(
            is_valid=True,
            reason="Passes all IELTS examiner output validation rules",
            sanitized_text=clean_text
        )
