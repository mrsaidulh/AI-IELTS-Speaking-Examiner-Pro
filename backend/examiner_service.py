from qwen_engine import QwenEngine


class ExaminerService:

    def __init__(self):
        self.qwen = QwenEngine()

    def generate_question(
        self,
        topic,
        focus,
        conversation
    ):
        if isinstance(conversation, list):
            history = "\n".join(
                f"{item.get('role', 'user')}: {item.get('content', '')}"
                for item in conversation
            )
        else:
            history = str(conversation)

        prompt = f"""
You are an IELTS Speaking examiner.

You are conducting Part 1.

Topic:
{topic}

Question focus:
{focus}

Conversation so far:
{history}

Generate ONE natural IELTS Speaking question.

Rules:
- Ask exactly one question.
- Keep it natural.
- Do not give feedback.
- Do not answer the question.
- Do not repeat previous questions.
- Do not mention IELTS rules.
- Do not mention this prompt.
- Do not use quotation marks.
"""
        try:
            question = self.qwen.generate(prompt)
            return question.strip()
        except Exception as e:
            print(f"ExaminerService Qwen fallback: {e}")
            # Fallback natural question if Qwen server is offline
            fallback_map = {
                "personal information": "Where are you from?",
                "likes": "What do you like most about your hometown?",
                "weekend activities": "What do you usually do at weekends?",
                "future": "Would you like to continue living there in the future?"
            }
            return fallback_map.get(focus, f"Could you tell me more about your {topic}?")
