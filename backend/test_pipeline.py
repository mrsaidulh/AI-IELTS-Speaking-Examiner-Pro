from voice_pipeline import process_audio
import os

audio_file = "audio.wav"

if not os.path.exists(audio_file):
    print(f"File {audio_file} not found. Please place an audio.wav file in the current directory.")
else:
    result = process_audio(audio_file)

    print("\n==============================")
    print("RESULT")
    print("==============================")

    print("Candidate:")
    print(result["candidate_text"])

    print("\nExaminer:")
    print(result["examiner_text"])

    print("\nAudio:")
    print(result["audio_file"])
