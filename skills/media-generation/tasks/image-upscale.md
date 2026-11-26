# Task: upscale an image

**Goal:** a sharper image ×2 or ×4 with the same content. Workflow: `seedvr2-upsample` (SeedVR2 7B sharp, one restore step, colour fix). No prompt.

## Ask if unsure
- ×2 or ×4? Default: ×2.

## Inputs
| Node | Set |
|---|---|
| `Image to upscale` | the image |
| `Scale (2 or 4) · lanczos stretch` | `resize_type.multiplier`: `2` or `4` |

## Run
```bash
$RUN seedvr2-upsample --set "Image to upscale.image=@in.png" --set "Scale (2 or 4) · lanczos stretch.resize_type.multiplier=2"
```
Output: `output/seedvr2-upsample/out`, and a JPEG with iPhone EXIF in `output/seedvr2-upsample/phone`.

## Check
- **Same face and details,** sharper.
- **Colours unchanged** (the lab colour fix is on).
- **No invented texture on skin.**

## Lessons
- 2026-11-21 · The character-sheet build uses this workflow as saved, for its ×2 step. Rule.
