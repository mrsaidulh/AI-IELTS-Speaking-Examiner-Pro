from answer_buffer import AnswerBuffer

buffer = AnswerBuffer()

buffer.add(b"hello")
buffer.add(b"world")

print("Bytes:", buffer.get_bytes())
print("Size:", buffer.size())

buffer.clear()
print("Size after clear:", buffer.size())
