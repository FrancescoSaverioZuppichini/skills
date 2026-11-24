# Task: relight a swap render to its source

**Goal:** the render gets back the source clip's light (a night tint, a warm filter) that H3 drops. Tool: cv-tools `color_match` (per-channel curves fitted on what the render shares with the source) + ffmpeg. No ComfyUI, no prompt.

## When
On a yes to the light question of `video-swap.md` (After the render): it measures the render and asks only when the largest shift is 25 levels or more on any channel. Never relight without a yes.

## Inputs
From the swap's work folder `$OUT`: `shots.txt`, and for each shot `shot-<k>.mp4` and its guide's `guide-<k>/masks.npz`. The guide step already made the masks the mode needs:
- **Character swap:** the person mask. The curves are fitted on the background; she stays as she is.
- **Face swap:** the head + hair mask. The curves are fitted on everything she shares with the source (body, clothes, scene) and applied to the whole frame, face included. Never fit on the head: a different woman's hair and skin would be copied onto hers.

`$RENDER` is the render as H3 made it: the joined render when shots were rendered on their own, still upright when the clip was turned upright.

## Run
One fit per shot, from that shot's masks, applied to that shot before the shots are joined. A one-shot clip runs the same steps.
```bash
CV=/abs/path/cv-tools          # cv-tools checkout (has .venv)
OUT=/abs/path/work/clip1       # the swap's work folder
RENDER=/abs/path/render.mp4
```
1. Cut the render into its shots. Each gets a line `k start end` in `samples.txt`: the seconds of the shot to sample, from its cut.
   ```bash
   while read -r k a b; do
     ffmpeg -nostdin -v error -y -ss "$a" -to "$b" -i "$RENDER" -an -c:v libx264 -crf 12 -pix_fmt yuv420p "$OUT/render-$k.mp4"
     echo "$k 0 $(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$OUT/render-$k.mp4")"
   done < "$OUT/shots.txt" > "$OUT/samples.txt"
   ```
2. Edit `samples.txt` so no line samples a dissolve or a fade: a shot that opens on a 0.6 s dissolve and fades out at 7 s becomes `2 0.6 7.0`.
3. Relight at full (`--strength 1`) and half (`--strength 0.5`) strength; the user picks.
   ```bash
   for S in 1 0.5; do
     : > "$OUT/relit.txt"
     while read -r k s e; do
       F=$(cd "$CV" && .venv/bin/python -m cv_tools.color_match --source "$OUT/shot-$k.mp4" --render "$OUT/render-$k.mp4" --masks "$OUT/guide-$k/masks.npz" --start "$s" --end "$e" --strength "$S")
       ffmpeg -nostdin -v error -y -i "$OUT/render-$k.mp4" -vf "$F" -c:v libx264 -crf 12 -pix_fmt yuv420p "$OUT/relit-$k.mp4"
       echo "file '$OUT/relit-$k.mp4'" >> "$OUT/relit.txt"
     done < "$OUT/samples.txt"
     ffmpeg -nostdin -v error -y -f concat -safe 0 -i "$OUT/relit.txt" -i "$RENDER" -map 0:v -map "1:a?" -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a copy "$OUT/relight-$S.mp4"
   done
   ```
4. Clip turned upright: turn both results back (`video-swap.md`, After the render).

## Check
- Source | render | relight-1 | relight-0.5 side by side, 2–3 moments per shot: the scene's tint and lights read like the source's, and her skin stays natural (face swap: her face sits in the same light as her body).
- No colour jump at a cut that the source doesn't have.
- Saturation can stay a little below the source's: per-channel curves barely move it.

## Lessons
- 2026-11-24 · A night car face swap: curves fitted outside her head and hair fixed the light colour, where brightness-only kept the wrong colour. Medium (1 clip, approved).
- 2026-11-23 · A night car character swap with a green-yellow grade: H3 rendered neutral colour (largest shift 37–38 levels); the background fit brought the grade back. Medium (1 clip, approved).
- 2026-11-23 · A dark night car face swap (largest shift r 40, g 33, b 30): full strength darkened her face red-brown; half kept the night and her face natural ("global half is amazing", the owner). Render both every time. Medium (1 clip).
