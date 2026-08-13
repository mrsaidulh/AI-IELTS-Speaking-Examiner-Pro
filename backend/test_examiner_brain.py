from examiner.session import IELTSSession, SessionState, IELTSPart
from examiner.manager import QuestionManager
from examiner.questions import PART_1_QUESTIONS
from examiner.prompts import SYSTEM_PROMPT, build_examiner_turn_prompt
from llm.qwen import QwenService

print("Testing IELTS Examiner Brain (Lesson 28)...")

# 1. Initialize session and question manager
session = IELTSSession(candidate_name="Alex")
session.state = SessionState.PART_1
manager = QuestionManager(PART_1_QUESTIONS)

# 2. Simulate asking 3 questions and recording answers
for i in range(3):
    q_data = manager.get_next_question()
    if not q_data:
        break

    session.set_question(q_data["question"])
    print(f"\n[Question {session.question_number} - {q_data['topic']}] {session.current_question}")

    # Simulated candidate answer
    sample_answer = f"I am answering question {i+1} about {q_data['topic']} in detail."
    ans_record = session.record_answer(sample_answer, duration=4.5)
    print(f"[Recorded Answer] {ans_record['answer']} ({ans_record['duration']}s)")

# 3. Verify session memory state
print("\n--- Session Answers Summary ---")
for idx, item in enumerate(session.answers, 1):
    print(f"Q{idx}: {item['question']} -> Answer: {item['answer']} ({item['duration']}s)")

print("\n--- System Prompt Verification ---")
print(SYSTEM_PROMPT.strip()[:180] + "...")

# 4. Test QwenService examiner prompt generation
qwen = QwenService()
transition = qwen.generate(
    prompt=build_examiner_turn_prompt("Part 1", "hometown", "Where are you from?", "I am from Mymensingh."),
    system_prompt=SYSTEM_PROMPT
)
print("\n--- Examiner Transition Output ---")
print("Transition:", transition)
print("\nLesson 28 Examiner Brain Test Completed Successfully!")
