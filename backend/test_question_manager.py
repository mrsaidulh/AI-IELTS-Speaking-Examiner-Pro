from question_manager import QuestionManager

manager = QuestionManager()

for i in range(12):
    question = manager.get_current_question()
    print(f"Part {manager.part}: {question}")
    question = manager.next_question()
    if question is None:
        print("TEST FINISHED")
        break
