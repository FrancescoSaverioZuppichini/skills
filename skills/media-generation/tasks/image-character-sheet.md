# Task: build a character sheet

**Goal:** one clean reference sheet of a character (front body, back body, head), the input every swap uses. Model: `models/qwen-image-edit.md`. Workflows: `qwen-character-sheet-build`, then `seedvr2-upsample`, then the cut.

## Ask if unsure
- Whose face (the identity picture)?
- Body, breast and clothes references?
- A new outfit? Dress the sheet afterwards with `image-outfit-swap`.

## Steps
1. **Render the sheet** (Qwen, 1664×1248, face refine on). Inputs:
   - `Image 1 · the face (identity)`;
   - `Image 2 · body reference (glutes / hips)`, `Image 3 · breast reference`, `Image 4 · clothes reference`;
   - `Reference face (who the face should be)` for the face refine.

   **You write nothing.** `Sheet prompt (v2 · three columns · names Images 1-4)` is fixed: three columns, the pictures named in order.
   ```bash
   $RUN qwen-character-sheet-build --set "Image 1 · the face (identity).image=@face.png" --set "Reference face (who the face should be).image=@face.png"
   ```
2. **Upscale, cut and assemble** in one command, from the cv-tools folder with its venv, inside one GPU slot:
   ```bash
   <sheet build script> <qwen render> <name>   (private: SeedVR2 ×2 + cv_tools.char_sheet + assembly)
   ```
   It runs SeedVR2 ×2 (`seedvr2-upsample` as saved), splits the columns at the white gaps, finds the pose (Sapiens2), cuts the bodies just under the chin and the toes, and frames the head from the face landmarks. The crop step alone is public: `python -m cv_tools.char_sheet --input sheet.png` writes `front.png`, `back.png`, `head.png`, `proof.jpg`.

## Check
- **Three columns, one person, the same face** as Image 1.
- **The cuts in `proof.jpg`:** shoulders whole on front and back, toes in, the head centred with no empty space.

## Lessons
- 2026-11-21 · Build the layout in code, never by prompting Qwen for panels: prompts gave wrong panel counts and crops, and a drawn template at denoise 0.88 stayed grey. Strong.
- 2026-11-21 · Always re-run from the Qwen render; never edit the last sheet image. The v7 framing is accepted. Strong.
