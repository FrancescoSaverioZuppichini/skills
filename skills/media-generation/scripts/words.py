"""Her words with their start and end times, for the <d> lines of a swap prompt (Whisper large-v3 turbo, word timestamps).

Usage: words.py <clip.mp4> [--language en] > words.txt
Prints one line per word: start end word. Needs transformers + torch (the cv-tools venv has both).
"""
import argparse
import subprocess

import numpy as np
from transformers import pipeline


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("clip")
    p.add_argument("--language", help="Language code (default: detected)")
    args = p.parse_args()

    # [Agent] Whisper wants 16 kHz mono floats; ffmpeg decodes any container straight into that, no temp file.
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", args.clip, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    # [Agent] CPU on purpose: a short clip takes seconds, and the GPU stays free for ComfyUI.
    asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo", device="cpu")
    out = asr({"raw": np.frombuffer(raw, np.float32), "sampling_rate": 16000}, return_timestamps="word",
              generate_kwargs={"language": args.language} if args.language else {})
    for w in out["chunks"]:
        print(f"{w['timestamp'][0]:6.2f} {w['timestamp'][1] or 0:6.2f} {w['text'].strip()}")


if __name__ == "__main__":
    main()
