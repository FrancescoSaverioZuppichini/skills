# Task: character swap in a video

**Goal:** a character (from her character sheet) replaces the whole person in a source clip: face, hair, body and clothes. The motion, expression timing, scene and camera follow the source. No head or face swaps: the person is replaced whole. A face-only swap is a separate task (`tasks/face-swap.md`), run only with the on-screen person's consent.

## Rules for this task, any model
- **Hide the whole source woman** (blur, grey, or regenerate her area). Every run where her clothes stayed visible kept them (11b, 12, 18b); with the raw clip H3 kept her face and only recoloured her hair (base0).
- **Never name what is drawn or hidden on the input.** Describe only the new person and the scene. Every prompt that described the drawn pose guides, even to say "never show them", got them painted onto her face (iterations 0–2, 3 wordings); the same prompt without them was clean 10 of 10 (iteration 3).
- **The motion comes from the video, not the words.** Describe the moves in plain prose, in order, without timestamps. A source with cuts gets one `[Shot N]` per shot and a cut time on each later shot, never inside a shot (multi-shot variant below).
- **The look comes only from her reference.** Name her hair, eyes and build. Never name the source person's clothes, hair or jewellery.
- **Never mention on-screen graphics** (stickers, captions, pop-ups). Asking to keep them got the guides painted too (25 → 26).

## Models
- [MiniMax H3 video (Singularity + Pika)](#minimax-h3-video-singularity--pika)

---

## MiniMax H3 video (Singularity + Pika)
Read `models/minimax-h3.md` (the common H3 format) first. Everything below is specific to this task and overrides it where they differ (this task leaves out dialogue tags, and timestamps everywhere except the cut times of a multi-shot source).

One route: her blurred + the pose drawn on top, full redraw, the prompt never naming the drawing.

**Never use a ControlNet (Fun ControlNet Union or any other), for the pose or for inpainting.** It failed every time (2026-11-14 full redraw: hands at the wrong moments; 2026-11-16 repaint-only: wrong pose).

### Model and settings
- Singularity v1.3 int8 (`Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8.safetensors`) → `MiniMaxChunkFeedForward` → Pika LoRA `pika_h3_flex_ref2va_v1_bf16.safetensors` (rgthree Lora Loader Stack) → sigma shift 12 / 3; sampler `lcm` on Pika's schedule `1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0` (6 steps), CFG 1; 736×1312 (1 MP).
- **No 4-step speed LoRA** (base H3 + ref2v turbo): worse look (2026-11-15).
- `<Picture 1>`: the character sheet only, already dressed in the outfit she should wear. Dress the sheet with an image editor (we use Qwen Image 2.1), never with H3: an H3-dressed sheet drifted the look on the loop renders of 2026-11-14 to 16. A face close-up as `<Picture 2>` added nothing (18f with and without it: identical); an outfit crop added nothing (21 vs 22).
- The original sound of the window, kept.
- Length: 17n + 5 frames at 24 fps (73 = 3 s, 124 = 5.2 s, 201 = 8.4 s). Render 3 s first; long clips drift more (8.4 s: pose good on 2 of 4 seeds).

### Inputs
- `<Video 1>` = `guide.mp4` from `python -m cv_tools.motion_guide` ([cv-tools](https://github.com/FrancescoSaverioZuppichini/cv-tools)) `--input <window.mp4> --output <dir> --mask-grow 0.05`, fed at 368×656 with the window's audio.
  - The woman is heavily blurred inside her SAM 3.1 tracked mask, and the blur reaches 5 % of the frame's long side past the mask (`--mask-grow 0.05`, default 0.01). The wider blur stops the source's hairstyle and accessories coming back through her outline (reel 02 bun + hoop earrings: iteration 3 → 5).
  - The DWPose-style skeleton and eyebrow + mouth dots are drawn on top (motion_guide's default `--face brows_mouth`; eye and nose dots came back as glowing eyes, 26/27 → 28).
- A bigger reference video (576×1024) is slower and lets garment shapes back in (REF59). Keep 368×656.

### Workflow
1. **Cut the window** at 24 fps and 736×1312, with its audio. Run `motion_guide` on exactly that window.
   **Find its shots:** `python -m cv_tools.shots --input window.mp4 --output <dir>` ([cv-tools](https://github.com/FrancescoSaverioZuppichini/cv-tools)). It writes `shots.json` (each shot's start and end frame and its `start` as `MM:SS.mmm`) and one frame strip per shot, `shot-N.png`. Rule inside: a scene score of 0.3 or more starts a new shot; no shot is shorter than 12 frames (0.5 s). **One shot: the template as is, no timestamps. Several: the multi-shot variant, with `{TIME}` = each later shot's `start` from `shots.json`.** A new angle inside the same room scores lower and is untested, so look at the strips when the clip might have one.
2. **Frame strip for the writer:** `shot-N.png` from step 1, frames picked by index (every 6th = 0.25 s at 24 fps, plus each shot's last frame; the frame numbers are in `shots.json` → `strip_frames`), 480 px wide, the smallest size where hands and gaze read. Never fast `-ss` seek: two encodes seek to different moments.
3. **The writer fills the slots** of the template below from the strip, following "Writing the slots". `{OUTFIT}`, `{CHARACTER_LINE}` and `{OUTFIT_LOCK}` are written once per character sheet and then fixed; our test character's:
   - `{OUTFIT}`: `a silver chain-mail halter top that leaves her back bare and a glossy black patent-leather mini skirt`
   - `{CHARACTER_LINE}`: `She is a 21-year-old woman with long straight medium chestnut-brown hair, warm brown eyes, petite and slim.`
   - `{OUTFIT_LOCK}`: `the silver chain-mail halter top covers her chest and the glossy black patent-leather mini skirt covers her hips`
4. **Audit:** `scripts/h3_audit.py <dir>` (exits 1 on any failure), then check the moves against the strip by eye.
5. **After the render:** check her face and both hands at full resolution every 6th frame for painted lines or dots (crop them out at full size, don't judge from the downscaled video), and the pose on a synced side by side with the original. A metric alone is never the verdict.

### Template
`{…}` is filled per clip. Everything else is fixed text, copied word for word.

```
subject_definitions:
<Subject 1> is the young woman of the character sheet <Picture 1>: her face, identity, hair, body shape and the outfit she wears there ({OUTFIT}). {CHARACTER_LINE}
<Subject 2> is the performance of the woman in <Video 1>: her body motion, head turns, hand gestures, expression timing, mouth movement, gaze, position and scale in the frame.
<Subject 3> is the scene of <Video 1>: {SCENE_SHORT}.
<Video 1> is the source video for the target video edit. The woman in it is hidden under a heavy blur. The blur only carries her motion and expression; it is not part of any picture, and it never appears in the target video.

summary:
[video editing + audio reuse] The target video is an edited version of <Video 1>. <Subject 1> takes the place of the woman in <Video 1> and performs <Subject 2> in <Subject 3>, with the original sound. Her clothes and jewellery in <Video 1> are replaced by the outfit of <Subject 1>. The blur on <Video 1> is not part of the target video.

retention_analysis:
<Video 1> (shot length and original sound): partially_preserved - the shot length and the sound remain; the woman and the blur are not kept.
<Subject 2> (throughout [Shot 1]): attribute_transfer - only her movement, gestures, expression timing, mouth movement, gaze, position and scale transfer to <Subject 1>.
<Subject 3> (throughout [Shot 1]): fully_preserved - {KEPT}.
<Subject 1> (throughout [Shot 1]): attribute_transfer - her face, hair, body and outfit come from <Picture 1>, not from <Video 1>; her skin tone is hers, never the colour of the blur.

detailed_description:
{STYLE} [Shot 1] <Subject 1> performs the motion and expressions of <Subject 2> as shown in <Video 1>, frame by frame, in <Subject 3>: {SCENE}. {FRAMING} She wears the outfit of <Subject 1> in every frame: {OUTFIT_LOCK}. {MOVES} {CAMERA} Her face is sharp, natural and fully visible in every frame, lit by {LIGHT}, with real skin texture. The picture is clean, with no blur anywhere. One continuous shot with no cuts.

overall_soundscape:
The original sound of <Video 1>: {SOUND}.

non_diegetic_music:
N/A
```

**No-sound variant** (the only allowed changes): the summary prefix becomes `[video editing]`; ", with the original sound" is dropped; the `<Video 1>` retention line becomes "(shot length): partially_preserved - the shot length remains; the woman and the blur are not kept."; write a new `overall_soundscape`.

**Multi-shot variant** (the source has cuts; the only allowed changes, applied by `scripts/h3_audit.py`'s `template()`):
- every `(throughout [Shot 1])` lists all the shots: `(throughout [Shot 1], [Shot 2])`;
- each later shot is one block right after shot 1's `{CAMERA}`, in order, with its own `{SCENE}`, `{FRAMING}`, `{MOVES}` and `{CAMERA}`:
- Later shot: `[Shot {N}] At {TIME}, the shot cuts to <Subject 1> in <Subject 3>: {SCENE}. {FRAMING} She wears the outfit of <Subject 1> in every frame: {OUTFIT_LOCK}. {MOVES} {CAMERA}`
- Closing sentence: `One continuous shot with no cuts.` becomes `It cuts only where <Video 1> cuts.`
- `{TIME}` is the cut: the first frame of the shot ÷ fps, as `MM:SS.mmm` (frame 36 at 24 fps = `00:01.500`). `{MOVES}` of each shot covers only that shot, in prose, with no timestamp. `{SCENE_SHORT}` and `{KEPT}` name the places of every shot.

**Evidence:** iteration 3 (this template) and 5 (+ `--mask-grow 0.05`): 10 of 10 clean each, pose followed, on bridge, video 2, reel 01, reel 02, reel 03 at seeds 1001 / 2002 (the seeds that painted before), full-resolution audit. Prompt length 540–670 words.

### Shots and timestamps: the official format, the community, and ours
**Official (MiniMax full-reference guide §5.1, verbatim):** "`[Shot 1]` marks the opening shot and has no timestamp. Later shots use `[Shot N] At MM:SS.mmm, ...` to mark cut times."

Official examples, short verbatim quotes (MiniMax's full-reference guide, linked in `references/README.md`: §5.2 and its worked example; the third is from MiniMax's H3-Context-IR API docs):
```
The target video is in a cinematic, literary music-video style with soft lighting and a slightly desaturated color palette.
[Shot 1] The scene opens in a crowded urban street...
[Shot 2] At 00:09.000, the shot cuts to an extreme close-up...
```
```
<Subject 1> (appears in [Shot 1], [Shot 2], [Shot 3]): fully_preserved - the exposed brick wall, orange tufted sofa, patterned pillows, neon sign, and wooden coffee table are retained.
[Shot 1] A medium shot establishes <Subject 1>, the coffee shop with its exposed brick wall, orange tufted sofa, patterned pillows, neon sign, and wooden coffee table. …
[Shot 2] At 00:03.000, the shot cuts to a close-up of <Subject 4> (S2), the young man in the dark-grey hoodie from Shot 1, sitting beside <Subject 3> on the sofa and holding <Subject 2> securely in his arms. …
[Shot 3] At 00:05.000, the shot cuts to a close-up of <Subject 3> (S1), the blonde woman in the light-pink shirt from Shot 1. …
```
```
[Shot 2] At 00:02.800, the camera cuts to a medium close-up of the captain from Shot 1 in profile facing right
```

**Community (2026-11-22):** nobody puts a timestamp on a single shot; multi-shot use varies.
- [HF discussion 47](https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/47): three single-shot prompts, each opening `[Shot 1] Live-action, …`, no timestamp; later shots as `[Shot 2] At 00:03, the camera cuts to…`.
- [HF discussion 71](https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/71) (ref2va): retention lines `(appears in [Shot 1], [Shot 2], [Shot 3])`, shot blocks without timestamps.
- [ComfyUI Fantastic H3 Prompt Builder](https://github.com/Adudeguyman/ComfyUI-Fantastic-MiniMaxH3-PromptBuilder): its shot button inserts `[Shot N] At MM:SS.mmm, the shot cuts to `; it warns when `[Shot 1]` carries a timestamp, when cut times don't increase, or when they pass the clip length.
- [awesome-minimax-h3-prompts](https://github.com/ecomimagelab/awesome-minimax-h3-prompts): one-line single shots, no timestamps; multi-shot prompts split by `CUT TO:` with no times; one single take timed as `TIMELINE 0.0–3.0s`.
- [Civitai article 34646](https://civarchive.com/articles/34646/minimax-h3-prompt-guide-structure-5-copy-ready-t2v-i2v-ref2v-prompts): its video-edit prompt has no timestamps ("Use Video 1 for all subject motion, timing and camera behavior."); its generation prompts use `[0–3 seconds]` ranges.
- [ComfyUI's H3 prompt guide](https://docs.comfy.org/tutorials/video/minimax/minimax-h3-prompt-guide): one timestamp per cut (`At 00:05.000`), never a range; cut times increase and stay inside the clip length.

**Ours:** one shot = no timestamp (the edit source carries the timing); several shots = the official `[Shot N] At MM:SS.mmm,` at each detected cut, moves still in prose. We write both with a ComfyUI node: ffmpeg scene score for the cuts, a vision LLM for the slots, `scripts/h3_audit.py`'s `template()` to fill and `audit()` to check. Example: its prompt for the 2-shot test clip (jeans 0–1.5 s + video 2 0–1.5 s), detailed_description:
```
Realistic phone footage in a lit parking garage, filmed as a selfie at arm's length, then in a bright room from a phone standing still; she holds nothing. [Shot 1] <Subject 1> performs the motion and expressions of <Subject 2> as shown in <Video 1>, frame by frame, in <Subject 3>: a gray parking garage with concrete flooring, white parking markings, exposed overhead pipes and a gray utility panel. She is framed from her head to her hips with one arm extending toward the lens, with the whole picture turned sideways so the floor runs along the right side of the frame. She wears the outfit of <Subject 1> in every frame: the silver chain-mail halter top covers her chest and the glossy black patent-leather mini skirt covers her hips. She extends one arm toward the camera and initially looks away with her face in profile. She turns her head toward the lens as her upper body becomes more front-facing. She keeps looking into the lens, moving her mouth and changing from parted lips to a slight smile. The arm's-length selfie camera swings and tilts briefly before settling into a closer frontal view, matching the framing and speed of <Video 1> throughout. [Shot 2] At 00:01.500, the shot cuts to <Subject 1> in <Subject 3>: a white room with a patterned rug, pale wooden flooring, a frosted-glass sliding door on a black rail, open shelving and an open doorway. She is framed from head to feet near the center, with the rug below her and ample space above her head. She wears the outfit of <Subject 1> in every frame: the silver chain-mail halter top covers her chest and the glossy black patent-leather mini skirt covers her hips. Facing the camera, she lifts both arms outward and smiles with her mouth open. She makes small bouncing steps and shifts her weight with her arms spread. She then angles her torso and turns her head toward the right side of the frame, smiling as one arm stays extended and her other arm draws slightly back. The camera stays still in a wide full-body view, matching the framing and speed of <Video 1> throughout. Her face is sharp, natural and fully visible in every frame, lit by the same overhead garage light and soft indoor daylight as the respective scenes, with real skin texture. The picture is clean, with no blur anywhere. It cuts only where <Video 1> cuts.
```

### Writing the slots (any clip)
These hold for any clip. A rule that only fits one clip does not go here.
- **`{SCENE_SHORT}`** (in `<Subject 3>`, one short phrase): the place, its light and the framing. "the bridge at night, its lights, the city behind it and the close handheld framing".
- **`{KEPT}`**: what of the scene stays, ending "as `<Video 1>`". "the same location, lights, camera path and night light as <Video 1>".
- **`{STYLE}`**: one sentence: "Realistic phone footage <where, light>, filmed <by another person holding the phone / from a phone standing still / as a selfie at arm's length>; she holds nothing." or "…; she holds <the object> in one hand."
- **`{SCENE}`**: the place and its 3–5 main objects, one phrase, no people.
- **`{FRAMING}`**: one sentence, "She is framed <from where to where>…". If the whole picture is turned sideways (the floor runs along a side of the frame, as in a phone clip filmed rotated), say so: "with the whole picture turned sideways so the floor runs along the right side of the frame" (jeans W2).
- **`{MOVES}`**: **4–6 sentences of plain prose, in order, no timestamps.** Say what she does with its verb ("she spits onto the tip of the nozzle", "covers her mouth and laughs"), not only where her hands are; the reel 03 spit and the video 2 hand-to-mouth both came out (iteration 3). Say which way her body faces (front to the camera, side, back) and write a turn only if the raw frames show one: a false turn line turned her in the render on 3 of 5 seeds, the truthful "keeps her front to the camera the whole time and never turns" on 0 of 5 (jeans, fallback table). The video carries the timing: every passing prompt (16, 18f, iterations 3 and 5) used prose; 0.125 s timestamped beats were never validated.
- **`{CAMERA}`**: one sentence ending "…matching the framing and speed of <Video 1> throughout." Still, handheld drift, or following, as the strip shows.
- **`{LIGHT}`**: "the same <light> as the <scene>".
- **`{SOUND}`**: what is heard (her singing, her voice, the ambience). Speech is never transcribed: no `<d>` dialogue tags.
- **Hands:** "one hand" / "her other hand"; directions are frame directions ("to the right side of the frame").
- **Objects she holds** stay in the picture (outside her mask): name them in `{STYLE}` and in the moves (reel 03 nozzle: kept and used in every render).
- **Phones:** never name a phone in her hand, or the model paints one. For a selfie, say "filmed as a selfie at arm's length"; her outstretched arm may be described, the phone never.
- **Never name** the drawing, the skeleton, dots, lines or guides; the source woman's clothes, hair or jewellery; any sticker or caption. The audit rejects these words.

### Checklist (all must pass before rendering)
| # | Rule | From |
|---|---|---|
| 1 | No sticker, caption, overlay or on-screen text is kept, described or quoted | 25 → 26 |
| 2 | Nothing drawn is named anywhere (skeleton, dots, lines, guides, keypoints) | iterations 0–2 → 3 |
| 3 | The `<Video 1>` definition says she is hidden under a heavy blur that never appears | iteration 3 |
| 4 | The `<Video 1>` retention line is partially_preserved, with the woman and the blur not kept | 18d → 18f |
| 5 | The summary says the blur is not part of the target video | 18f |
| 6 | "The picture is clean, with no blur anywhere." just before "One continuous shot with no cuts." | iteration 3 |
| 7 | The skin-tone line is present | 18f (guard, never tested alone) |
| 8 | No source garment, hair or jewellery is named | rule; checked by word list + eye |
| 9 | Pictures cited inside `<Subject 1>` only, no standalone `<Picture N>` lines | 18e → 18f |
| 10 | The source woman is never fully_preserved; her performance is attribute_transfer | 17 |
| 11 | Moves in prose, no timestamps. One shot: no timestamp anywhere. Several shots: `[Shot 1]` bare, each later `[Shot N] At MM:SS.mmm,` at its detected cut, times increasing | 16, 18f, iterations 3 + 5; official guide §5.1 |
| 12 | Scene and moves match the strip: nothing invented, right order | official guide |
| 13 | Fixed text copied word for word | iteration 3 |
| 14 | The outfit sentence ("She wears the outfit of `<Subject 1>` in every frame: …") sits in the shot, after the framing | jeans A → B (2026-11-19) |

### Fallbacks: symptom → what to try
Evidence: **strong** = failed and fixed on several runs or clips. **Medium** = one before/after pair. **Open** = no fix yet.

| Symptom | Likely cause | What fixed it | Evidence |
|---|---|---|---|
| White face dots or skeleton painted onto her | the prompt names the drawing | remove every mention (this template) | **strong**: iterations 0–2 painted on video 2 → iteration 3 clean 10 of 10 |
| Source hairstyle or accessories come back (bun, hoops) | the blurred outline keeps their shape | `motion_guide --mask-grow 0.05` | **medium**: reel 02, iteration 3 → 5, 2 of 2 seeds. A hair sentence did nothing (iteration 4) |
| Glowing white eyes / white spot on the nose | dense eye and nose dots drawn | eyebrow + mouth dots only (motion_guide default) | **medium**: 26/27 → 28 |
| Old clothes kept; only face and hair swapped | her clothes visible in `<Video 1>` | hide the whole woman | **strong**: 11b, 12, 18b → 16, 18c+ |
| A masked clothes area becomes a plain top | a flat masked region read as a garment | mask the whole woman, not only the clothes | **strong**: M1, 14, 15a, 15b → 16, M5 |
| Framing jumps closer mid-clip | person-mask dropouts | SAM 3.1 tracked mask (motion_guide) | **medium**: 27 → 28 |
| **Nude** from the first frame, outfit lost | a small dark garment, bare arms and waist blur into one skin-coloured shape; the outfit was named only in `<Subject 1>`, never in the shot | the outfit sentence in the shot (template, checklist 14) | **strong**: jeans reel A → B, nude 2/2 → dressed on every later render (2 seeds, 7 prompts); no change on bridge or reel 01 (2026-11-19) |
| Body turns front → side → back where the source keeps her front | **a false move line**: the prompt said "turns half away, and the camera swings down to her bare back", while the raw clip faces the camera throughout (the move had been written from the blurred guide) | write the moves from the **raw clip's frames**: W2 ("keeps her front to the camera the whole time and never turns") | **strong**: 3 s jeans, 5 seeds, a per-frame front/back check (SigLIP zero-shot on the person crop): old prompt baseline back on 3/5, the 0.5 MP-draft pipeline back on 4/5 → W2 0/5 for both; one wide-framing miss per arm remains. An earlier "W2 did not fix it" note was a longer clip judged by eye (2026-11-22) |
| Soft face | a false move line also softens the face (old prompt vs W2, same seeds: baseline sharpness +3 % to +83 % on 5 of 5 seeds); small faces are few tokens | first check the moves against the raw clip. Avoid crops, face passes and paste-backs: work on the full frame. Resolution route: 0.5 MP draft → H3 learned latent upscaler ×2 → 2 Pika steps at 2.1 MP from noise 0.45 | **medium**: jeans 5 seeds (prompt effect); the 2.1 MP route's gain on a truthful prompt is median +6 % on jeans, under test on far faces (2026-11-22) |
| The render ignores a cut or puts it elsewhere; identity changes across the cut | a multi-shot source | the cut comes from `<Video 1>`: with the guide cut at the same frame, the prose-only prompt cut at frame 36 and the tagged multi-shot prompt at 35 (real cut 36); both kept her identity. Use the multi-shot variant for format (a cut source must never say "one continuous shot"), not as a lever; build the guide per shot | **medium**: 2-shot test clip, 1 seed (2026-11-22). The tagged prompt held the sideways framing to the cut, the prose one swung the camera: 1 seed, open |
| Stickers and captions gone | the full redraw drops them | **open**, accepted for now | every render |
| Short hair (bob) after the wider blur | the rounder blurred head reads as short hair | **open** | reel 02, iteration 5 |
| Pose drifts on long clips | — | **open**; try another seed | 8.4 s reel 01: 2 of 4 seeds |
| Studded wristband, barefoot | sheet details / the sheet has no shoes | **open** | iterations 3, 5 |

### Failed → fixed examples (real prompts)
**1. Face dots painted (iteration 0 → 3).** Same input, sheet, seeds; only these sentences changed.
- ❌ iteration 0: "The woman in it is hidden under a heavy blur and carries drawn guides: coloured pose-skeleton lines and dots on her body and hands, and small white dots on her face for her eyebrows and mouth. The blur and the guides only carry her motion and expression; they are not part of any picture, and they never appear in the target video." … "The blur, the skeleton lines and the dots drawn on <Video 1> are not part of the target video." … "the woman, the blur, the skeleton lines and the dots are not kept." … "The picture is clean: no blur, no lines, no dots and no skeleton anywhere." → white blobs over her eyes and mouth in every frame.
- ✅ iteration 3: the template above (the drawing never named) → clean on all 10.

**2. Source hairstyle (iteration 3 → 5).** Same prompt; the input's blur grown from 1 % to 5 % → bun and hoop earrings gone.

### What failed (do not retry without a new reason)
- **Any ControlNet** (never again). Pose through Fun ControlNet Union 2.0 with nothing drawn, full redraw: hands at the wrong moments and a harsher look (bridge 1–7 s side by side, 2026-11-14); stopping it at 60 % of the steps changed nothing. Earlier "8 of 8" verdicts were still frames only.
- **Describing the drawn guides in the prompt** in any wording: painted (iterations 0–2).
- **Drawing the guides at 70 % / 40 % opacity:** painted, just paler (30, 30b).
- **Pasting stickers back after the render:** visible patches around her (2026-11-15).
- **Repainting only the person** (original video as the start latent + a denoise mask, pose through the ControlNet's inpaint mode): wrong pose and hand signs (bridge 5 s, 2 seeds, 2026-11-16).
- **Timestamped beats every 0.125 s, prompts up to 850 words:** never validated; dropped.

