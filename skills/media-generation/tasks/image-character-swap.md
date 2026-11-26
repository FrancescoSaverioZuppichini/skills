# Task: character swap in a photo

**Goal:** the character becomes the whole person in a photo (face, hair, body build); the photo's pose, room, light and framing stay. Model: `models/qwen-image-edit.md`. Workflow: `qwen-character-swap` (Qwen Image 2.1 UC + the BFS body-swap LoRA).

## Ask if unsure
- Which character sheet? Default: the body sheet (it carries her body shape; a must) plus her head picture.
- Her clothes, or the photo's? Default: the sheet's.
- Phone finish on? Default: yes for anything that goes out.

## Inputs
| Node | Set |
|---|---|
| `Image 1 · the photo (the scene and pose to keep)` | the photo |
| `Image 2 · the character's character sheet (the WHOLE sheet, uncut)` | the whole sheet, never cropped |
| `Image 3 · the character's face (head only: no clothes for Qwen to copy)` | her head picture |
| `Clothes · off = from the character sheet · on = keep the photo's` | `switch`: `false` = the sheet's clothes, `true` = the photo's |
| `Seed` | `-1` = random |

**You write nothing.** Both prompts are fixed, and the clothes switch picks one. Sizes follow the photo (2 MP; the face at 0.59 MP).

## Run
```bash
$RUN qwen-character-swap \
  --set "Image 1 · the photo (the scene and pose to keep).image=@photo.jpg" \
  --set "Clothes · off = from the character sheet · on = keep the photo's.switch=false" \
  --group "OPTIONAL · PHONE FINISH=on"
```
Output: `output/char-swap/swap` (raw) and a JPEG with iPhone EXIF in `output/char-swap/phone` (phone-finished when that group is on).

## Check
- **It's her:** the face, hair colour (medium chestnut-brown), eyes (warm brown).
- **The source woman is gone:** no trace of her face or body.
- **The photo's pose, room and light are kept.**
- **Teeth showing ⇒ she has orthodontic dental braces.** If they're missing, run the braces fix (lessons below).
- **A B&W source photo ⇒ the whole swap goes grey** (no relight).

## Lessons
- 2026-11-04 · This exact setup (BFS body-swap LoRA, Qwen 2.1 UC) was voted "perfect". Strong.
- 2026-11-05 · Keeping the photo's clothes needs the clothes-first wording (the second prompt): kept 8/8 vs 0/8. Strong.
- 2026-11-05 · Phone finish (sharpen + iPhone grain + JPEG 95) is a must on every final; the raw swap looks airbrushed. Never on LoRA training images (2026-11-11). Strong.
- 2026-11-06 · Braces: a face-detail edit (face crop ×2 → Qwen edit with the canonical mouth picture, "change only the teeth", "orthodontic dental braces") → relight → phone finish. Strong.
- 2026-11-21 · Lowering the denoise to keep pose or texture: dead. Strong.
- 2026-11-03 · Never a head or face swap on a real person: the whole person or nothing. Rule.
