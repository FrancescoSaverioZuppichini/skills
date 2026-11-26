# Task: remove anything from a photo

**Goal:** remove things from a photo (overlaid text, watermarks, logos, tattoos, jewellery, piercings, or what you name) and keep everything else. Model: `models/qwen-image-edit.md`. Workflow: `qwen-remove-anything` (Qwen Image 2.1 UC).

## Ask if unsure
- Remove what? The default prompt covers text, watermarks, logos, stamps, tattoos, jewellery and piercings.
- The whole picture, or only a painted area?

## Inputs
| Node | Set |
|---|---|
| `1 · Picture + mask` | the photo. Paint a mask in ComfyUI's mask editor to limit the edit to an area; no mask = the whole picture |
| `Prompt · mine` | your own removal instruction (leave empty to use `Prompt · default`) |
| `Which prompt` | which of the two is used |
| `Person` | the character's hair and eyes line (`long straight medium chestnut-brown hair, warm brown eyes`); the workflow appends "make her hair and eyes match this description" |

**You write nothing** for the default removal. Write only `Prompt · mine` when you remove something else: "Edit `<image1>`: remove …". Here naming the things to remove IS the task.

## Run
```bash
$RUN qwen-remove-anything --set "1 · Picture + mask.image=@photo.png"
```
Output: `output/remove-anything/clean`, and a JPEG with iPhone EXIF in `output/remove-anything/phone`. The edit is cropped around the mask at 2 MP and stitched back.

## Check
- **Every target is gone,** with no ghost outline.
- **Skin, background and the face are unchanged elsewhere.**
- **Hair and eyes match the `Person` line.**

## Lessons
- 2026-11-09 · Hair is medium chestnut-brown, not black. A wrong colour word made Qwen far too dark. Keep the `Person` text identical to the persona file. Strong.
