class ConversationSummary:
    def __init__(self):
        self.summary = ""

    def update(self, new_information):
        if not self.summary:
            self.summary = new_information
        else:
            self.summary += " " + new_information

    def get(self):
        return self.summary
