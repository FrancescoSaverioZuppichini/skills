# Task: build a character sheet

**Goal:** two pictures of one character, the inputs every swap uses:
- `<name>.png`: the sheet, three columns side by side (front body, back body, big face);
- `<name>-face.png`: the big face alone.

Model: `models/qwen-image-edit.md`. Workflows: `qwen-character-sheet-build`, then `seedvr2-upsample`. Tools: cv-tools `sapiens2.pose` + a few lines of Python. No phone finish: a sheet is a reference, never a post.

## Ask if unsure
- Whose face (the identity picture)?
- Body, breast and clothes references?
- A new outfit? Dress the sheet afterwards with `image-outfit-swap`.

## Run
```bash
CV=/abs/path/cv-tools
NAME=soi
OUT=/abs/path/work/$NAME-sheet; mkdir -p "$OUT"
```
1. **Render the sheet** (Qwen, 1664×1248, face refine on). Inputs:
   - `Image 1 · the face (identity)`;
   - `Image 2 · body reference (glutes / hips)`, `Image 3 · breast reference`, `Image 4 · clothes reference`;
   - `Reference face (who the face should be)` for the face refine.

   **You write nothing.** `Sheet prompt (v2 · three columns · names Images 1-4)` is fixed: three columns, the pictures named in order.
   ```bash
   $RUN qwen-character-sheet-build --set "Image 1 · the face (identity).image=@face.png" --set "Reference face (who the face should be).image=@face.png"
   ```
   It comes out as three columns split by thin white gaps: the body from the front, the body from the back, and a column whose top half is a face close-up.
2. **Upscale it ×2** (SeedVR2):
   ```bash
   $RUN seedvr2-upsample --set "Image to upscale.image=@<qwen render>"
   ```
   Copy the PNG (`<ComfyUI>/output/seedvr2-upsample/out_*.png`) to `$OUT/sheet.png`. Never use the iPhone JPEG the workflow also saves.
3. **The columns.** In Python (numpy + PIL), on `sheet.png` in grey:
   - background = the median of the leftmost 1/200 of the width (always floor and wall); white = (background + 255) / 2;
   - a gap = a run of x where the 5th percentile of that pixel column is above white, not touching either edge. Two gaps give front = 0..gap 1, back = between the gaps, face column = after gap 2;
   - face panel = the face column from the top down to its first row gap (the same test on rows). No gap found: its top half.
4. **The pose** on each body column and on the face panel (`--box X Y WIDTH HEIGHT` in sheet pixels):
   ```bash
   (cd "$CV" && .venv/bin/python -m cv_tools.sapiens2.pose --input "$OUT/sheet.png" --box <x0> 0 <column width> <sheet height> --output "$OUT/pose-front")
   ```
   Same for `pose-back` and `pose-face`. Each run writes `landmarks.jsonl` with the points in sheet pixels. Read them by name, keeping a point only at score 0.3 or more:
   ```python
   names = {int(k): p["name"] for k, p in json.load(open(f"{CV}/cv_tools/sapiens2/keypoints.json"))["points"].items()}
   r = json.loads(open(f"{OUT}/pose-front/landmarks.jsonl").readline())
   pts = {names[i]: xy for i, xy, s in zip(r["keypoint_ids"], r["keypoints"], r["scores"]) if s is not None and s >= 0.3}
   ```
5. **The cuts.** Both bodies get the same two rows, so front and back keep one scale.
   - Top = `tip_of_chin` + 0.1 × (shoulders − chin) on the front view; shoulders = the mean y of `left_shoulder` and `right_shoulder`. The head goes; the neck and shoulders stay. Stop if the top row reaches the back view's shoulders.
   - Bottom = the lowest foot point of both views (`ankle`, `big_toe`, `small_toe`, `heel`, left and right) + 0.03 × (lowest − shoulders).
   - The big face, on the face panel: brows = the highest `eyebrow` point, span = chin − brows. The box runs from brows − 0.75 × span to chin + 0.12 × span, is grown ×1.12 around its centre and is 0.8 × its height wide. Centre it between `left_eye` and `right_eye`, and shrink it evenly if it would leave the panel.
6. **Proof.** Draw the points (green) and the two rows plus the face box (red) on the sheet, save it at 2400 px max, and show it on the page before going on.
7. **The big face, upscaled.** Crop the face box and run `seedvr2-upsample` on it again until it is at least as tall as the bodies (bottom − top), 3 passes at most. Save it as `$OUT/$NAME-face.png`.
8. **Assemble.** Front | back | big face: the bodies cropped at their native pixels, the big face resized (lanczos) down to the body height, and white gaps of 1 % of that height. Save it as `$OUT/$NAME.png`.

## Check
- **Three columns, one person, the same face** as Image 1.
- **The proof:** shoulders whole on front and back, toes in, the face centred in its box with no empty space.
- `$NAME.png` is front | back | big face, all the same height; `$NAME-face.png` is the big face alone.

## Lessons
- 2026-11-21 · Build the layout in code, never by prompting Qwen for panels: prompts gave wrong panel counts and crops, and a drawn template at denoise 0.88 stayed grey. Strong.
- 2026-11-21 · Always re-run from the Qwen render; never edit the last sheet image. The v7 framing is accepted. Strong.
