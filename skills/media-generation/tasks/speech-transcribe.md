# Task: transcribe speech or singing, with word times

**Goal:** what is said or sung in a clip, each word with its start and end: for the `<d>` lines of a video swap prompt, for captions, or as a plain transcript. Tool: `scripts/transcribe.py` (Whisper large-v3 turbo). No ComfyUI, no prompt.

## Ask if unsure
- Which output? `words` (default: one line per word, what the swap prompts read), `text`, `json`, `srt` (captions).
- The language, when you know it (`--language en`): left out, Whisper detects it, and a song can be detected as another language.

## Run
```bash
PY=/abs/path/cv-tools/.venv/bin/python     # any python with transformers + torch
"$PY" "$SKILL/scripts/transcribe.py" "$CLIP" --language en > "$OUT/words.txt"              # start end word
"$PY" "$SKILL/scripts/transcribe.py" "$CLIP" --language en --format srt > "$OUT/captions.srt"
```
- `--device auto` (default): the GPU in bf16 when 6 GB are free, else the CPU: the same words, but 10–30× slower. When ComfyUI holds the GPU and is idle (empty queue), free its memory first instead of falling back: `curl -s -X POST <server>/free -d '{"unload_models":true,"free_memory":true}'`. Never during a render.
- Time for a 15 s clip: 1.8 s on a 3090 in bf16 (plus ~5 s to load), 17–60 s on a CPU (2026-11-24).

## Check
Read the words against the clip, with the sound. Whisper:
- stretches the first word back to 0.00 s when the clip opens on music: its real start comes from her mouth (the face strip) or your ears;
- invents words on music with no voice ("Thank you so much for joining us"): drop them;
- starts each word where the previous one ends, so starts run early after a pause or a held note.

For a swap prompt the face strip wins over these times (`video-character-swap.md`, Her words).

## Lessons
- 2026-11-24 · Whisper turbo, the same words everywhere: fp32 on a CPU 60 s (one box) and 17 s (another) for a 15 s song; bf16 on a 3090 1.8 s, peak 4.5 GiB. Strong.
- 2026-11-24 · Parakeet TDT 0.6B v3 (MLX on a Mac): 1.0 s and a believable first-word start (2.72 s where Whisper says 0.00), but the sung words wrong on both songs ("Rashina, hit a woke" for "Crashing, hit a wall", "Oh minister" for "oh, promise"). Whisper stays. Medium (2 songs).
- Open: Qwen3-ASR-1.7B with Qwen3-ForcedAligner-0.6B claims singing and aligned word times; not tried.
