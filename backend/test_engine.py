from conversation_memory import ConversationMemory


class IELTSTestEngine:

    def __init__(self):
        self.part = 1
        self.question_number = 0
        self.topic = "hometown"
        self.memory = ConversationMemory()
        self.questions = [
            {
                "id": 1,
                "topic": "hometown",
                "focus": "personal information",
                "question": "Where are you from?"
            },
            {
                "id": 2,
                "topic": "hometown",
                "focus": "likes",
                "question": "What do you like about your hometown?"
            },
            {
                "id": 3,
                "topic": "hometown",
                "focus": "weekend activities",
                "question": "What do you usually do at weekends?"
            },
            {
                "id": 4,
                "topic": "hometown",
                "focus": "future",
                "question": "Would you like to continue living there?"
            }
        ]

    def start(self):
        self.question_number = 1
        question = self.get_current_question()
        if question:
            self.memory.add_examiner_message(question["question"])
        return question

    def get_current_question(self):
        if self.question_number == 0:
            return self.start()

        index = self.question_number - 1
        if index >= len(self.questions):
            return None

        return self.questions[index]

    def submit_answer(self, transcript):
        current = self.get_current_question()
        if current is None:
            return None

        self.memory.add_candidate_message(transcript)

        result = {
            "question": current["question"],
            "answer": transcript,
            "part": self.part,
            "question_id": current["id"]
        }

        self.question_number += 1
        return result

    def record_question(self, question):
        self.memory.add_examiner_message(question)

    def finished(self):
        return self.question_number > len(self.questions)


if __name__ == "__main__":
    engine = IELTSTestEngine()
    question = engine.start()
    print("Examiner:", question["question"])
    answer = "I'm from Mymensingh."
    print("Student:", answer)
    result = engine.submit_answer(answer)
    print("\nSaved result:", result)
    next_question = engine.get_current_question()
    if next_question:
        print("\nNext Question:", next_question["question"])
