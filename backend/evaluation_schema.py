class IELTSScore:
    def __init__(
        self,
        fluency,
        lexical,
        grammar,
        pronunciation
    ):
        self.fluency = fluency
        self.lexical = lexical
        self.grammar = grammar
        self.pronunciation = pronunciation

    def overall(self):
        return round(
            (
                self.fluency
                + self.lexical
                + self.grammar
                + self.pronunciation
            ) / 4,
            1
        )
