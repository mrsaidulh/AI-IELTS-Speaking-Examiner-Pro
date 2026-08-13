import uuid
from examiner.part3 import Part3State, PART_3_CONFIG
from examiner.part3_topics import PART3_TOPICS
from examiner.strategy import Part3Strategy
from examiner.session import IELTSSession, SessionState


class Part3Controller:

    def __init__(self, topic_key="education", evaluator=None, qwen_service=None, session_id=None):
        self.topic_key = topic_key if topic_key in PART3_TOPICS else "education"
        self.topic_data = PART3_TOPICS[self.topic_key]
        self.topic_title = self.topic_data["title"]

        self.evaluator = evaluator
        self.qwen_service = qwen_service
        self.strategy_engine = Part3Strategy()

        self.session_id = session_id or str(uuid.uuid4())
        self.session = IELTSSession(candidate_name="Candidate")
        self.session.state = SessionState.PART_3

        self.state = Part3State.INTRODUCTION
        self.question_count = 0
        self.max_questions = PART_3_CONFIG.get("max_questions", 6)

        self.current_question = None
        self.current_type = "general"
        self.used_questions = set()

        self.part3_history = []
        self.evaluations = []
        self.summary_claims = []

    def get_first_question(self) -> dict:
        questions = self.topic_data["questions"]
        q_obj = questions[0] if questions else {
            "type": "general",
            "question": "Why is this topic considered important in society today?"
        }

        self.current_question = q_obj["question"]
        self.current_type = q_obj.get("type", "general")
        self.used_questions.add(self.current_question)
        self.question_count = 1
        self.state = Part3State.QUESTION

        self.session.set_question(self.current_question)

        return {
            "question": self.current_question,
            "type": self.current_type,
            "topic": self.topic_title,
            "question_number": self.question_count,
            "max_questions": self.max_questions
        }

    def analyze_idea_development(self, transcript: str) -> dict:
        if not transcript:
            return {"claim": False, "reason": False, "example": False, "explanation": False}

        low = transcript.lower()
        has_claim = len(transcript.split()) >= 3
        has_reason = any(w in low for w in ["because", "since", "as a result", "due to", "the reason is"])
        has_example = any(w in low for w in ["for example", "for instance", "such as", "take ", "like "])
        has_explanation = any(w in low for w in ["this means", "in other words", "therefore", "thus", "consequently"])

        return {
            "claim": has_claim,
            "reason": has_reason,
            "example": has_example,
            "explanation": has_explanation
        }

    def determine_next_question(self, last_transcript: str) -> str:
        if self.question_count >= self.max_questions:
            self.state = Part3State.COMPLETED
            return None

        next_type = self.strategy_engine.determine_next_type(self.current_type)
        candidate_question = None

        # Attempt Qwen generation if service available
        if self.qwen_service:
            prompt = f"""You are an official IELTS Speaking Part 3 Examiner generating a follow-up discussion question.

Topic: {self.topic_title}
Required Question Category: {next_type}
Candidate's previous answer: "{last_transcript}"

Strict Rules:
1. Return ONLY the question string ending with a question mark.
2. Ask an abstract, high-level societal discussion question.
3. Stay strictly on the topic of {self.topic_title}.
4. DO NOT ask personal questions ("do you like", "in your life").
5. Keep length between 8 and 25 words.
6. Do not include markdown or quotation marks.
"""
            try:
                raw_q = self.qwen_service.generate_response(prompt).strip().replace('"', '')
                if self.strategy_engine.validate_question(raw_q, self.topic_title, self.used_questions):
                    candidate_question = raw_q
            except Exception as e:
                print(f"Qwen Part 3 follow-up generation error: {e}")

        # Fallback to topic question bank or template engine
        if not candidate_question:
            # Check topic bank first
            bank_matches = [q["question"] for q in self.topic_data["questions"] if q["question"] not in self.used_questions]
            if bank_matches:
                candidate_question = bank_matches[0]
            else:
                candidate_question = self.strategy_engine.get_template_fallback(self.topic_title, next_type)

        self.current_question = candidate_question
        self.current_type = next_type
        self.used_questions.add(self.current_question)
        self.question_count += 1
        self.state = Part3State.QUESTION

        self.session.set_question(self.current_question)

        return self.current_question

    def process_answer(self, transcript: str, duration: float, segments: list = None) -> dict:
        self.state = Part3State.EVALUATING

        idea_dev = self.analyze_idea_development(transcript)
        self.summary_claims.append(transcript[:100])

        self.part3_history.append({
            "question_number": self.question_count,
            "question": self.current_question,
            "type": self.current_type,
            "answer": transcript,
            "duration": duration,
            "idea_development": idea_dev
        })

        rec = self.session.record_answer(transcript, duration)

        evaluation_result = None
        if self.evaluator:
            try:
                evaluation_result = self.evaluator.evaluate_answer(
                    question=self.current_question or "Part 3 Discussion",
                    answer=transcript,
                    duration=duration,
                    segments=segments
                )
                if isinstance(evaluation_result, dict):
                    evaluation_result["idea_development"] = idea_dev

                self.evaluations.append({
                    "question_number": self.question_count,
                    "question": self.current_question,
                    "transcript": transcript,
                    "idea_development": idea_dev,
                    "evaluation": evaluation_result
                })
            except Exception as e:
                print(f"Part 3 evaluation exception: {e}")

        if self.question_count >= self.max_questions:
            self.state = Part3State.COMPLETED

        return {
            "record": rec,
            "idea_development": idea_dev,
            "evaluation": evaluation_result
        }

    def is_completed(self) -> bool:
        return self.state == Part3State.COMPLETED or self.question_count >= self.max_questions

    def build_event(self, event_type: str, payload: dict = None) -> dict:
        event = {
            "type": event_type,
            "session_id": self.session_id,
            "part": "part3",
            "state": self.state.value if isinstance(self.state, Part3State) else str(self.state),
            "topic": self.topic_title,
            "question_number": self.question_count,
            "max_questions": self.max_questions
        }
        if payload:
            event.update(payload)
        return event
