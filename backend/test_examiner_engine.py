from examiner_engine import IELTSExaminerEngine

engine = IELTSExaminerEngine()

print("Current part:")
print(engine.get_part())

print("Question:")
print(engine.next_question())

print("Question:")
print(engine.next_question())

engine.move_to_part_2()

print("Current part:")
print(engine.get_part())

print("Question:")
print(engine.next_question())

engine.move_to_part_3()

print("Current part:")
print(engine.get_part())
