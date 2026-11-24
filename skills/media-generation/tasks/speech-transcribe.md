# Task: transcribe speech or singing, with word times

**Goal:** what is said or sung in a clip, each word with its start and end: for the `<d>` lines of a video swap prompt, for captions, or as a plain transcript. Tool: `scripts/transcribe.py`. No ComfyUI, no prompt.

## Ask if unsure
- Which output? `words` (default: one line per word, what the swap prompts read), `text`, `json`, `srt` (captions), `ass` (one big word at a time; `video-captions.md`).
- The language, when you know it (`--language en`).

## Run
```bash
PY=/abs/path/cv-tools/.venv/bin/python     # any python with transformers + torch
"$PY" "$SKILL/scripts/transcribe.py" "$CLIP" --language en > "$OUT/words.txt"              # start end word
"$PY" "$SKILL/scripts/transcribe.py" "$CLIP" --language en --format srt > "$OUT/captions.srt"
```
It runs on the GPU when 6 GB are free, else on the CPU, much slower. When ComfyUI holds the GPU with an empty queue, free its memory first: `curl -s -X POST <server>/free -d '{"unload_models":true,"free_memory":true}'`. Never during a render.

## Check
Read the words against the clip, with the sound:
- the first word is often stretched back to 0.00 s when the clip opens on music: its real start comes from her mouth (the face strip) or your ears;
- words on music with no voice ("Thank you so much for joining us") are invented: drop them;
- each word starts where the previous one ends, so starts run early after a pause or a held note.

For a swap prompt the face strip wins over these times (`video-swap.md`, Her words).
