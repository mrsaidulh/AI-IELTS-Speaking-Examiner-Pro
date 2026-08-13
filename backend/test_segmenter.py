import time
from speech_segmenter import SpeechSegmenter
from rolling_buffer import RollingBuffer
from speech_state import SpeechState

segmenter = SpeechSegmenter(silence_timeout=0.5, min_speech_duration=0.1, max_answer_duration=3.0)
rolling_buf = RollingBuffer(max_chunks=3)

# Test 1: Rolling buffer behavior
for i in range(5):
    rolling_buf.add(f"chunk_{i}".encode())

print("Rolling buffer contents (max 3):", [c.decode() for c in rolling_buf.get()])

# Test 2: Speech state transitions
events = []
# Speech starts
events.append(segmenter.process(speech_detected=True))
# Speech continues
events.append(segmenter.process(speech_detected=True))
events.append(segmenter.process(speech_detected=True))
# Pause occurs
events.append(segmenter.process(speech_detected=False))
# Silence timeout wait
time.sleep(0.6)
events.append(segmenter.process(speech_detected=False))

print("Segmenter state:", segmenter.state.value)
print("Processed events sequence:", events)
