def question_already_asked(question, questions):
    normalized = question.lower().strip()

    for previous in questions:
        previous_normalized = previous.lower().strip()
        if normalized == previous_normalized:
            return True

    return False
