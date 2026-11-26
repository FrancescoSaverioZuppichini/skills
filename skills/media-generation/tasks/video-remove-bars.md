# Task: take the black bars out of a clip

**Goal:** a clip with black bars (letterbox, pillarbox, a picture inside the picture) fills its frame again, shot by shot, at the same size and with its sound. Tools: cv-tools `shots` + ffmpeg. No ComfyUI.

## When
Only when the user asks. Before cropping, show one frame per shot with the crop drawn on it and ask: a narrow picture in a wide frame needs a big zoom (the car clip's upright strip: 2.4×, which cut her head and knees).

## Run
```bash
CV=/abs/path/cv-tools
CLIP=/abs/path/clip.mp4
OUT=/abs/path/work/clip1/bars; mkdir -p "$OUT"
```
1. **Shots.** `(cd "$CV" && .venv/bin/python -m cv_tools.shots --input "$CLIP" --output "$OUT/shots")`, then look at the strips in `$OUT/shots/`. A dissolve into or out of bars is not a hard cut, so `shots.json` misses it: split that shot by hand at the middle of the dissolve. The car clip has 1 hard-cut shot but 4 real ones (dissolves at 4.0, 8.0 and 11.9 s).
2. **The picture in each shot** (`a`..`b` in seconds):
   ```bash
   ffmpeg -nostdin -ss <a> -to <b> -i "$CLIP" -vf cropdetect=limit=24:round=2:reset=0 -f null - 2>&1 | grep -o "crop=[0-9:]*" | tail -1
   ```
   It prints `crop=w:h:x:y`, the lit box over the whole shot (car shot 3: `crop=404:720:278:0`).
   - The frame's own size means no bars in that shot.
   - A box only a few pixels short of the frame on a dark shot is dark picture, not bars (car shot 2: `920:720:20:0`). Check the strip and keep the full frame.
3. **The crop.** It's the largest box with the frame's shape inside the picture, placed on her head.
   - For a frame `FW×FH` and a picture `w×h` at `x,y`: if `w/h > FW/FH` the box is `h` tall and `h·FW/FH` wide; otherwise it's `w` wide and `w·FH/FW` tall. Use even numbers.
   - Slide the box inside the picture until her head is in it; look at the shot's strip to place it.
   - Car shot 3: `404:304:278:<y>`.
4. **Each shot, cropped and scaled back.** A shot without bars drops the `crop`/`scale` filter:
   ```bash
   ffmpeg -nostdin -y -ss <a> -to <b> -i "$CLIP" -vf "crop=<bw>:<bh>:<bx>:<by>,scale=<FW>:<FH>:flags=lanczos,setsar=1" -an -c:v libx264 -crf 12 -pix_fmt yuv420p "$OUT/part-<k>.mp4"
   ```
5. **Join, with the clip's sound:**
   ```bash
   ls "$OUT"/part-*.mp4 | sort -V | sed "s|.*|file '&'|" > "$OUT/parts.txt"
   ffmpeg -nostdin -y -f concat -safe 0 -i "$OUT/parts.txt" -i "$CLIP" -map 0:v -map "1:a?" -c:v copy -c:a copy -shortest "$OUT/nobars.mp4"
   ```

## Check
- Every shot fills the frame with no black edge left, and her head is inside the crop in every shot.
- Same length as the clip, and her mouth on the sound.
