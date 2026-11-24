"""Transcribe a clip's speech or singing with word times (Whisper large-v3 turbo).

Usage: transcribe.py <clip> [--format words|text|json|srt|ass] [--language en] [--device auto|cuda|cpu] > out
  words  one line per word: start end word (default; what the swap prompts read)
  text   the plain transcript
  json   {"text": ..., "words": [{"start", "end", "word"}]}
  srt    subtitle cues, a new cue at a pause, a sentence end or every 7 words
  ass    one big word at a time in the middle of the clip's frame, like a lyric video (burn: ffmpeg -vf ass=<file>)
Needs transformers + torch (the cv-tools venv has both).
"""
import argparse
import json
import subprocess

import numpy as np
import torch
from transformers import pipeline

MODEL = "openai/whisper-large-v3-turbo"
NEEDS_GB = 6  # bf16 peak was 4.5 GiB on a 15 s clip
ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,Nimbus Sans Narrow,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,{shadow},5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""


def pick_device(name):
    if name != "auto":
        return name
    # [Agent] ComfyUI often holds the GPU: use it only when there's room, else the CPU (60 s instead of 2 s, same words).
    return "cuda" if torch.cuda.is_available() and torch.cuda.mem_get_info()[0] / 2**30 >= NEEDS_GB else "cpu"


def read_audio(path):
    # [Agent] Whisper wants 16 kHz mono floats; ffmpeg decodes any container straight into that, no temp file.
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def transcribe(path, language, device):
    asr = pipeline("automatic-speech-recognition", model=MODEL, device=device,
                   torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32)
    out = asr({"raw": read_audio(path), "sampling_rate": 16000}, return_timestamps="word",
              generate_kwargs={"language": language} if language else {})
    words = [{"start": w["timestamp"][0], "end": w["timestamp"][1] or w["timestamp"][0], "word": w["text"].strip()} for w in out["chunks"]]
    return out["text"].strip(), words


def cues(words, gap=0.6, size=7):
    group = []
    for i, w in enumerate(words):
        group.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if not nxt or nxt["start"] - w["end"] > gap or w["word"][-1:] in ".!?" or len(group) == size:
            yield group
            group = []


def stamp(seconds):
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def read_size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout
    return [int(x) for x in out.strip().split(",")]


def ass_stamp(seconds):
    cs = round(seconds * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass(words, width, height):
    # [Agent] PlayRes = the clip's own pixels, so libass draws 1:1 and the text never stretches.
    lines = [ASS_HEAD.format(width=width, height=height, size=height // 3, shadow=round(height / 400, 1))]
    # [Agent] Each word stays up until the next one starts, so the screen never goes blank between words; the last
    # [Agent] one ends with its sound.
    ends = [w["start"] for w in words[1:]] + [w["end"] for w in words[-1:]]
    for w, end in zip(words, ends):
        text = w["word"].strip(".,!?;:")
        # [Agent] A third of the height reads as one big word, but a long word in a narrow (vertical) frame would run
        # [Agent] off the sides: shrink it to fill at most 90 % of the width, counting about 0.6 em per letter.
        size = min(height // 3, int(0.9 * width / (0.6 * max(len(text), 1))))
        tag = f"{{\\pos({width // 2},{height // 2})\\fs{size}\\blur1}}"
        lines.append(f"Dialogue: 0,{ass_stamp(w['start'])},{ass_stamp(end)},Word,,0,0,0,,{tag}{text}")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("clip")
    p.add_argument("--format", choices=["words", "text", "json", "srt", "ass"], default="words")
    p.add_argument("--language", help="Language code (default: detected)")
    p.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    args = p.parse_args()

    text, words = transcribe(args.clip, args.language, pick_device(args.device))
    if args.format == "words":
        print("\n".join(f"{w['start']:6.2f} {w['end']:6.2f} {w['word']}" for w in words))
    elif args.format == "text":
        print(text)
    elif args.format == "json":
        print(json.dumps({"text": text, "words": words}, ensure_ascii=False, indent=1))
    elif args.format == "ass":
        print(ass(words, *read_size(args.clip)))
    else:
        for n, c in enumerate(cues(words), 1):
            print(f"{n}\n{stamp(c[0]['start'])} --> {stamp(c[-1]['end'])}\n{' '.join(w['word'] for w in c)}\n")


if __name__ == "__main__":
    main()
