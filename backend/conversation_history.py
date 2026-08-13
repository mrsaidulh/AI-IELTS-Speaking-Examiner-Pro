def build_history(conversations):
    history = []
    for item in conversations:
        history.append(f"Examiner: {item.question}")
        history.append(f"Candidate: {item.answer}")
    return "\n".join(history)
