# Task: swap the person in a video

**Goal:** the character from a character sheet takes the place of the woman in a clip. Her motion, expression timing, the scene, the camera and the sound follow the clip. Model: MiniMax H3 (`models/minimax-h3.md`).

## 1. Pick the mode
Character swap is the default. Face swap only when the user asks for the face only; never propose it. Everything else in this file is the same for both.

| | Character swap (default) | Face swap (on request) |
|---|---|---|
| What changes | face, hair, body and clothes come from the sheet | only face and hair; her body, clothes and jewellery stay |
| Guide flags (step 4) | `GUIDE=(--mask-prompt person --mask-grow 0 --color)` | `GUIDE=(--mask-prompt "head, hair" --mask-grow 0.02 --include head,face)` |
| Her values (The person) | `{OUTFIT}`, `{CHARACTER_LINE}`, `{OUTFIT_LOCK}` | `{FACE_LINE}`, `{HAIR}` |
| Her clothes in the prompt | never named; the outfit sentence in every shot | named exactly in `{CLOTHES}`, in every shot; never the outfit sentence |
| The woman who sings, in `<d>` lines | `<Subject 1>` | `<Subject 2>` |
| Template | Character-swap template | Face-swap template |

## 2. Defaults, and when to change them
Start from the defaults. Change one only for its scenario, and when you show the inputs say what you changed and why.

| Setting | Default |
|---|---|
| Part | the whole clip, one run |
| Guide | the mode's flags, one track per shot |
| Prompt | the mode's template; one move sentence every half second; mouth from the face strips; no words, no lip-sync sentence |
| Sheet | the dressed sheet the workflow loads |
| Render | ~1 MP, seed 1001, clip sound on, Spark on, REFINE off, DE-ROPE off |

| Scenario | Change |
|---|---|
| The user asks for the face only | face swap (step 1) |
| Her eyes sit one above the other (head sideways) for more than half the clip | turn the clip upright, render it upright, turn the render back (step 1) |
| The user asks to remove black bars | `cv_tools.bars` (step 1) |
| A new outfit (character swap) | dress the sheet first with `image-outfit-swap.md`; only Qwen-dressed sheets |
| Her lips move to the words of a song or speech | her words in `<d>` lines and the lip-sync sentence (Her words) |
| The user asks for her singing where she doesn't | the same, and her mouth lines sing |
| No audio track, or told to drop the sound | the no-sound variant (template) |
| The one run fails (out of memory) | each shot on its own (Run) |
| The source's hairstyle or accessories come back | `--mask-grow 0.05` |
| The user finds her face soft or small | suggest REFINE |
| The user complains about the motion (smear, wobble, wrong head turn) | suggest DE-ROPE |
| The render's colour is 25+ levels off the source | ask about `video-color-match.md` |

Ask when the request doesn't say: which clip and which part, which sheet, which seed(s), whether to show the inputs before the render.

## 3. Steps
Run cv-tools and the scripts on the GPU machine; look at the images wherever you are.
```bash
SRC=/abs/path/source.mp4            # the clip as the user gave it
OUT=/abs/path/work/clip1            # an empty work folder
CV=/abs/path/cv-tools               # cv-tools checkout (has .venv)
PY="$CV/.venv/bin/python"           # runs the skill's scripts
SKILL=/abs/path/media-generation    # this whole skill folder on that machine
NAME=clip1                          # a unique name for the files sent to ComfyUI
mkdir -p "$OUT/prompt"
```

1. **The clip.**
   ```bash
   CLIP="$SRC"   # a part only: ffmpeg -nostdin -y -ss <start> -i "$SRC" -t <seconds> -c:v libx264 -crf 12 -pix_fmt yuv420p -c:a aac -ar 48000 "$OUT/clip.mp4"; CLIP="$OUT/clip.mp4"
   ```
   - Head sideways: top of her head at the picture left → `transpose=1` (back at the end: `transpose=2`); at the picture right → `transpose=2` (back: `transpose=1`). Every later step uses the upright clip.
     ```bash
     ffmpeg -nostdin -y -i "$CLIP" -vf transpose=1 -c:v libx264 -crf 12 -pix_fmt yuv420p -c:a copy "$OUT/upright.mp4"; CLIP="$OUT/upright.mp4"
     ```
   - Bars, only when the user asks: `(cd "$CV" && .venv/bin/python -m cv_tools.bars --input "$CLIP" --output "$OUT/nobars.mp4"); CLIP="$OUT/nobars.mp4"`
   - Then:
     ```bash
     LEN=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$CLIP")
     ```
     H3 renders only the longest 17n+5 frames at 24 fps that fit (the audit prints how much). Never cut the clip shorter to make it easier.
2. **Shots and the half-second strip.**
   ```bash
   (cd "$CV" && .venv/bin/python -m cv_tools.shots --input "$CLIP" --output "$OUT/shots")
   ffmpeg -nostdin -v error -y -i "$CLIP" -vf "fps=2,scale=480:-2,tile=4x2" -vsync 0 "$OUT/half-%02d.png"   # tile k = (at k/2 s), left to right, top row first
   ```
   A jump or a dissolve to a new angle or place is a cut, even when `shots.json` misses it: split it by hand in `$OUT/shots.txt` (step 4). A pan is not a cut.
3. **Sound and words.**
   ```bash
   AUDIO=$(ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$CLIP"); echo "audio: ${AUDIO:-none}"
   [ -n "$AUDIO" ] && ffmpeg -nostdin -y -i "$CLIP" -lavfi showspectrumpic=s=1024x256:legend=0 "$OUT/spec.png"   # stacked bands = a voice, a regular beat = music
   [ -n "$AUDIO" ] && "$PY" "$SKILL/scripts/transcribe.py" "$CLIP" --language <code> > "$OUT/words.txt"   # start end word
   ```
   No audio: the no-sound variant.
4. **Guide and face strips, one per shot.** Free ComfyUI's GPU memory first (`curl -s -X POST <server>/free -d '{"unload_models":true,"free_memory":true}'`).
   ```bash
   GUIDE=(--mask-prompt person --mask-grow 0 --color)   # the mode's flags (step 1)
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
   Look at the joined guide: she is blurred in every frame. A fade to black at the end stops the last shot ("SAM lost the person"): end that shot before the black frames in `$OUT/shots.txt` and rerun.
5. **Close-ups where she moves fast** (hands, head, mouth), one second at 8 fps, and a denser face strip:
   ```bash
   ffmpeg -nostdin -v error -y -ss <t> -t 1 -i "$CLIP" -vf "fps=8,scale=480:-2,tile=4x2" -frames:v 1 "$OUT/fast-<t>.png"
   "$PY" "$SKILL/scripts/face_strip.py" "$OUT/shot-<k>.mp4" "$OUT/guide-<k>/keypoints.npz" "$OUT/face-<k>-dense.jpg" --start <shot start> --every 0.1
   ```
6. **Write the prompt** into `$OUT/prompt/prompt.txt`: the mode's template word for word, her values (The person), every other `{SLOT}` from the clip's own frames (Writing the prompt).
7. **Audit.** Exit 1 = fix and rerun. It names any banned word and any changed fixed text, and prints the render's length and its last anchor. Add `--no-lip-sync` when the prompt has no lip-sync sentence. Then reread every move against the strips.
   ```bash
   python3 "$SKILL/scripts/h3_audit.py" "$OUT/prompt" --seconds "$LEN"
   ```
8. **Render** (Run), turn it back if you turned the clip upright, then check (Check the result).

## The person
The workflow has no persona node: who she is comes from the sheet (`Picture 1 · sheet`) and her values in the prompt, copied verbatim.

Character swap, our character's dressed sheet:
- `{OUTFIT}`: `a silver chain-mail halter top that leaves her back bare and a glossy black patent-leather mini skirt`
- `{CHARACTER_LINE}`: `She is a 21-year-old woman with long straight medium chestnut-brown hair, warm brown eyes, petite and slim.`
- `{OUTFIT_LOCK}`: `the silver chain-mail halter top covers her chest and the glossy black patent-leather mini skirt covers her hips`

Face swap, our character:
- `{FACE_LINE}`: `She is a 21-year-old woman with long straight medium chestnut-brown hair and warm brown eyes.`
- `{HAIR}`: `long, straight and medium chestnut-brown`

Another person or outfit: a new sheet and her values written the same way (`--set "Picture 1 · sheet.image=@/abs/her-sheet.png"` in Run).

## Writing the prompt
- Only what the clip's frames show (the upright clip if you turned it): never the guide, never another clip, never what you hope the render does.
- Directions are picture directions, as the video plays: top, bottom, left, right of the frame.
- Never name anything drawn, hidden or overlaid on the input (the guide, its colours, captions, stickers), not even to exclude it.
- Her look comes from the sheet: never the source's hairstyle, hair colour or skin ("her hair swings" is fine). Character swap: never the source's clothes or jewellery. Face swap: those go in `{CLOTHES}` and nowhere else.
- Fixed text is copied word for word; only the `{SLOTS}` change. Never the aspect ratio or the resolution.

| Slot | Write | Example |
|---|---|---|
| `{SCENE_SHORT}` | 5–12 words: the place, its light, the kind of framing | "a bedroom in warm lamp light, a close selfie" |
| `{KEPT}` | what of the scene stays, ending "as <Video 1>" | "the same bedroom, lamp light and camera path as <Video 1>" |
| `{STYLE}` | "Realistic phone footage <where, light>, filmed <as a selfie at arm's length / by another person holding the phone / from a phone standing still>; she holds nothing." Her arm toward the lens or a face filling a close frame = selfie; then end with "her other hand is empty", or "her hands stay out of view" when no hand shows. A small drift = another person; a still background = standing still; in a moving vehicle judge by her arm and the framing, not the background. | "Realistic phone footage in a bedroom at night, filmed as a selfie at arm's length; her other hand is empty." |
| `{SCENE}` | the place and its 3–5 main objects, in the order they appear; no other people, no small details | "a bedroom with a white bed, a window with blinds and a desk lamp" |
| `{FRAMING}` | how close, from where to where, and which parts of her body are in view, named as body parts (never what covers them) | "She is framed close from slightly above, from the top of her head to her chest; the view shows her face, her shoulders and one hand." |
| `{MOVES}` | the facing sentence, then one sentence every half second (Moves) | |
| `{CAMERA}` | one sentence ending "matching the framing and speed of <Video 1> throughout." Still, drift, follow, swing, tilt or roll, as the strips show | "The camera is held close with a small handheld drift and rolls a little, matching the framing and speed of <Video 1> throughout." |
| `{LIGHT}` | "the same <light> as the <place>" | "the same warm lamp light as the bedroom" |
| `{SOUND}` | the kinds of sound, in order; only what you're sure of | "a pop song with a woman's singing voice over a steady beat" |
| `{CLOTHES}` (face swap) | every garment as the frames show it (colour, kind, visible details), then jewellery and anything else she wears; the same text in every shot | "a white top with thin straps and a low neckline, a thin gold chain and small silver stud earrings" |
| `{HAIR}` (face swap) | the hair part of her `{FACE_LINE}` | "long, straight and medium chestnut-brown" |
| `{TIME_k}` (several shots) | shot k's `start` in `shots.json` (or your split), as `MM:SS.mmm` | "00:04.250" |

### Moves: one sentence every half second
- The facing sentence first: which way her body faces, and "she never turns" when she doesn't. A turn = you see her side or her back; while her chest faces the camera it's a sway. Write a turn only if the frames show one.
- Then `(at 0.0 s)`, `(at 0.5 s)`, … up to the last anchor the audit prints. An anchor covers its half second (`(at 4.0 s)` = 4.0 to 4.5 s). The clock runs through cuts: a later shot opens at the first half second after its cut.
- 12–22 words each, at most two gestures, each with its verb. Nothing new: say what she holds ("keeps the finger raised").
- A big head roll or tilt (her head leaning far to one side) is a move: write it with its side. Small tilts can go.
- Hands: "one hand", "her other hand", or the picture side ("the hand at the picture right"). Objects she holds stay: name them in `{STYLE}` and in the moves. Never a phone in her hand.
- Example: "She keeps her front to the camera and never turns. (at 0.0 s) One hand covers her mouth, her eyes on the lens. (at 0.5 s) The hand slides down to her chin as her head tips toward the picture right."

### Her mouth
- Only from the face strips (her face every 1/4 s, times on the tiles); the dense strip where it changes fast.
- Say her resting mouth at the start and whenever she goes back to it.
- An odd shape (pout, kiss, lip bite, tongue out, mouth wide open: clearly not her resting mouth) is written where it starts and where it ends; both in the same sentence when it lasts less than half a second. A shape with no end is held by H3 to the end of the video. The last anchor says the mouth she ends with.
- Example: "(at 6.0 s) She looks at the lens, her lips pushed into a small, sudden pout. (at 7.0 s) Her lips relax and close."

### Her words and the lip-sync sentence
- Only when her lips move to the words (face strip). Each word or short phrase from `words.txt` goes in the anchor where her lips start it, in its language; words in the same half second share one `<d>`. The first one names the woman who sings (step 1 table), later ones start with `(S1)`. Speech: `(S1) says, <d>[English] …</d>`.
- Example (character swap): "(at 2.5 s) <Subject 1> (S1) sings along, <d>[English] hold me</d>, her eyes closed. (at 3.0 s) (S1) sings along, <d>[English] closer</d>, her mouth wide open."
- Fix `words.txt` from the face strip and the spectrogram: a first word stretched back to 0.00 s, a misheard word, a stock phrase on a clip where nobody sings (invented). Words after the render's end are dropped.
- With her words, keep the template's lip-sync sentence. Without them, drop it and audit with `--no-lip-sync`.

### Banned words
The audit reads these lists and names any word that fires; use other words ("pulls her arm back", not "drawn back"):
- drawing: `skeleton, keypoint, keypoints, guide, guides, drawn, drawing, dots, pose line, pose lines, drawn line, drawn lines, face marks, white marks`
- overlays: `sticker, stickers, overlay, overlays, caption, captions, speech bubble, speech bubbles, on-screen, card, cards`
- source wear: `corset, corsets, garter, garters, choker, chokers, stocking, stockings, pvc, latex, tattoo, tattoos, blouse, blouses, necklace, necklaces, pendant, pendants, bun, buns, ponytail, ponytails, updo, braid, braids, sneaker, sneakers, trainers, boot, boots, heels, sandals, shoes, socks, jeans, trousers, pants, sweatpants, joggers, leggings, shorts, hoodie, hoodies, sweater, sweaters, jumper, jumpers, cardigan, cardigans, jacket, jackets, coat, coats, t-shirt, t-shirts, tank top, tank tops, crop top, crop tops, sports bra, sports bras, bra, bras, bikini, bikinis, dress, dresses, earring, earrings, bracelet, bracelets, ring, rings, lanyard, lanyards, glove, gloves, glasses, sunglasses, hat, hats, scrunchie, scrunchies, hair tie, hair ties, belt, belts`
- Exempt from the source-wear list: the sheet's outfit text (`{OUTFIT}`, `{OUTFIT_LOCK}`) and, in a face swap, `{CLOTHES}`.
- The list can't be complete: outside `{CLOTHES}`, no word for anything the source woman wears (sleeve, zip, fabric, strap, logo, ring).

## Character-swap template

### Length
The audit's limit: 750 words + 150 per later shot + 45 per second past 3 s. Over it, shorten the sentences, never drop an anchor.

## Character-swap template
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

## Face-swap template
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
{STYLE} [Shot 1] <Subject 2>, with the face and hair of <Subject 1>, performs her own motion and expressions as shown in <Video 1>, frame by frame, in <Subject 3>: {SCENE}. {FRAMING} She wears {CLOTHES}. Her hair is {HAIR}. {MOVES} She lip-syncs the vocals in the original sound of <Video 1>, whether she speaks or sings; the soundtrack itself is unchanged. {CAMERA} Her face is sharp, natural and fully visible in every frame, lit by {LIGHT}, with real skin texture. The picture is clean, with no blur anywhere. One continuous shot with no cuts.

overall_soundscape:
The original sound of <Video 1>: {SOUND}.

non_diegetic_music:
N/A
```

**Two shots**, exactly what the audit builds (`template(task, 2)`):

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
<Subject 2> (throughout [Shot 1], [Shot 2]): partially_preserved - her body, clothes, jewellery, movement, gestures, expression timing, mouth movement, gaze, position and scale remain; only her face and hair are replaced by those of <Subject 1>.
<Subject 3> (throughout [Shot 1], [Shot 2]): fully_preserved - {KEPT}.
<Subject 1> (throughout [Shot 1], [Shot 2]): attribute_transfer - only her face and hair come from <Picture 1>, not from <Video 1>; her face's skin tone matches the neck and arms of <Subject 2>, never the colour of the blur.

detailed_description:
{STYLE} [Shot 1] <Subject 2>, with the face and hair of <Subject 1>, performs her own motion and expressions as shown in <Video 1>, frame by frame, in <Subject 3>: {SCENE}. {FRAMING} She wears {CLOTHES}. Her hair is {HAIR}. {MOVES} She lip-syncs the vocals in the original sound of <Video 1>, whether she speaks or sings; the soundtrack itself is unchanged. {CAMERA} [Shot 2] At {TIME_2}, the shot cuts to <Subject 2>, with the face and hair of <Subject 1>, in <Subject 3>: {SCENE_2}. {FRAMING_2} She wears {CLOTHES}. Her hair is {HAIR}. {MOVES_2} {CAMERA_2} Her face is sharp, natural and fully visible in every frame, lit by {LIGHT}, with real skin texture. The picture is clean, with no blur anywhere. It cuts only where <Video 1> cuts.

overall_soundscape:
The original sound of <Video 1>: {SOUND}.

non_diegetic_music:
N/A
```

**Several shots** (open: never rendered face-only; same rules as the character swap):
- Later shot: `[Shot {N}] At {TIME}, the shot cuts to <Subject 2>, with the face and hair of <Subject 1>, in <Subject 3>: {SCENE}. {FRAMING} She wears {CLOTHES}. Her hair is {HAIR}. {MOVES} {CAMERA}`
- Closing sentence: `One continuous shot with no cuts.` becomes `It cuts only where <Video 1> cuts.`

**No sound** (the only allowed changes): the summary prefix becomes `[video editing]`; the lip-sync sentence is dropped; ", with the original sound" is dropped; the `<Video 1>` retention line becomes "(shot length): partially_preserved - the shot length remains; the woman's face and hair and the blur are not kept."; write a new `overall_soundscape`.

## Run
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
- Another sheet: add `--set "Picture 1 · sheet.image=@/abs/her-sheet.png"`.
- Output: `<ComfyUI>/output/h3-ref2vid/swap_*.mp4`, with sound. A 3 s clip takes about 2 min on a 3090; longer clips take longer.
- Turned upright: `ffmpeg -nostdin -y -i <render> -vf transpose=<back> -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a copy <final>`.

**Several shots** render in one run. Only when that run fails (out of memory) or the user asks, render each shot on its own and join them. Each shot gets the shortest 17n+5-frame window that covers it (the last one reaches back instead of past the end), its own guide, and its own one-shot prompt with anchors from `(at 0.0 s)` (audit with `--seconds` = the window's length); the same seed and sheet. A colour match goes on each part before the join.
```bash
python3 - "$OUT/shots.txt" "$LEN" > "$OUT/windows.txt" <<'PYW'
import math, sys
end = float(sys.argv[2])
for line in open(sys.argv[1]):
    k, a, b = line.split(); a, b = float(a), float(b)
    seconds = (17 * math.ceil((round((b - a) * 24) - 5) / 17) + 5) / 24
    start = min(a, end - seconds)
    print(k, f"{start:.3f}", f"{seconds:.3f}", f"{a - start:.3f}", f"{b - a:.3f}")   # shot, window start, window length, shot offset, shot length
PYW
: > "$OUT/parts.txt"
while read -r k s w off len; do
  ffmpeg -nostdin -v error -y -ss "$s" -t "$w" -i "$CLIP" -c:v libx264 -crf 12 -pix_fmt yuv420p -c:a aac -ar 48000 "$OUT/win-$k.mp4"
  (cd "$CV" && .venv/bin/python -m cv_tools.motion_guide --input "$OUT/win-$k.mp4" --output "$OUT/wguide-$k" "${GUIDE[@]}")
  # write and audit $OUT/prompt-$k/prompt.txt for win-$k.mp4, then:
  R=$($RUN minimax-h3-reference-to-video --set "Video 1 · guide.video=@$OUT/wguide-$k/guide.mp4" \
      --set "Swap prompt.value=$(cat "$OUT/prompt-$k/prompt.txt")" --set "Seed.noise_seed=1001" 2>&1 | grep -E 'mp4$' | tail -1)
  ffmpeg -nostdin -v error -y -ss "$off" -t "$len" -i "$R" -an -c:v libx264 -crf 12 -pix_fmt yuv420p "$OUT/part-$k.mp4"
  echo "file '$OUT/part-$k.mp4'" >> "$OUT/parts.txt"
done < "$OUT/windows.txt"
ffmpeg -nostdin -v error -y -f concat -safe 0 -i "$OUT/parts.txt" -i "$CLIP" -map 0:v -map 1:a -c:v copy -c:a aac -shortest "$OUT/$NAME-joined.mp4"
```

## Check the result
1. `/history` of the run: the sheet is the one you meant.
2. Every 6th frame at full size: her face, both hands, no dots or lines painted on her. Character swap: the sheet's outfit (never nude), nothing of the source's clothes, hairstyle or accessories. Face swap: her own clothes, the character's hair.
3. She turns only where the clip turns.
4. A synced side by side with the clip, with sound: moves, mouth, timing, camera and cuts match.

| Symptom | Fix |
|---|---|
| Dots or lines painted on her | remove every word naming the drawing |
| She turns where the clip doesn't; the face goes soft | rewrite the moves from the frames; "she never turns" when she doesn't |
| Nude or outfit lost (character swap) | the outfit sentence in every shot |
| Redressed (face swap) | her clothes named exactly in `{CLOTHES}` |
| A mouth shape held for the whole video | write where it ends |
| The source's hairstyle or accessories back | `--mask-grow 0.05` |
| A phone painted in her hand | never name the phone |
| An invented camera move before a cut | the several-shots template with the cut time |
| Stickers or captions gone | accepted |

## Lessons (dated, evidence)
- 2026-11-24 · A one-second pout written with no end was held for the whole 11 s video; written with its end, it ended. Strong (the owner's rule).
- 2026-11-24 · On a clip where she doesn't sing, the lip-sync sentence made her sing on one render and not on another: the mouth lines decide. Medium.
- 2026-11-23 · H3 takes her timing from the moves: in prose a singing selfie ran 2 s ahead of the song; one anchored sentence every half second with her words at their times kept it on time (2 clips, the owner's pick). Medium.
- 2026-11-23 · A sideways, face-filling selfie with a plain blur guide came out as a generic upright portrait; turned upright with the colour guide, her pose and framing came back. Medium (2 clips).
- 2026-11-24 · A person mask grown 5 % pulled her hands toward her head; not grown is the default. Medium.
- 2026-11-23 · Face swap: clothes not named, H3 redressed her; named, they stayed. Strong.
- 2026-11-22 · One false move ("turns half away" where she never turns) turned her and softened her face on most seeds; the true line fixed it. Strong.
- 2026-11-19 · Character swap without the outfit sentence in every shot: nude. Strong.
- 2026-11-14 · Naming the drawing in any wording paints it on her. Strong.
- 2026-11-22 · Shot tags hold each shot's framing to its cut; prose invented a camera swing before it. Medium.
- 2026-11-13 · Long clips drift more: try another seed, never cut the clip. Medium.
- Open: stickers and captions vanish in the redraw; in a face swap the source's pulled-back hairstyle can stay (try `--mask-grow 0.05`).
