# Task: clone a reference image's vibe

**Goal:** a new photo of the character that copies a **reference image's look**: its pose, framing and camera, light, colour, place and mood. Only the person changes: she becomes the character. The reference is a template for the look, never a person to copy. Model: `models/krea2.md`. Workflow: `krea2-clone-vibe` (Krea 2 + the character's LoRA).

## How it works
- **The reference goes in twice:**
  - **A vision model reads it** (group `OPTIONAL · PHOTO IN THE VLM`, on) and writes the scene part of the prompt: place, light, camera, pose, outfit.
  - **A half-noise copy of it** is attended to by the image tokens at the same positions during the first steps (group `C · HALF-NOISE COPY (N4)`, always on). That's what keeps the pose and limbs.
- **The character comes from her LoRA** plus the persona line.
- **Kept:** pose, framing, camera, light, place, outfit, mood. **Changed:** the person (face, hair, body), and the details the model redraws.

## Ask if unsure
- Which reference image?
- The reference's outfit, or a different one? Default: the reference's.

## Inputs
| Node | Set |
|---|---|
| `Reference photo` | the reference image |
| `PROMPT` | **the only thing you write, and only if it changes:** the persona line ("She is a 21-year-old woman with long straight medium chestnut-brown hair, warm brown eyes, a petite, slender build…"). Keep it as saved for the character |
| `Seed` | a fixed seed for comparisons, `-1` otherwise |

Size follows the reference (2 MP).

## Run
```bash
$RUN krea2-clone-vibe --set "Reference photo.image=@reference.jpg"
```
Output: `Save final` and `Save raw`; `Save phone finish` (the phone finish group is on).

## Check
- **Next to the reference:** same pose, framing, light and place.
- **It's her:** face, hair colour, eyes.
- **None of the reference person's face remains.**

## Lessons
- 2026-11-12 · Always with the photo in the vision model AND N4: the vision-model-only renders changed the outfit and camera. Only `*_vibe_cloned*` renders are candidates. Strong.
- 2026-11-08 · Pose comes only from N4 (position-matched attention to a half-noise copy). It brings back some of the reference's hair colour and light on close-ups. Medium.
- 2026-11-07 · No NAG or negative prompt: a no-op at CFG 1. Strong.
- 2026-11-06 · Relight (optional group) is judged only side by side with the reference: original | relight. Strong.
