# Task: burn captions on a swap render

**Goal:** the words she sings or says, burned on the finished video in time with her mouth: plain subtitles, or one big word at a time like a lyric video. Tools: `scripts/transcribe.py` + ffmpeg. No ComfyUI, no prompt.

## When
On a yes to the captions question of `video-swap.md` (After the render: the source had captions or lyric text that the render lost), or when the user asks. Ask which style when the request doesn't say: plain subtitles at the bottom, or word by word in the centre.

## Inputs
- `$VIDEO`: the finished video, relit if it was (`video-relight.md`). Captions go last, so the text stays white.
- The words with their times. `transcribe.py` writes them from `$VIDEO` (its sound is the clip's, and its frame size sets the text's frame); you correct them by ear and against her mouth, as in `speech-transcribe.md`.

## Run
```bash
PY=/abs/path/cv-tools/.venv/bin/python    # any python with transformers + torch
SKILL=/abs/path/media-generation          # this skill folder on that machine
OUT=/abs/path/work/clip1                  # the swap's work folder
VIDEO="$OUT/relight-0.5.mp4"              # the finished video
```

**Plain subtitles**: white, a thin black outline, near the bottom.
1. Write the cues, then fix their words and times in the file:
   ```bash
   "$PY" "$SKILL/scripts/transcribe.py" "$VIDEO" --language en --format srt > "$OUT/captions.srt"
   ```
2. Burn. Sizes count in a 288-line frame whatever the video's size: `Fontsize=16` is about 1/18 of the height, `MarginV=30` about a tenth of it up from the bottom.
   ```bash
   ffmpeg -nostdin -y -i "$VIDEO" -vf "subtitles=$OUT/captions.srt:force_style='FontName=Nimbus Sans,Fontsize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=1,Shadow=0,MarginV=30'" -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a copy "$OUT/captioned.mp4"
   ```

**Word by word**, like a lyric video: one big white word at a time in the centre, bold narrow sans, soft shadow.
1. Write one `Dialogue` line per word, each shown from its start to the next word's start, sized to the frame; then fix the words and times in the file:
   ```bash
   "$PY" "$SKILL/scripts/transcribe.py" "$VIDEO" --language en --format ass > "$OUT/words.ass"
   ```
2. Burn:
   ```bash
   ffmpeg -nostdin -y -i "$VIDEO" -vf "ass=$OUT/words.ass" -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a copy "$OUT/captioned.mp4"
   ```
- Optional, by hand: a long held word swells in the middle with per-letter sizes, e.g. `{\fs190}h{\fs256}o{\fs256}l{\fs190}d`.

## Check
Play it with the sound, and look at a frame at 3–4 word starts:
- the words are the ones she sings or says;
- each word appears when her mouth starts it; a word held over a long break ends where the break starts;
- centred, readable, not stretched;
- nothing covers her face for long. If it does, move the text: word by word, a lower `\pos` for every line (`sed -i 's/\\pos(\([0-9]*\),[0-9]*)/\\pos(\1,<y>)/' "$OUT/words.ass"`); plain, a bigger `MarginV`.

## Lessons
- 2026-11-23 · A 2-shot night car singing clip lost its burned-in lyrics in the redraw; they went back on word by word, after the per-shot relight. Open (1 clip).
