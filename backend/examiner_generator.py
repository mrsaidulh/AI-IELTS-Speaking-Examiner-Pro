from advanced_examiner_prompt import build_advanced_examiner_prompt

class ExaminerGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client

    def generate(
        self,
        part,
        topic,
        current_question,
        conversation,
        candidate_facts,
        questions_asked
    ):
        prompt = build_advanced_examiner_prompt(
            part=part,
            topic=topic,
            current_question=current_question,
            conversation=conversation,
            candidate_facts=candidate_facts,
            questions_asked=questions_asked
        )

        response = self.llm.generate(prompt)
        return response.strip()
