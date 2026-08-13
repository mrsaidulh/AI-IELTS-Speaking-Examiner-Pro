from ielts_structure import IELTS_TEST_STRUCTURE

class QuestionManager:
    def __init__(self):
        self.part = 1
        self.topic_index = 0
        self.question_index = 0

    def get_current_question(self):
        if self.part == 1:
            topics = IELTS_TEST_STRUCTURE[1]["topics"]
            topic = topics[self.topic_index]
            questions = topic["questions"]
            return questions[self.question_index]

        if self.part == 2:
            return IELTS_TEST_STRUCTURE[2]["cue_card"]["topic"]

        if self.part == 3:
            questions = IELTS_TEST_STRUCTURE[3]["questions"]
            return questions[self.question_index]

    def next_question(self):
        if self.part == 1:
            topics = IELTS_TEST_STRUCTURE[1]["topics"]
            current_topic = topics[self.topic_index]
            if self.question_index < len(current_topic["questions"]) - 1:
                self.question_index += 1
            else:
                self.topic_index += 1
                self.question_index = 0

                if self.topic_index >= len(topics):
                    self.part = 2
                    self.topic_index = 0
                    self.question_index = 0

        elif self.part == 2:
            self.part = 3
            self.question_index = 0

        elif self.part == 3:
            questions = IELTS_TEST_STRUCTURE[3]["questions"]
            if self.question_index < len(questions) - 1:
                self.question_index += 1
            else:
                return None

        return self.get_current_question()
