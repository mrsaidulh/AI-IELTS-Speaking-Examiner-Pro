from faster_whisper import WhisperModel
import os
import sys

def main():
    audio_file = "audio.wav"
    if not os.path.exists(audio_file):
        print(f"File {audio_file} not found. Please place an audio.wav file in the current directory.")
        return

    print("Loading Whisper model (small, int8, CPU)...")
    model = WhisperModel(
        "small",
        device="cpu",
        compute_type="int8"
    )

    print("Transcribing...")
    segments, info = model.transcribe(
        audio_file,
        beam_size=5
    )

    print("Detected language:", info.language)
    print("Language probability:", info.language_probability)

    print("\nTranscription:")
    print("-" * 50)

    for segment in segments:
        print(segment.text)

    print("-" * 50)

if __name__ == "__main__":
    main()
