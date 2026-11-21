# Task: face-only swap in a video

**Goal:** the character's face and hair (from her sheet) replace the source woman's face and hair. Her body, clothes, jewellery, motion, expression timing, scene and camera stay the source's.

**Only with the consent of the person on screen.** This keeps a real person's body and puts another face on it. The default for every swap is the whole person (`tasks/character-swap.md`).

## Rules for this task, any model
- **Hide only her face and hair; leave her body and clothes visible.** The model keeps what it can see, so her clothes stay. This is the character swap's rule turned around: there, visible clothes always came back (11b, 12, 18b).
- **Never name her clothes, jewellery or hair.** "She stays dressed exactly as in `<Video 1>`" carries the clothes. Not naming them kept them on 6 of 6 renders; naming them was never tested.
- **No outfit sentence.** "She wears the outfit of `<Subject 1>` …" belongs to the character swap; here it would dress her in the sheet's outfit.
- **The character's face and hair only.** Her body shape is not named ("petite and slim" is dropped), because the body stays the source's.
- **Never name what is drawn on the input, and never mention stickers or captions.** Same rule and evidence as the character swap.

## Models
- [MiniMax H3 video (Singularity + Pika)](#minimax-h3-video-singularity--pika)

---

## MiniMax H3 video (Singularity + Pika)
Read `models/minimax-h3.md` first, then the character swap's H3 subsection. Its **Model and settings**, **Workflow** steps 1–2 and **Writing the slots** apply here unchanged unless this section says otherwise.

### What differs from the character swap
| | Character swap | Face only |
|---|---|---|
| Guide mask | the whole woman, `--mask-grow 0.05` | `--mask-prompt "head, hair" --mask-grow 0.02` |
| Visible in `<Video 1>` | nothing of her | her body, skin, clothes and jewellery |
| `<Picture 1>` | the dressed character sheet | the same dressed sheet. The 17 Nov runs used an undressed sheet of the same character; no face-only render with the dressed sheet exists yet |
| `<Subject 1>` | face, identity, hair, body shape, outfit | only her face, identity and hair |
| `<Subject 2>` | her performance only | the woman herself: body, clothes, jewellery and performance |
| Outfit sentence | required (checklist 14) | never |

### Inputs
- `<Video 1>` = `guide.mp4` from `python -m cv_tools.motion_guide` ([cv-tools](https://github.com/FrancescoSaverioZuppichini/cv-tools)) `--input <window.mp4> --output <dir> --mask-prompt "head, hair" --mask-grow 0.02`, fed at 368×656 with the window's audio.
  - SAM 3 runs "head" and "hair" as two text prompts on the same frame and pools both masks. The track starts on the first frame with a person (cv-tools `896696a`). The skeleton and the eyebrow + mouth dots are drawn on top, as in the character swap (motion_guide defaults, Sapiens2 0.8b).
  - Free the GPU first (ComfyUI `/free`): the jeans face guide ran out of memory on 2026-11-19 while ComfyUI held 18.5 GB.

### Workflow
1. Cut the window and make the frame strip, exactly as the character swap's steps 1–2.
2. The writer fills the slots of the template below, following the character swap's "Writing the slots", with these changes:
   - `{FACE_LINE}` is written once per character and then fixed; our test character's: `She is a 21-year-old woman with long straight medium chestnut-brown hair and warm brown eyes.`
   - There is no `{OUTFIT}`, `{CHARACTER_LINE}` or `{OUTFIT_LOCK}`.
   - `{FRAMING}` may say which part of her body shows ("so her chest and shoulders show"), never what she wears.
3. Audit with `scripts/h3_audit.py <dir>`. It uses this template for any prompt whose `<Subject 1>` says "only her face, identity and hair". Then check the moves against the strip by eye.
4. After the render, do the character swap's face-and-hands check. Then, on a synced side by side with the original, check that her clothes match the source and that her hair is the character's, not the source's hairstyle.
5. Optional face pass: `facecrop.py` → `face_refine.py` → `facestitch.py`, as in the character swap's "Soft face" row. It was tested on full-swap renders only.

### Template
`{…}` is filled per clip. Everything else is fixed text, copied word for word.

```
subject_definitions:
<Subject 1> is the young woman of the character sheet <Picture 1>: only her face, identity and hair. {FACE_LINE}
<Subject 2> is the woman in <Video 1>: her body, her clothes and jewellery, her body motion, head turns, hand gestures, expression timing, mouth movement, gaze, position and scale in the frame.
<Subject 3> is the scene of <Video 1>: {SCENE_SHORT}.
<Video 1> is the source video for the target video edit. The woman's face and hair in it are hidden under a heavy blur. The blur only carries her head motion and expression; it is not part of any picture, and it never appears in the target video.

summary:
[video editing + audio reuse] The target video is an edited version of <Video 1>. <Subject 2> gets the face and hair of <Subject 1> and keeps everything else, in <Subject 3>, with the original sound. She stays dressed exactly as in <Video 1> in every frame, in the same clothes and jewellery; nothing of <Picture 1> other than the face and hair appears. The blur on <Video 1> is not part of the target video.

retention_analysis:
<Video 1> (shot length and original sound): partially_preserved - the shot length and the sound remain; the woman's face and hair and the blur are not kept.
<Subject 2> (throughout [Shot 1]): partially_preserved - her body, clothes, jewellery, movement, gestures, expression timing, mouth movement, gaze, position and scale remain; only her face and hair are replaced by those of <Subject 1>.
<Subject 3> (throughout [Shot 1]): fully_preserved - {KEPT}.
<Subject 1> (throughout [Shot 1]): attribute_transfer - only her face and hair come from <Picture 1>, not from <Video 1>; her face's skin tone matches the neck and arms of <Subject 2>, never the colour of the blur.

detailed_description:
{STYLE} [Shot 1] <Subject 2>, with the face and hair of <Subject 1>, performs her own motion and expressions as shown in <Video 1>, frame by frame, in <Subject 3>: {SCENE}. {FRAMING} {MOVES} {CAMERA} Her face is sharp, natural and fully visible in every frame, lit by {LIGHT}, with real skin texture. The picture is clean, with no blur anywhere. One continuous shot with no cuts.

overall_soundscape:
The original sound of <Video 1>: {SOUND}.

non_diegetic_music:
N/A
```

**No-sound variant** (the only allowed changes): the summary prefix becomes `[video editing]`; ", with the original sound" is dropped; the `<Video 1>` retention line becomes "(shot length): partially_preserved - the shot length remains; the woman's face and hair and the blur are not kept."; write a new `overall_soundscape`.

**Evidence:** method 5 (`r1f90-*`), 2026-11-17. Six clips (bridge, video 2, reel 01, reel 02, reel 03, snap 6), 3.75 s (90 frames), seed 1001, 736×1312, 3.1–3.2 min each. All six prompts follow this template word for word (551–690 words). The character's face and hair, with the source's own clothes kept, on 6 of 6. Reel 02 kept the source's pulled-back hairstyle. These verdicts are by eye, by the agent that ran them; no person has rated the runs yet.

### Checklist (all must pass before rendering)
| # | Rule | From |
|---|---|---|
| 1 | No sticker, caption, overlay or on-screen text is kept, described or quoted | character swap 25 → 26 |
| 2 | Nothing drawn is named anywhere (skeleton, dots, lines, guides, keypoints) | character swap, iterations 0–2 → 3 |
| 3 | The `<Video 1>` definition says her face and hair are hidden under a heavy blur that never appears | method 5 |
| 4 | The `<Video 1>` retention line is partially_preserved, with her face and hair and the blur not kept | method 5 |
| 5 | The summary says the blur is not part of the target video | method 5 |
| 6 | "The picture is clean, with no blur anywhere." just before "One continuous shot with no cuts." | character swap, iteration 3 |
| 7 | The skin-tone line matches her face to the neck and arms of `<Subject 2>` | method 5 (a guard, never tested alone) |
| 8 | None of her clothes, jewellery or hair is named | rule; word list + eye |
| 9 | Pictures cited inside `<Subject 1>` only, no standalone `<Picture N>` lines | character swap 18e → 18f |
| 10 | `<Subject 2>` is partially_preserved, never fully: her face and hair go | method 5 |
| 11 | Moves in prose, no timestamps | character swap |
| 12 | Scene and moves match the strip: nothing invented, right order | official guide |
| 13 | Fixed text copied word for word | method 5 |
| 14 | No outfit sentence ("She wears the outfit of …") | task rule |

### Fallbacks: symptom → what to try
Evidence: **strong** = failed and fixed on several runs or clips. **Medium** = one before/after pair. **Weak** = one run. **Open** = no fix yet.

| Symptom | Likely cause | What to try | Evidence |
|---|---|---|---|
| The source's hairstyle stays (pulled back, bun) | the blurred head outline keeps its shape | **open**. The character swap fixed the same thing with `--mask-grow 0.05` (reel 02, iteration 3 → 5); not tried here | reel 02, 1 seed (2026-11-17) |
| Dots or skeleton painted onto her | the prompt names the drawing | remove every mention (this template) | **strong** on the character swap; never seen here |
| Stickers and captions gone | the full redraw drops them | **open**, accepted for now | reel 01, snap 6 |
| Soft face | — | the face pass (workflow step 5) | **weak**, tested on full swaps only |
| The guide build runs out of GPU memory | ComfyUI holds the models | ComfyUI `/free` before `motion_guide` | jeans, 2026-11-19 |

### From the character swap to face only: the sentences that change
There is no failed → fixed pair yet; method 5 passed on its first round. These are the edits that turn the character-swap template into this one:
- `<Subject 1>`: "her face, identity, hair, body shape and the outfit she wears there (…)" → "only her face, identity and hair"; "petite and slim" dropped.
- `<Subject 2>`: "the performance of the woman in `<Video 1>`" → "the woman in `<Video 1>`: her body, her clothes and jewellery, her body motion, …".
- `<Video 1>`: "The woman in it is hidden under a heavy blur" → "The woman's face and hair in it are hidden under a heavy blur"; "carries her motion" → "carries her head motion".
- Summary: "Her clothes and jewellery in `<Video 1>` are replaced by the outfit of `<Subject 1>`." → "She stays dressed exactly as in `<Video 1>` in every frame, in the same clothes and jewellery; nothing of `<Picture 1>` other than the face and hair appears."
- Shot: "`<Subject 1>` performs the motion and expressions of `<Subject 2>`" → "`<Subject 2>`, with the face and hair of `<Subject 1>`, performs her own motion and expressions"; the outfit sentence is removed.
