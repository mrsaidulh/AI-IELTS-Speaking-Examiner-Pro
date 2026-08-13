class Part2Manager:
    PREPARATION_TIME = 60
    SPEAKING_TIME = 120

    def __init__(self):
        self.state = "cue_card"

    def show_cue_card(self):
        self.state = "cue_card"
        return self.state

    def start_preparation(self):
        self.state = "preparation"
        return self.state

    def start_speaking(self):
        self.state = "speaking"
        return self.state

    def finish_speaking(self):
        self.state = "completed"
        return self.state
