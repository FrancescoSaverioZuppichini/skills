# Task: colour match a swap to its source (optional)

**Goal:** the swap render gets the source clip's colour grade back (a night tint, a warm filter) that H3 drops. The person stays as she is: the curves are fitted on the background only. Tool: cv-tools `color_match` + ffmpeg. No ComfyUI, no prompt.

## When
Optional, never run unasked. After a video swap, measure (about 1 s). When the largest shift on any channel is **25 levels or more**, ask the user: "The render's colour is far from the source (largest shift r X, g Y, b Z levels). Match it to the source's grade?" Below 25, say nothing. Never apply it without a yes.

## Ask if unsure
- One fit for the whole clip, or one per shot? One per shot when the shots were rendered on their own or have different grades.

## Inputs
- The source part that was rendered (`$CLIP` or one shot's cut), and the render.
- The person masks of that same part: `masks.npz` in the guide folder that the guide step wrote.
- The seconds to sample: leave out dissolves and fades.

## Run
```bash
CV=/abs/path/cv-tools
F=$(cd "$CV" && .venv/bin/python -m cv_tools.color_match --source "$CLIP" --render "$RENDER" --masks "$OUT/guide-1/masks.npz" --end <SECONDS>)
ffmpeg -nostdin -y -i "$RENDER" -vf "$F" -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a copy "$OUT/matched.mp4"
```
- stderr prints the largest shift per channel: that is the number to measure with (run it, read the line, apply nothing).
- Shots rendered on their own: one fit per shot from its own guide's masks, each applied before the shots are joined.
- Words or captions burned on top go after the match, so they stay white.

## Check
- On the page: source | render | matched frames side by side, 2–3 moments per shot. The background tint, the lights and her skin read like the source's.
- Saturation can stay a little below the source's: per-channel curves barely move it.

## Lessons
- 2026-11-23 · a night car clip with a green-yellow grade: H3 rendered neutral colour, largest shift 37–38 levels; the background-only match brought the grade back (approved). A face swap whose colour was fine measured 12–17. The 25-level line rests on these 2 clips. Open.
- 2026-11-23 · Pinning the curve ends at the 0.5 % / 99.5 % levels instead of the darkest and brightest pixel was less stable: up to 38 levels apart between two disjoint frame sets, against 8. Keep the full-range fit. Medium.
