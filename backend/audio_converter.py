import subprocess
import os

def webm_to_wav(input_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-ar",
        "16000",
        "-ac",
        "1",
        output_path
    ]
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return output_path

def convert_to_wav(input_file, output_file):
    try:
        return webm_to_wav(input_file, output_file)
    except Exception as e:
        print(f"FFmpeg conversion note: {e}")
        return input_file

