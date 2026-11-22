---
name: prompt-writing
description: How to write prompts for the image/video models (MiniMax H3 video so far), organised by task (character swap, …) with one subsection per model. Use EVERY time you write, rewrite, review or audit a prompt for a generation or edit run, or brief an LLM/agent to write one. Each task/model subsection has a template, a pre-render checklist, a symptom→fix fallback table with evidence strength, and failed→fixed examples from real runs.
---

# Prompt writing

## Rules for every task and model
1. **Read the model's official prompt guide first** and write in its format (`models/<model>.md`, plus the official guide linked in `references/README.md`).
2. **Describe what is in the source, never what you hope to see fixed.** Per-clip text comes from looking at frames grabbed by index.
3. **Fix failures in the template, not in one clip's text.** A fix that only works for one clip is overfitting.
4. **Never ask the model to keep something drawn on the input** (stickers, captions, overlays). Guide-conditioned models can't tell those from the guides. Paste graphics back afterwards.
5. **Never name what you are removing.** Describe only the new thing.
6. **The orchestrator audits, not the writer.** Run the task's checklist and script on every prompt, put it verbatim on the review page, and do a short render before a full one.
7. **Every claim carries its evidence:** the run ids, and whether it is strong, medium, weak or open. Don't present one run as a law.

## Tasks
| Task | File | Models covered |
|---|---|---|
| Character swap in a video (a character from her sheet replaces the whole person; motion from the source) | `tasks/character-swap.md` | MiniMax H3 video (Singularity + Pika): blur + drawn pose, never a ControlNet |
| Face-only swap in a video (the character's face and hair; the source person's body and clothes stay). **Only with the on-screen person's consent** | `tasks/face-swap.md` | MiniMax H3 video (Singularity + Pika): face + hair blurred, pose drawn |

Add a task as `tasks/<task>.md`, laid out as: goal → rules for the task on any model → one subsection per model containing inputs, workflow, template, checklist, fallback table and failed→fixed examples.

## Models (the common format, shared by every task)
| Model | File |
|---|---|
| MiniMax H3 | `models/minimax-h3.md`, plus the official guide (linked in `references/README.md`) and `references/h3-singularity-spec.md` (community, Apache-2.0) |

## Scripts
- `scripts/h3_audit.py <dir>`: checks the checklist and that the fixed template text is copied word for word, on every `.txt` prompt in `<dir>`. A prompt whose `<Subject 1>` says "only her face, identity and hair" is checked against the face-swap template, any other against the character-swap one. One shot must carry no timestamp; several shots must follow the task's multi-shot variant (`[Shot 1]` bare, `[Shot N] At MM:SS.mmm,` increasing). Exits 1 if any check fails. `template(task, shots)` builds the template for any shot count.
- `python -m cv_tools.shots --input <clip> --output <dir>` ([cv-tools](https://github.com/FrancescoSaverioZuppichini/cv-tools)): the shots of a clip as `shots.json` (start/end frame, `MM:SS.mmm`) plus one frame strip per shot. Run it first and write the prompt from the strips: one shot, no timestamps; several, the multi-shot variant.
- A tool that writes prompts automatically (we use a ComfyUI node) should import `template()` and `audit()` from here instead of copying the template text, and fail on any audit miss.
