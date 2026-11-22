# Task: an image from text

**Goal:** a new photo of the character from a scene description. Model: `models/krea2.md` (examples there). Workflow: `krea2-text-to-image` (Krea 2 Turbo int8 + the character's LoRA).

## Ask if unsure
- The character (her LoRA is on by default), or no character?
- Portrait or landscape? Default: 3:4 portrait.
- Finals: phone finish on?

## Inputs
| Node | Set |
|---|---|
| `PROMPT · scene` | **you write this:** the scene in Krea 2's style (subject → action → setting → light → camera → finish), as in `models/krea2.md` |
| `Size` | default ratio + MP: 3:4 · 1.69 MP = 1152×1536 (~1.7 MP) |
| `Seed` | `-1` = random |
| `LoRAs` | the character's LoRA row is on; realism LoRAs are optional rows |

The `Final prompt` node adds the LoRA trigger, the identity line and the optional camera and expression presets (group `4 · CAMERA + EXPRESSION`).

## Run
```bash
$RUN krea2-text-to-image --set "PROMPT · scene.value=An amateur iPhone flash photograph of a young woman …" --set "Seed.seed=-1"
```
Output: `Save` (and `Save 2×` with `OPTIONAL · SEEDVR2 2×`). Add `--group "OPTIONAL · PHONE FINISH=on"` for finals; turn on the face or hand refine groups only when the face or hands are small or broken.

## Check
- **It's her** (face, hair, eyes), and the scene matches the prompt.
- **Hands and face at full size.**

## Lessons
- 2026-11-07 · No negative prompt or NAG on Krea 2: both do nothing at CFG 1. Strong.
- 2026-11-22 · Default size ~1.7 MP (1152×1536). The old saved file rendered 4096×4096 by mistake. Rule.
