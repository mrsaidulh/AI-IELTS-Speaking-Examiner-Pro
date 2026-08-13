class CandidateContext:
    def __init__(self):
        self.facts = []
        self.topics = []
        self.questions_asked = []

    def add_fact(self, fact):
        if fact not in self.facts:
            self.facts.append(fact)

    def add_topic(self, topic):
        if topic not in self.topics:
            self.topics.append(topic)

    def add_question(self, question):
        self.questions_asked.append(question)
