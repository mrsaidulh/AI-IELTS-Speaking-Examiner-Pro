from kokoro_engine import KokoroEngine

try:
    engine = KokoroEngine()
    output = engine.synthesize(
        "What do you like about your hometown?",
        "examiner_test.mp3"
    )
    print("Generated:", output)
except Exception as e:
    print(f"Kokoro engine test note: {e}")
