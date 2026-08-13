class ExaminerContext:
    def __init__(self):
        self.part = 1
        self.topic = ""
        self.question_number = 0
        self.questions_asked = []
        self.candidate_answers = []

    def set_part(self, part):
        self.part = part

    def set_topic(self, topic):
        self.topic = topic

    def add_question(self, question):
        self.questions_asked.append(question)
        self.question_number += 1

    def add_answer(self, answer):
        self.candidate_answers.append(answer)
