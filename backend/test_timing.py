from timing_engine import TimingEngine

timer = TimingEngine()

timer.start_preparation()

print("State:")
print(timer.state)

print("Remaining:")
print(timer.remaining())

print("Finished:")
print(timer.is_finished())
