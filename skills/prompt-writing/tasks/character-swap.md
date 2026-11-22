# Task: character swap in a video (MiniMax H3, Singularity + Pika)

**Goal:** the character from a character sheet replaces the whole person in a source clip: face, hair, body and clothes. Motion, expression timing, scene, camera and sound follow the source. Not a head or face swap (that is `tasks/face-swap.md`, only on request).

Read `models/minimax-h3.md` first (the H3 format). Render setup, evidence and history: `references/character-swap-history.md`. You don't need them to write.

## Rules
1. **Write only what the raw frames show.** Never from the blurred guide, never from another clip, never what you hope the render does.
2. **Never name anything drawn, hidden or overlaid on the input** (banned words below). Naming the drawing, even to exclude it, gets it painted onto her.
3. **Her look comes only from the sheet.** Never name the source person's clothes, accessories (sunglasses, bags, hats), hairstyle, hair colour or skin; they are never kept. "Her hair" as something that moves is fine ("pushes her hair back", "the wind lifts her hair").
4. **Motion comes from the video.** Moves are plain prose in playback order; timestamps appear only at cuts.
5. **Fixed text is copied word for word.** Only `{SLOTS}` change.

## Workflow
Copy this block, set the four variables, run it step by step. Paths are absolute because cv-tools runs from its own folder.

```bash
SRC=/abs/path/source.mp4                 # the source clip
OUT=/abs/path/work/clip1                 # an empty work folder
CV=/abs/path/cv-tools                    # cv-tools checkout (has .venv)
SKILL=/abs/path/prompt-writing           # this skill
mkdir -p "$OUT/prompts"

# 1. Look at the whole clip: strips in $OUT/full/shot-N.png, cuts in $OUT/full/shots.json
(cd "$CV" && .venv/bin/python -m cv_tools.shots --input "$SRC" --output "$OUT/full")

# 2. Cut the 3 s window: 73 frames at 24 fps, 736x1312 (START in seconds, inside one shot)
START=0
ffmpeg -y -ss $START -i "$SRC" -t 3.042 \
  -vf "fps=24,scale=736:1312:force_original_aspect_ratio=increase,crop=736:1312" -frames:v 73 \
  -af apad=whole_dur=3.042 -c:v libx264 -crf 12 -pix_fmt yuv420p -c:a aac -ar 48000 "$OUT/window.mp4"

# 3. Shots and strips of the window: $OUT/window/shots.json + shot-N.png (every 6th frame = 0.25 s)
(cd "$CV" && .venv/bin/python -m cv_tools.shots --input "$OUT/window.mp4" --output "$OUT/window")

# 3b. Close-up of a fast move: every 2nd frame from A to B (repeat for each fast range)
A=0; B=26
ffmpeg -y -i "$OUT/window.mp4" -vf "select='between(n,$A,$B)*not(mod(n,2))',scale=480:-2,tile=7x2" \
  -frames:v 1 -vsync 0 "$OUT/dense-$A-$B.png"

# 4. Sound: no output = silent source; otherwise read the spectrogram
ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$OUT/window.mp4"
ffmpeg -y -i "$OUT/window.mp4" -lavfi showspectrumpic=s=1024x256:legend=0 "$OUT/spec.png"

# 5. Write the prompt to $OUT/prompts/<name>.txt (template below), then audit (exit 1 = fix and rerun)
python3 "$SKILL/scripts/h3_audit.py" "$OUT/prompts"
```

What to decide at each step:
1. **Whole clip:** where she's in frame, and where the cuts are.
2. **Window:** the one you were given, otherwise the first 3 s where she's in frame, inside one shot. A source that isn't 9:16 is cropped to fill (sides or top/bottom are lost); from here on, write only from the window. **Never write the aspect ratio or resolution in the prompt:** it is set by the render's width and height (736×1312 here). MiniMax's README lists Ref2VA's ratio as "adaptive" (it follows the inputs), its prompt rewriter returns `ratio` as a separate field, and no official prompt names a ratio.
3. **Shots:** **one shot = the template as is, no timestamps. Several = the multi-shot variant, `{TIME}` = each later shot's `start` in `shots.json`.** Two adjacent frames that jump to a different angle or place are a cut too, whatever the score; a pan slides the same place across and is not a cut. Strips read left to right, top row first; frame numbers are in `strip_frames`. Wherever her hands or head move between two strip frames, run 3b on that range.
4. **Sound:** silent source = the no-sound variant with the silent-source soundscape (below). With audio: listen if you can; in the spectrogram stacked bands are a voice or singing, a regular beat is music. `{SOUND}` names the kinds of sound in order ("a short voice line, then loud music", "a voice singing over music"); speech and lyrics are never transcribed.
5. **Prompt:** fill the slots from the strips and close-ups; after the audit passes, reread every move against the strips (checklist 10–12). Only prompt `.txt` files go in `$OUT/prompts`.

## Per-sheet values (the sheet in use, copied verbatim; a new sheet gets its own)
- `{OUTFIT}`: `a silver chain-mail halter top that leaves her back bare and a glossy black patent-leather mini skirt`
- `{CHARACTER_LINE}`: `She is a 21-year-old woman with long straight medium chestnut-brown hair, warm brown eyes, petite and slim.`
- `{OUTFIT_LOCK}`: `the silver chain-mail halter top covers her chest and the glossy black patent-leather mini skirt covers her hips`

## Writing the slots
Directions are **picture directions**, as the video plays: top, bottom, left, right of the frame, even when the picture is turned sideways.

| Slot | Write | Example |
|---|---|---|
| `{SCENE_SHORT}` | 5–12 words: the place, its light, the kind of framing (details go in `{SCENE}` and `{FRAMING}`) | "a white parking garage in flat light, close selfie framing" |
| `{KEPT}` | what of the scene stays, ending "as `<Video 1>`" | "the same garage, light and camera path as <Video 1>" |
| `{STYLE}` | one sentence: "Realistic phone footage <where, light>, filmed <by another person holding the phone / from a phone standing still / as a selfie at arm's length>; she holds nothing." or "…; she holds <object> in one hand." Which camera: her outstretched arm toward the lens = selfie; the background never moves = standing still; a small drift = another person. If the picture is turned sideways, add "with the picture turned a quarter turn sideways". | |
| `{SCENE}` | the place and its 3–5 main objects (up to 8 when the camera swings to new things, in the order they appear; the swing itself goes in `{CAMERA}`). Leave out other people: they stay because the scene is kept | "a white garage with white walls and ceiling and white painted lines on the floor" |
| `{FRAMING}` | one or two sentences: how close, from where to where, and **which parts of her body are in view** (front of her top, bare waist, legs) | "She is framed close and from below, from her outstretched arm in the foreground up to her head; the view shows the front of her top, her bare waist and the front of her skirt." |
| `{MOVES}` | 4–6 sentences per 3 s shot (at least 2 for a short shot), counting the facing sentence, in order, each with its verb ("covers her mouth and laughs", "spits onto the nozzle"). **Say which way her body faces and write a turn only if the frames show one.** A turn = her shoulders rotate more than about 45°, toward one side facing the camera; anything less is a sway ("her hips sway", never "her body angles"). If she never turns, say so. | "She keeps her front to the camera the whole time and never turns." |
| `{CAMERA}` | one sentence ending "…matching the framing and speed of <Video 1> throughout." Still, handheld drift, following or a swing, as the strip shows; a camera move only if the background moves | "The camera stays still, matching…" / "The selfie camera swings steadily toward the picture right, the park sliding out as the street comes in, matching…" |
| `{LIGHT}` | "the same <light> as the <scene>" | "the same flat white light as the garage" |
| `{SOUND}` | the kind of sound, in order (step 3) | "a short voice line at the start, then loud music" |

- **Many quick beats:** 4–6 sentences still. Merge repeats of one action ("pushes her hair back twice"); never drop a change of direction or a gesture with its own verb (a wave, covering her mouth).
- **Lips move on a silent source:** write it ("her lips move"); the soundscape stays the silent-source line.
- **Hands:** "one hand" / "her other hand"; when you can't tell which is which, say where it is ("the hand at the picture right"). **Eyes hidden** (sunglasses, hair): write where her head faces ("faces the lens"), never what covers the eyes. **Objects she holds** stay (they're outside her mask): name them in `{STYLE}` and in the moves.
- **Phones:** never name a phone in her hand, or the model paints one. A selfie is "filmed as a selfie at arm's length"; her outstretched arm may be described.
- **Her head leaves the frame:** keep the fixed face line anyway and write the move ("the camera drops to her waist"). The renders follow the guide.
- **Banned words** (the audit reads this list; use other words, e.g. "pulls her arm back", not "drawn back"):
  - drawing: `skeleton, keypoint, keypoints, guide, guides, drawn, drawing, dots, pose line, pose lines, drawn line, drawn lines, face marks, white marks`
  - overlays: `sticker, stickers, overlay, overlays, caption, captions, speech bubble, speech bubbles, on-screen, card, cards`
  - source wear: `corset, corsets, garter, garters, choker, chokers, stocking, stockings, pvc, latex, tattoo, tattoos, blouse, blouses, necklace, necklaces, pendant, pendants, bun, buns, ponytail, ponytails, updo, braid, braids, sneaker, sneakers, trainers, boot, boots, heels, sandals, shoes, socks, jeans, trousers, pants, sweatpants, joggers, leggings, shorts, hoodie, hoodies, sweater, sweaters, jumper, jumpers, cardigan, cardigans, jacket, jackets, coat, coats, t-shirt, t-shirts, tank top, tank tops, crop top, crop tops, sports bra, sports bras, bra, bras, bikini, bikinis, dress, dresses, earring, earrings, bracelet, bracelets, ring, rings, lanyard, lanyards, glove, gloves, glasses, sunglasses, hat, hats, scrunchie, scrunchies, hair tie, hair ties, belt, belts`
  - The sheet's own outfit text (`{OUTFIT}`) is exempt from the source-wear list.

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

**No sound** (a silent source, or the sound must not be kept; the only allowed changes, checked by the audit): the summary prefix becomes `[video editing]`; ", with the original sound" is dropped; the `<Video 1>` retention line becomes "(shot length): partially_preserved - the shot length remains; the woman and the blur are not kept."; `overall_soundscape` becomes, for a silent source: "Quiet natural ambience of <the scene in 2–5 words>, with no speech and no music." (rule, not render-tested yet: open), or the new sound you were asked for.

The no-sound lines in full, for a silent source:
```
[video editing] The target video is an edited version of <Video 1>. <Subject 1> takes the place of the woman in <Video 1> and performs <Subject 2> in <Subject 3>. …
<Video 1> (shot length): partially_preserved - the shot length remains; the woman and the blur are not kept.
…
overall_soundscape:
Quiet natural ambience of <the scene>, with no speech and no music.
```

**Several shots** (the only allowed changes; `scripts/h3_audit.py` builds this template):
- every `(throughout [Shot 1])` lists all shots: `(throughout [Shot 1], [Shot 2])`;
- each later shot is one block right after shot 1's `{CAMERA}`, in order, with its own `{SCENE}`, `{FRAMING}`, `{MOVES}` and `{CAMERA}`:
- Later shot: `[Shot {N}] At {TIME}, the shot cuts to <Subject 1> in <Subject 3>: {SCENE}. {FRAMING} She wears the outfit of <Subject 1> in every frame: {OUTFIT_LOCK}. {MOVES} {CAMERA}`
- Closing sentence: `One continuous shot with no cuts.` becomes `It cuts only where <Video 1> cuts.`
- `{SCENE_SHORT}`, `{KEPT}`, `{LIGHT}` and `{SOUND}` cover all shots ("the same flat garage light and soft room daylight as the two scenes").

**Length** (the whole prompt; the fixed text alone is ~340 words): aim for 540–670; the audit fails above 750, plus 150 per later shot. Budget per shot: `{MOVES}` 90–150 words, `{FRAMING}` up to 45, `{SCENE}` up to 40; trim those first.

## Checklist (the audit checks 1–9; you check 10–12 by eye)
1. No banned word (drawing, overlays, source wear).
2. The `<Video 1>` definition says she's under a heavy blur that never appears.
3. The `<Video 1>` retention line is partially_preserved, with the woman and the blur not kept.
4. The summary says the blur is not part of the target video; the sound lines follow one variant (original sound kept, or no sound).
5. The clean line and the skin-tone line are present.
6. No standalone `<Picture N>` line; the woman's performance is never fully_preserved.
7. Shots: one shot has no timestamp; several have `[Shot 1]` bare and `[Shot N] At MM:SS.mmm,` increasing.
8. The outfit sentence is in every shot, after the framing.
9. Fixed text verbatim; length within the limit.
10. Every move, facing and camera move is in the frames, in the right order. No turn that isn't there.
11. `{FRAMING}` says which parts of her body are in view.
12. Directions are picture directions.

## Symptom → fix (evidence in the history file)
| Symptom | Fix | Evidence |
|---|---|---|
| Dots or lines painted on her face or body | remove every word naming the drawing | strong |
| Her body turns where the source doesn't; face soft | rewrite the moves from the raw frames; say "never turns" when she doesn't | strong |
| Nude, outfit lost | outfit sentence in every shot (template) | strong |
| Source clothes kept | hide the whole woman in the guide | strong |
| Source hairstyle or accessories come back | `motion_guide --mask-grow 0.05` | medium |
| Glowing eyes, white spot on the nose | eyebrow + mouth dots only (motion_guide default) | medium |
| The render invents a camera move before a cut | multi-shot variant with the cut time | medium (1 seed) |
| Phone painted in her hand | never name the phone | strong |
| Stickers, captions disappear | none yet; accepted | open |
