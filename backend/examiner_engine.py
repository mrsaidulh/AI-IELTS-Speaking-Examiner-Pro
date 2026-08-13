class IELTSExaminerEngine:
    def __init__(self):
        self.part = 1
        self.topic_index = 0
        self.question_index = 0
        self.status = "active"

    def get_part(self):
        return self.part

    def get_question_number(self):
        return self.question_index

    def next_question(self):
        self.question_index += 1
        return self.question_index

    def move_to_part_2(self):
        self.part = 2
        self.topic_index = 0
        self.question_index = 0

    def move_to_part_3(self):
        self.part = 3
        self.topic_index = 0
        self.question_index = 0

    def finish_test(self):
        self.status = "completed"
