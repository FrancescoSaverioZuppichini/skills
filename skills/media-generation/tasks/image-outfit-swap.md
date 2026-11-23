# Task: outfit swap (dress a person or a character sheet)

**Goal:** the person in a picture wears the outfit from another picture; face, pose, body and background stay. The common use is dressing the character sheet before a video swap (`video-character-swap`, step 0). Model: `models/qwen-image-edit.md`. Workflow: `qwen-outfit-swap`.

## Ask if unsure
- Which picture to dress? For a video swap, the undressed body sheet.
- Which outfit picture? Is it a person wearing it, or the garment alone?
- Only the outfit, or the shoes and accessories too?

## Inputs
| Node | Set |
|---|---|
| `Image 1 · the picture to dress (the canvas)` | the picture or the body sheet |
| `Image 2 · the outfit picture` | the outfit |
| `SAM 3 prompt · what to keep from the outfit picture` | `text`: what to cut out of Image 2, e.g. `woman` (a worn outfit) or `dress` |
| `Instruction (B) · what Luna turns into the prompt` | the edit in one or two plain sentences (default: replace the clothes in `<image1>` with the outfit from `<image2>`) |
| `Seed` | `-1` = random |

**You write at most the instruction.** The enhancer group (3b, GPT-6 Luna through OpenRouter, needs the key in comfyui-nodes' `.env`) turns it into the final prompt from both pictures. Image 1 is scaled to 1 MP.

## Run
```bash
$RUN qwen-outfit-swap \
  --set "Image 1 · the picture to dress (the canvas).image=@sheet.png" \
  --set "Image 2 · the outfit picture.image=@outfit.jpg"
```
Output: `Save (with metadata)`. Turn on `8 · PHONE FINISH (optional)` only for finals, never for a sheet.

## Check
- **The outfit matches the picture:** cut, colour, material and length.
- **The face, body and pose of Image 1 are unchanged.**
- **For a sheet:** front and back are both dressed, consistently. Then write the sheet's new `{OUTFIT}` and `{OUTFIT_LOCK}` lines for the video template.

## Lessons
- 2026-11-17 · Video swaps take only Qwen-dressed sheets; a sheet dressed by H3 is banned. Strong (rule).
- 2026-11-19 · The video prompt must lock the new outfit in every shot ("She wears the outfit of `<Subject 1>` in every frame: …"), or the render can come out nude. Strong.
