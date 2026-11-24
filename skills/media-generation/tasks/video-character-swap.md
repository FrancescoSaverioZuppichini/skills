# Task: character swap in a video

**Goal:** the character from a character sheet replaces the whole person in a source clip: face, hair, body and clothes. Motion, expression timing, scene, camera and sound follow the clip. Not a face swap (`video-face-swap.md`, on request only).

**Model:** MiniMax H3 (Singularity + Pika). How H3 prompts work, shots, length: `models/minimax-h3.md`. Render setup and where every rule came from: `references/video-character-swap-history.md`.

## Before you start: ask if unsure
- Which clip, and which part: the whole clip (default), a time range, or one shot?
- Which character sheet? Default: the dressed sheet the workflow loads.
- A new outfit? An outfit picture means dressing the sheet first (step 0).
- Keep the clip's sound? Default yes. A clip without an audio track needs the no-sound variant: what should it sound like?
- Which seed(s)?
- Do you want to see the inputs (guide, sheet, prompt) before the render?

**REFINE and DE-ROPE stay off; never ask about them.** Suggest REFINE only when the user complains about a soft or low-quality face. Suggest DE-ROPE only when the user brings it up or complains about the motion (smear, wobble, a wrong head turn).

**Spark-H3 stays on** (group 8, on by default): sparse attention on the main pass, ~20 % faster, the same video. Turn it off only for an exact dense render.

## Steps
Run cv-tools where it is installed (the GPU machine); look at the strips wherever you are. Over ssh, `ssh <host> 'bash -s' <<'EOF'` … `EOF` keeps the variables remote.

```bash
SRC=/abs/path/source.mp4      # the clip as the user gave it
OUT=/abs/path/work/clip1      # an empty work folder
CV=/abs/path/cv-tools         # cv-tools checkout (has .venv)
PY="$CV/.venv/bin/python"     # runs the skill's scripts (cv2, transformers)
SKILL=/abs/path/media-generation   # the whole skill folder on this machine: the audit reads its tasks/
NAME=clip1                    # a unique name for the files sent to ComfyUI
mkdir -p "$OUT/prompt"
```

0. **New outfit only.** Dress the undressed body sheet with `image-outfit-swap.md` (Image 1 = the body sheet, Image 2 = the outfit picture, finishing steps off). Only Qwen-dressed sheets are allowed, never one dressed by H3. Then write the sheet's three values (The person, below) for the new outfit and use them in the prompt.
1. **The part to render.** Whole clip: `CLIP="$SRC"`. A part or one shot: cut it, keeping the sound; take the times from step 2's `shots.json` when it's a shot.
   ```bash
   CLIP="$OUT/clip.mp4"
   ffmpeg -nostdin -y -ss <START> -i "$SRC" -t <SECONDS> -c:v libx264 -crf 12 -pix_fmt yuv420p -c:a aac -ar 48000 "$CLIP"
   LEN=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$CLIP")
   ```
   The workflow renders the longest 17n+5 frames that fit at 24 fps (73 = 3 s, 124 = 5.2 s, 201 = 8.4 s, 241 = 10 s). Never cut a clip shorter to make it easier.
2. **Shots.** `shots.json` (cuts, `MM:SS.mmm` times) and one strip per shot (every 6th frame, left to right, top row first; frame numbers in `strip_frames`):
   ```bash
   (cd "$CV" && .venv/bin/python -m cv_tools.shots --input "$CLIP" --output "$OUT/shots")
   ```
   - One shot: the one-shot template, no shot timestamp (the moves still carry their `(at X s)` anchors).
   - N shots: the multi-shot template. Each later shot k gets `{TIME_k}` = its `start` in `shots.json`, and its own `{SCENE_k}`, `{FRAMING_k}`, `{MOVES_k}`, `{CAMERA_k}` from its own strip, written as one later-shot block (template below).
   - A cut the tool missed: two adjacent frames that jump to a new angle or place are a cut, whatever the score (the tool's line for it: `max_score_inside_shots`). A pan slides the same place across and is not a cut. Re-run with a lower `--cut`, or split the shot by hand at that frame. A dissolve or glitch into a new angle is a cut too: split at its middle by hand (its line in `$OUT/shots.txt`, step 5; `{TIME_k}` = that time).
   - The half-second strip, for the anchors (tile k = `(at k/2 s)`, 8 per row = 4 s): `ffmpeg -nostdin -v error -y -i "$CLIP" -vf "fps=2,scale=320:-2,tile=8x4" -vsync 0 "$OUT/half-%02d.png"`
3. **Close-ups of fast moves.** Wherever hands or head move between two strip frames, tile that range (A even, B - A ≤ 26):
   ```bash
   A=0; B=26
   ffmpeg -nostdin -y -i "$CLIP" -vf "select='between(n,$A,$B)*not(mod(n,2))',scale=480:-2,tile=7x2" -frames:v 1 -vsync 0 "$OUT/dense-$A-$B.png"
   ```
4. **Sound.** Empty = silent clip (no-sound variant). Otherwise listen, or read the spectrogram: stacked bands = a voice or singing, a regular beat = music. A voice or singing: take the words with their times; the ones her lips move to go in her moves (Writing the slots).
   ```bash
   AUDIO=$(ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$CLIP"); echo "audio: ${AUDIO:-none}"
   [ -n "$AUDIO" ] && ffmpeg -nostdin -y -i "$CLIP" -lavfi showspectrumpic=s=1024x256:legend=0 "$OUT/spec.png"
   [ -n "$AUDIO" ] && "$CV/.venv/bin/python" "$SKILL/scripts/words.py" "$CLIP" > "$OUT/words.txt"   # start end word
   ```
5. **Guide video** (`<Video 1>`), **one per shot:** SAM loses her across a cut (Coffee time, 2026-11-23: tracked from frame 0, lost from the cut to the end), so each shot of step 2 gets its own track, and the guides are joined in order with the clip's sound. One shot runs the loop once. Her whole body is blurred inside her SAM mask, the pose drawn on top. Free ComfyUI's GPU memory first (`curl -X POST <server>/free -d '{"free_memory":true}'`).
   ```bash
   GUIDE=(--mask-prompt person --mask-grow 0)
   python3 -c 'import json, sys; s = json.load(open(sys.argv[1])); [print(x["shot"], x["start_frame"] / s["fps"], (x["end_frame"] + 1) / s["fps"]) for x in s["shots"]]' "$OUT/shots/shots.json" > "$OUT/shots.txt"
   : > "$OUT/guides.txt"
   while read -r k a b; do
     ffmpeg -nostdin -v error -y -ss "$a" -to "$b" -i "$CLIP" -c:v libx264 -crf 12 -pix_fmt yuv420p -c:a aac -ar 48000 "$OUT/shot-$k.mp4"
     (cd "$CV" && .venv/bin/python -m cv_tools.motion_guide --input "$OUT/shot-$k.mp4" --output "$OUT/guide-$k" "${GUIDE[@]}")
     "$PY" "$SKILL/scripts/face_strip.py" "$OUT/shot-$k.mp4" "$OUT/guide-$k/keypoints.npz" "$OUT/face-$k.jpg" --start "$a"
     echo "file '$OUT/guide-$k/guide.mp4'" >> "$OUT/guides.txt"
   done < "$OUT/shots.txt"
   ffmpeg -nostdin -v error -y -f concat -safe 0 -i "$OUT/guides.txt" -c:v libx264 -crf 12 -pix_fmt yuv420p -c:a aac -ar 48000 "$OUT/$NAME-guide.mp4"
   ```
   Then look at the joined guide: no frame where she is unblurred. A clip that fades to black at the end stops `motion_guide` on its last shot ("SAM lost the person on N frames"): end that shot before the black frames in `$OUT/shots.txt` and rerun, as long as it still covers the 17n+5 frames the workflow renders.
6. **Write the prompt** into `$OUT/prompt/prompt.txt`: copy the template below word for word, fill the person's three values (The person, below), and replace every other `{SLOT}` with this clip's text, from the strips and close-ups of the **raw** clip, never from the guide. Several shots: add one later-shot block per shot (template below). Rules: "Writing the slots" below. This whole text is what goes in the workflow's `Swap prompt` box.
7. **Audit** (exit 1 = fix and rerun; add `--no-lip-sync` when the sentence is dropped), then reread every move against the strips (checks 10–12):
   ```bash
   python3 "$SKILL/scripts/h3_audit.py" "$OUT/prompt" --seconds "$LEN"
   ```
8. **Render** (Run, below). Then check (Check the result).

### Worked mapping: shots.json → prompt (placeholders only)
```json
{"fps": 24.0, "frames": 192, "shots": [
  {"shot": 1, "start_frame": 0,   "end_frame": 101, "start": "00:00.000", "end": "00:04.250", "cut_score": null,  "strip": "…/shot-1.png"},
  {"shot": 2, "start_frame": 102, "end_frame": 191, "start": "00:04.250", "end": "00:08.000", "cut_score": 0.526, "strip": "…/shot-2.png"}]}
```
- Shot 1 (from `shot-1.png`) fills `{SCENE}`, `{FRAMING}`, `{MOVES}`, `{CAMERA}` after `[Shot 1]`, no timestamp.
- Shot 2 (from `shot-2.png`) is its own block right after shot 1's `{CAMERA}`, its `start` as the time:
  ```
  [Shot 2] At 00:04.250, the shot cuts to <Subject 1> in <Subject 3>: <place and its main objects in shot 2>. <how close, from where to where, which body parts are in view> She wears the outfit of <Subject 1> in every frame: {OUTFIT_LOCK}. <shot 2's moves, in order> <one sentence ending "matching the framing and speed of <Video 1> throughout.">
  ```
- The retention lines say `(throughout [Shot 1], [Shot 2])`, and the closing sentence becomes "It cuts only where <Video 1> cuts."

## The person
The workflow has no persona node. Who she is and what she wears come from two inputs:
- `Picture 1 · sheet`: her dressed character sheet.
- `Swap prompt`: the whole prompt. Its only per-person text is these three values, copied verbatim.

Our character's dressed sheet:
- `{OUTFIT}`: `a silver chain-mail halter top that leaves her back bare and a glossy black patent-leather mini skirt`
- `{CHARACTER_LINE}`: `She is a 21-year-old woman with long straight medium chestnut-brown hair, warm brown eyes, petite and slim.`
- `{OUTFIT_LOCK}`: `the silver chain-mail halter top covers her chest and the glossy black patent-leather mini skirt covers her hips`

Another person or outfit: change only those two inputs, her values written the same way.
```bash
--set "Picture 1 · sheet.image=@/abs/her-dressed-sheet.png" \
--set "Swap prompt.value=$(cat "$OUT/prompt/prompt.txt")"   # her three values in place of these
```

## Writing the slots
Write only what the raw frames show: never from the blurred guide, never from another clip, never what you hope the render does. Her look comes only from the sheet: never name the source person's clothes, accessories, hairstyle, hair colour or skin ("her hair" as something that moves is fine; never a hairstyle). Never name anything drawn, hidden or overlaid on the input, not even to exclude it. Fixed text is copied word for word; only `{SLOTS}` change. Keep the clip's sound unless told otherwise.

Directions are **picture directions**, as the video plays: top, bottom, left, right of the frame, even when the picture is turned sideways.

| Slot | Write | Example |
|---|---|---|
| `{SCENE_SHORT}` | 5–12 words: the place, its light, the kind of framing (details go in `{SCENE}` and `{FRAMING}`) | "<place> in <light>, <kind of framing>" |
| `{KEPT}` | what of the scene stays, ending "as `<Video 1>`" | "the same <place>, light and camera path as <Video 1>" |
| `{STYLE}` | one sentence: "Realistic phone footage <where, light>, filmed <by another person holding the phone / from a phone standing still / as a selfie at arm's length>; she holds nothing." or "…; she holds <object> in one hand." Her outstretched arm toward the lens = selfie (then end with "her other hand is empty", or "her hands stay out of view" when neither shows, instead of "she holds nothing"); the background never moves = standing still; a small drift = another person. A picture turned sideways: add "with the picture turned a quarter turn sideways". | |
| `{SCENE}` | the place and its 3–5 main objects (up to 8 when the camera swings to new things, in the order they appear; the swing itself goes in `{CAMERA}`). Leave out other people and small details: they stay because the scene is kept | "<place> with <object>, <object> and <object>" |
| `{FRAMING}` | one or two sentences: how close, from where to where, and **which parts of her body are in view**, named as body parts (her top, waist, hips, legs); the outfit text decides what covers them | "She is framed <how close, from which angle>, from <where> to <where>; the view shows <body parts in view>." |
| `{MOVES}` | First the facing sentence, then **one sentence every 0.5 s, each opening with its time on the clip's clock**: `(at 0.0 s)`, `(at 0.5 s)`, …, from the half-second strip (step 2), 12–22 words each. An anchor covers its half second (`(at 4.0 s)` = 4.0–4.5 s); the last one is the last half second the render covers (its 17n+5 length, step 1). The clock never restarts at a cut: shot 2 cut at 7.9 s opens `(at 8.0 s)`. At most two gestures per sentence (expressions and the wind don't count), each with its verb ("covers her mouth and laughs"); nothing new = say what she holds ("keeps the finger raised"). **Say which way her body faces and write a turn only if the frames show one.** A turn = you see her side or her back; while her chest faces the camera it's a sway ("her hips sway", "her weight shifts", never "her body angles"). If she never turns, say so. Can't tell a direction: leave it out. Small head tilts can be left out. | "She keeps her front to the camera the whole time and never turns. (at 0.0 s) One hand covers her mouth, her eyes on the lens. (at 0.5 s) The hand slides down to her chin." |
| `{CAMERA}` | one sentence ending "…matching the framing and speed of <Video 1> throughout." Still, handheld drift, following, a swing or a tilt, as the strip shows; a camera move only if the background moves. The background sliding to the picture left = the camera swings to the picture right | "The camera stays still, matching…" |
| `{LIGHT}` | "the same <light> as the <scene>" | "the same <light> as the <place>" |
| `{SOUND}` | the kinds of sound, in order; her own words go in `{MOVES}`, not here; name only what you're sure of ("music with a steady beat" when you can't tell whether there's a voice) | "a short voice line at the start, then loud music" |

- **Many quick beats** (a dance): keep every change in what her hands or body do; merge repeats ("pushes her hair back twice", "bounces to the beat").
- **Her mouth:** only from the face strips of the raw clip (`$OUT/face-<k>.jpg`, step 5: her face every 1/4 s, labelled on the clip's clock), never from the frame strips. Every mouth shape goes in the anchor where it starts. **An odd shape (pout, kiss, lip bite, tongue out, mouth wide open) is written twice: where it starts and where it ends** ("(at 9.5 s) … her lips pushed into a small, sudden pout. (at 10.5 s) Her lips relax and close …"). A shape with no end is held to the end of the clip. The last anchor says the mouth she ends with.
- **Her words:** only when her lips move to them in the face strip. Each word or short phrase from `words.txt` goes in the anchor where it starts, as heard, in its language; words in the same anchor share one `<d>`. The face strip wins over `words.txt`: a word stretched back to 0.00 s, a misheard word, or words on a song with no voice (Whisper invents them: "Thank you so much…") are moved, fixed or dropped from it: `(at 2.5 s) <Subject 1> (S1) sings along, <d>[English] Crashing</d>, her eyes closed`; later ones `(S1) sings along, <d>[English] hit a</d>`. Speech: `(S1) says, <d>[English] …</d>` (open: not render-tested).
- **Lip-sync sentence:** with her words (she sings or speaks in the source, or the user asks for her singing); otherwise drop it and audit with `--no-lip-sync`.
- **Hands:** "one hand" / "her other hand"; when you can't tell which, say where it is ("the hand at the picture right"). **Eyes hidden** (sunglasses, hair): write where her head faces, never what covers the eyes. **Objects she holds** stay: name them in `{STYLE}` and in the moves.
- **Phones:** never name a phone in her hand, or the model paints one ("filmed from a phone standing still" is fine: that phone is the camera).
- **Her head leaves the frame:** keep the fixed face line anyway and write the move ("the camera drops to her waist").
- **Never write the aspect ratio or resolution:** the render's size sets them.
- **Banned words** (the audit reads this list; use other words, e.g. "pulls her arm back", not "drawn back"):
  - drawing: `skeleton, keypoint, keypoints, guide, guides, drawn, drawing, dots, pose line, pose lines, drawn line, drawn lines, face marks, white marks`
  - overlays: `sticker, stickers, overlay, overlays, caption, captions, speech bubble, speech bubbles, on-screen, card, cards`
  - source wear: `corset, corsets, garter, garters, choker, chokers, stocking, stockings, pvc, latex, tattoo, tattoos, blouse, blouses, necklace, necklaces, pendant, pendants, bun, buns, ponytail, ponytails, updo, braid, braids, sneaker, sneakers, trainers, boot, boots, heels, sandals, shoes, socks, jeans, trousers, pants, sweatpants, joggers, leggings, shorts, hoodie, hoodies, sweater, sweaters, jumper, jumpers, cardigan, cardigans, jacket, jackets, coat, coats, t-shirt, t-shirts, tank top, tank tops, crop top, crop tops, sports bra, sports bras, bra, bras, bikini, bikinis, dress, dresses, earring, earrings, bracelet, bracelets, ring, rings, lanyard, lanyards, glove, gloves, glasses, sunglasses, hat, hats, scrunchie, scrunchies, hair tie, hair ties, belt, belts`
  - The sheet's own outfit text (`{OUTFIT}`, `{OUTFIT_LOCK}`) is exempt from the source-wear list.
  - The list can't be complete: no word for anything the source woman wears (sleeve, zip, fabric, strap, logo) is allowed either.

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
{STYLE} [Shot 1] <Subject 1> performs the motion and expressions of <Subject 2> as shown in <Video 1>, frame by frame, in <Subject 3>: {SCENE}. {FRAMING} She wears the outfit of <Subject 1> in every frame: {OUTFIT_LOCK}. {MOVES} She lip-syncs the vocals in the original sound of <Video 1>, whether she speaks or sings; the soundtrack itself is unchanged. {CAMERA} Her face is sharp, natural and fully visible in every frame, lit by {LIGHT}, with real skin texture. The picture is clean, with no blur anywhere. One continuous shot with no cuts.

overall_soundscape:
The original sound of <Video 1>: {SOUND}.

non_diegetic_music:
N/A
```

**Two shots**, exactly what the audit builds (`template(task, 2)`); three or more shots repeat the `[Shot N]` block:

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
<Subject 2> (throughout [Shot 1], [Shot 2]): attribute_transfer - only her movement, gestures, expression timing, mouth movement, gaze, position and scale transfer to <Subject 1>.
<Subject 3> (throughout [Shot 1], [Shot 2]): fully_preserved - {KEPT}.
<Subject 1> (throughout [Shot 1], [Shot 2]): attribute_transfer - her face, hair, body and outfit come from <Picture 1>, not from <Video 1>; her skin tone is hers, never the colour of the blur.

detailed_description:
{STYLE} [Shot 1] <Subject 1> performs the motion and expressions of <Subject 2> as shown in <Video 1>, frame by frame, in <Subject 3>: {SCENE}. {FRAMING} She wears the outfit of <Subject 1> in every frame: {OUTFIT_LOCK}. {MOVES} She lip-syncs the vocals in the original sound of <Video 1>, whether she speaks or sings; the soundtrack itself is unchanged. {CAMERA} [Shot 2] At {TIME_2}, the shot cuts to <Subject 1> in <Subject 3>: {SCENE_2}. {FRAMING_2} She wears the outfit of <Subject 1> in every frame: {OUTFIT_LOCK}. {MOVES_2} {CAMERA_2} Her face is sharp, natural and fully visible in every frame, lit by {LIGHT}, with real skin texture. The picture is clean, with no blur anywhere. It cuts only where <Video 1> cuts.

overall_soundscape:
The original sound of <Video 1>: {SOUND}.

non_diegetic_music:
N/A
```

`{TIME_2}` = shot 2's `start` in `shots.json`, as `MM:SS.mmm` (e.g. `00:04.250`).

**Several shots** (the only allowed changes; the audit builds them from these two lines):
- every `(throughout [Shot 1])` lists all shots: `(throughout [Shot 1], [Shot 2])`;
- each later shot is one block right after shot 1's `{CAMERA}`, in order, with its own `{SCENE}`, `{FRAMING}`, `{MOVES}` and `{CAMERA}`:
- Later shot: `[Shot {N}] At {TIME}, the shot cuts to <Subject 1> in <Subject 3>: {SCENE}. {FRAMING} She wears the outfit of <Subject 1> in every frame: {OUTFIT_LOCK}. {MOVES} {CAMERA}`
- Closing sentence: `One continuous shot with no cuts.` becomes `It cuts only where <Video 1> cuts.`
- `{SCENE_SHORT}`, `{KEPT}`, `{LIGHT}` and `{SOUND}` cover all shots ("the same <light 1> and <light 2> as the two scenes").

**No sound** (only for a clip with no audio stream, or when told not to keep it): the summary prefix becomes `[video editing]`; the lip-sync sentence is dropped; ", with the original sound" is dropped; the `<Video 1>` retention line becomes "(shot length): partially_preserved - the shot length remains; the woman and the blur are not kept."; `overall_soundscape` becomes, for a silent clip: "Quiet natural ambience of <the scene in 2–5 words>, with no speech and no music." (open: not render-tested), or the new sound you were asked for. In the workflow: `Clip sound on / off` = false.

**Length** (the fixed text alone is ~340 words): a 3 s single shot lands at 540–670 words. Per shot: `{MOVES}` 30–45 words per second, `{FRAMING}` up to 35, `{SCENE}` up to 30, the other slots one short sentence; trim words inside the `{MOVES}` sentences first, never an anchor. The audit fails above 750 words + 150 per later shot + 45 per second past 3 s (`--seconds`).

## Run
Default size: ~1 MP (Output size: from image, 0.92 MP, multiple 32; a 9:16 clip renders 736×1312). Sheet, models and sampler are fixed in the workflow.

**How the guide reaches H3:** `Video 1 · guide` loads the whole guide at 24 fps with its sound; `Clip length` cuts it to the longest 17n+5 frames; `Guide feed size (half)` (0.23 MP) and `Guide feed` shrink it to half the output (368×656 for 9:16); `References` hands it to H3 as `<Video 1>`, next to the sheet as `<Picture 1>` and the clip's sound. H3 snaps it to its 32 px grid (384×640), its text encoder reads it at 2 fps, and its frames join the video tokens, so a bigger guide costs time: the full-size guide (704×1280) was 3–4× slower for little gain (2026-11-23).

```bash
$RUN minimax-h3-reference-to-video \
  --set "Video 1 · guide.video=@$OUT/$NAME-guide.mp4" \
  --set "Swap prompt.value=$(cat "$OUT/prompt/prompt.txt")" \
  --set "Seed.noise_seed=1001" \
  --set "Clip sound on / off.value=true" \
  --set "REFINE on / off.value=false" \
  --set "DE-ROPE on / off.value=false" \
  --set "Spark-H3 on / off.value=true"
```
- Output: `<ComfyUI>/output/h3-ref2vid/swap_*.mp4`, with sound.
- Time (3090, models loaded): 3 s one pass 1.7 min with Spark, 2.1 min without (2026-11-23); REFINE on 3.8 min full frame, 2.6–2.9 min masked (2026-11-22). Time grows with length: a full 10 s clip took 12 min in one pass (2026-11-13, older graph). REFINE on a long clip may run out of memory (141 frames did). DE-ROPE: not timed in this graph.
- REFINE (R450-2): the toggle alone drops the main pass to a 0.50 MP draft, the learned upscaler doubles it to 2.1 MP, then 2 Pika steps from noise 0.45. No size to set by hand. `Masked refine on / off` (default on) redraws only her plus a margin.

## Check the result
1. `/history` of the run: the LoadImage input is the sheet you meant.
2. Every 6th frame at full size: her face, both hands, the outfit present (never nude), no dots or lines painted on her, none of the source's clothes, hairstyle or accessories back.
3. Facing: she turns only where the raw clip turns. Compare with the raw strips frame by frame.
4. A synced side by side with the raw clip, with sound: motion, timing, camera and cuts match.

| Symptom | Fix | Evidence |
|---|---|---|
| Dots or lines painted on her face or body | remove every word naming the drawing | strong |
| Her body turns where the clip doesn't; face soft | rewrite the moves from the raw frames; say "never turns" when she doesn't | strong |
| Nude, outfit lost | outfit sentence in every shot (template) | strong |
| Source clothes kept | the whole woman inside the guide's blur (`--mask-prompt person`) | strong |
| Source hairstyle or accessories come back | `motion_guide --mask-grow 0.05` on that clip only (off by default: it pulls her hands toward her head) | medium |
| Glowing eyes, white spot on the nose | eyebrow + mouth dots only (motion_guide default) | medium |
| A camera move invented before a cut | multi-shot template with the cut time | medium (1 seed) |
| Phone painted in her hand | never name the phone | strong |
| Small or far face soft | REFINE on; check the moves are true first | medium |
| Stickers, captions disappear | none yet; accepted | open |
| Black bars around a shot | kept on the approved final, never named; cropping them away is under test | open |

## Lessons (dated, evidence)
- 2026-11-24 · On a clip where she doesn't sing, the lip-sync sentence made her sing on one render and not on another: the mouth lines decide. Medium (1 clip).
- 2026-11-24 · A pout that lasts one second, written as "pushes her lips into a pout" with no end, became a kiss-pout held for the whole 11 s clip (face swap, night car). Mouth lines come from the 1/4 s face strip; an odd shape is written where it starts and where it ends. Strong (the owner's rule).
- 2026-11-23 · H3 takes her timing from the move list: in prose, a 14 s upright singing selfie ran 2 s ahead of the song on every render. One anchored sentence every 0.5 s plus her sung words in `<d>` lines at their times: on time, the owner's pick ("perfect", seed 1001); on a 2-shot 15.5 s clip, shot 1 without them ghosted two poses at 3.8 s, with them clean (1 seed), and the owner chose them for the final. Medium (2 clips).
- 2026-11-24 · Person mask grown 5 % vs not grown (`--mask-grow 0`), one clip, 3 seeds (full clip and two 5 s cuts): the same moves on every seed; not grown leaves the hair edge a touch darker at moments; the user saw her hands drift toward her head with the grow. Not grown is the default. Medium.
- 2026-11-14 · Naming the drawing in any wording paints it (white blobs on the face); not naming it: clean on 10 of 10. Strong.
- 2026-11-14 / 11-16 · Never a ControlNet, for pose or inpainting: wrong timing, wrong hand signs. Strong; the user's hard rule.
- 2026-11-15 · No 4-step speed LoRA (worse look); Pika runs only on its own 6 knots, never stacked with a speed LoRA. The user's rule.
- 2026-11-17 · Only Qwen-dressed sheets; H3-dressed sheets are deleted. A face close-up or an outfit crop as an extra picture added nothing. The user's rule; medium.
- 2026-11-19 · Outfit sentence inside every shot: nude on 2 of 2 seeds without it, dressed on every render with it. Strong.
- 2026-11-22 · One false move line ("turns half away" where she never turns) turned her on 3–4 of 5 seeds and softened the face on 5 of 5; the true line: 0 of 5. Strong.
- 2026-11-22 · Small or far faces: REFINE helps (89 px face: identity +0.03 to +0.10 on 4 of 4 seeds; 166 px face: median +6 %); big faces unchanged. Crops, face passes and paste-backs are banned: full frame only. Medium; the user's rule.
- 2026-11-22 · Masked refine = full refine on faces, identity, pose and seams at 67–77 % of its time (2 clips). Medium.
- 2026-11-13 · Long clips drift more: 8.4 s, pose good on 2 of 4 seeds; try another seed. Never a reason to cut. Medium.
- 2026-11-22 · Multi-shot tags hold shot 1's framing to the cut; prose invented a camera swing before it. Medium (1 seed).
- 2026-11-02 / 11-13 · De-RoPE fixes fast-motion smear and locks head pose (5 of 5) at 3–4× the time; it does nothing for small faces; at inject 0.67 it re-decided the pose. Off by default; suggested only when the user complains about the motion (rule, 2026-11-22). Medium.
- 2026-11-19 · Guide fed at 432 or full size instead of half: no visible change, +7 % / +80 % time. Medium.
- Open: stickers and captions vanish in the redraw; short bob on one clip after the wider blur; barefoot (the sheet has no shoes); sheet details leak (a studded wristband).
