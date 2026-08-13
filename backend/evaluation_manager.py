class EvaluationManager:
    def __init__(self, llm_client):
        self.llm = llm_client

    def evaluate(
        self,
        transcript,
        part,
        question,
        conversation
    ):
        from evaluator_prompt import (
            build_evaluator_prompt
        )

        prompt = build_evaluator_prompt(
            transcript=transcript,
            part=part,
            question=question,
            conversation=conversation
        )

        result = self.llm.generate(
            prompt
        )

        return result
