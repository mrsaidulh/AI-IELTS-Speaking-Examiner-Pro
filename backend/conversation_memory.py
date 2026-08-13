class ConversationMemory:
    def __init__(self):
        self.messages = []

    def add_examiner_message(self, message):
        self.messages.append({
            "role": "examiner",
            "content": message
        })

    def add_candidate_message(self, message):
        self.messages.append({
            "role": "candidate",
            "content": message
        })

    def get_messages(self):
        return self.messages

    def get_recent_messages(self, limit=10):
        return self.messages[-limit:]
