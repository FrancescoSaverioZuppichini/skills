# Task: face-only swap in a video

**Goal:** the character's face and hair replace the source woman's face and hair. Her body, clothes, jewellery, motion, expression timing, scene and camera stay the source's.

**Only when the user asks for it, and only with the consent of the person on screen.** It keeps a real person's body and puts another face on it. The default for every swap is the whole person (`video-character-swap.md`); never propose this route.

**Model:** MiniMax H3 (`models/minimax-h3.md`). Everything in `video-character-swap.md` applies unless this file says otherwise: the steps, "Writing the slots", the banned words, the checks.

## Before you start: ask if unsure
- Did the user ask for a face-only swap, and does the person on screen consent?
- Which clip, and which part (whole clip by default)?
- Which character sheet? Default: the dressed sheet the workflow loads.
- Keep the clip's sound? Default yes.
- Which seed(s)? Show the inputs before the render?

## What differs from the character swap
| | Character swap | Face only |
|---|---|---|
| Guide mask | the whole woman: `--mask-prompt person --mask-grow 0.05` | `--mask-prompt "head, hair" --mask-grow 0.02` |
| Visible in `<Video 1>` | nothing of her | her body, skin, clothes and jewellery |
| `<Subject 1>` | face, identity, hair, body shape, outfit | only her face, identity and hair |
| `<Subject 2>` | her performance only | the woman herself: body, clothes, jewellery and performance |
| Outfit sentence | in every shot | never |
| Template | the character-swap template | the face-only template below |

## Rules for this task
- **Hide only her face and hair.** The model keeps what it can see, so her clothes stay.
- **Never name her clothes, jewellery or hair.** "She stays dressed exactly as in `<Video 1>`" carries them (kept on 6 of 6 renders; naming them was never tested).
- **No outfit sentence**: it would dress her in the sheet's outfit.
- **Face and hair only:** her body shape is not named, because the body stays the source's.

## Steps
1–4 as in `video-character-swap.md` (the part to render, shots, close-ups, sound).
5. Guide: SAM 3 runs "head" and "hair" as two text prompts and pools both masks; skeleton and eyebrow + mouth dots are drawn on top. Free ComfyUI's GPU memory first (one build ran out of memory while ComfyUI held 18.5 GB).
   ```bash
   (cd "$CV" && .venv/bin/python -m cv_tools.motion_guide --input "$CLIP" --output "$OUT/guide" --mask-prompt "head, hair" --mask-grow 0.02)
   cp "$OUT/guide/guide.mp4" "$OUT/$NAME-guide.mp4"
   ```
6. Write the whole prompt from the template below into `$OUT/prompts/face.txt`, slots per "Writing the slots" in `video-character-swap.md`, with these changes: `{FACE_LINE}` is the per-sheet value below; there is no `{OUTFIT}`, `{CHARACTER_LINE}` or `{OUTFIT_LOCK}`; `{FRAMING}` may say which part of her body shows ("so her chest and shoulders show"), never what she wears. Shots exactly as in the character swap: one shot = no timestamps; N shots = one later-shot block each, `{TIME_k}` = shot k's `start` in `shots.json`.
7. Audit (it picks this template from "only her face, identity and hair"), then check the moves against the strips:
   ```bash
   python3 "$SKILL/scripts/h3_audit.py" "$OUT/prompts" --seconds "$SECONDS"
   ```

## Per-sheet value
- `{FACE_LINE}`: `She is a 21-year-old woman with long straight medium chestnut-brown hair and warm brown eyes.`

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
{STYLE} [Shot 1] <Subject 2>, with the face and hair of <Subject 1>, performs her own motion and expressions as shown in <Video 1>, frame by frame, in <Subject 3>: {SCENE}. {FRAMING} {MOVES} {CAMERA} [Shot 2] At {TIME_2}, the shot cuts to <Subject 2>, with the face and hair of <Subject 1>, in <Subject 3>: {SCENE_2}. {FRAMING_2} {MOVES_2} {CAMERA_2} Her face is sharp, natural and fully visible in every frame, lit by {LIGHT}, with real skin texture. The picture is clean, with no blur anywhere. It cuts only where <Video 1> cuts.

overall_soundscape:
The original sound of <Video 1>: {SOUND}.

non_diegetic_music:
N/A
```

**Several shots** (open: never rendered face-only; same rules as the character swap):
- Later shot: `[Shot {N}] At {TIME}, the shot cuts to <Subject 2>, with the face and hair of <Subject 1>, in <Subject 3>: {SCENE}. {FRAMING} {MOVES} {CAMERA}`
- Closing sentence: `One continuous shot with no cuts.` becomes `It cuts only where <Video 1> cuts.`

**No sound** (the only allowed changes): the summary prefix becomes `[video editing]`; ", with the original sound" is dropped; the `<Video 1>` retention line becomes "(shot length): partially_preserved - the shot length remains; the woman's face and hair and the blur are not kept."; write a new `overall_soundscape`.

## Run
The same workflow and toggles as the character swap; only the prompt in `Swap prompt` differs. Same size, time and output.

```bash
$RUN minimax-h3-reference-to-video \
  --set "Video 1 · guide.video=@$OUT/$NAME-guide.mp4" \
  --set "Swap prompt.value=$(cat "$OUT/prompts/face.txt")" \
  --set "Seed.noise_seed=1001" \
  --set "REFINE on / off.value=false"
```

## Check the result
The character swap's checks, then on a synced side by side with the source: her clothes match the source, and her hair is the character's, not the source's hairstyle.

## Lessons (dated, evidence)
- 2026-11-17 · Six clips × 1 seed (3.75 s, 551–690-word prompts on this template): the character's face and hair with the source's own clothes on 6 of 6; one clip kept the source's pulled-back hairstyle. Judged by the agent that ran them; no person rated them. Medium.
- 2026-11-17 · Those runs used the undressed body sheet; the dressed sheet (the user's call, 2026-11-19) has no face-only render yet. Open.
- Source hairstyle stays (pulled back, bun): the character swap fixed it with a wider blur (`--mask-grow 0.05`); not tried here. Open.
- Stickers and captions disappear in the redraw. Open, accepted.
