---
name: comfyui-workflow-edit
description: Use EVERY time you create or edit a ComfyUI workflow file (UI JSON in ComfyUI/user/default/workflows) by script — adding/moving nodes, groups, layout, wiring. Enforces a strict layout (by-eye review) (two-row group layout, short titles, real node sizes, no overlaps, previews inside their group, optional groups yellow) and the open-tab rule, and runs scripts/check_layout.py before handing anything over.
---

# Editing ComfyUI workflows by script

The user reviews workflows by eye. Every layout mistake costs a round trip. Follow all of this, every time.

## Before writing

1. **The open tab overwrites you.** ComfyUI's tab autosaves its own copy over the file. Ask the user to close the tab with "Don't save" before you write, and to reopen it after. Never write a file that's open in their tab.
2. **Edit in place.** Modify the workflow the user named. Never create a copy or a new variant unless asked (then use the name given, e.g. `-nag`, `-test`). No `.before-*` backup files per edit.
3. **Copy node JSON from a working workflow** (inputs with `widget`, outputs, `properties`, `widgets_values` order) instead of inventing it — e.g. `qwen-character-swap.json`, `remove-anything.json`. Check inputs/outputs with `curl localhost:8188/object_info/<NodeClass>`.

## Layout rules

- **Short titles, ≤ 25 characters.** ComfyUI widens a node to fit its title, so long titles push nodes under their neighbours. Explanations go in a MarkdownNote READ ME.
- **`pos` is the top of the node body; the ~32 px title bar is drawn above it.** Vertical stacking: next `y = y + rendered height + 100` (= 60 px clear + the next title bar). `+70` only leaves 38 px and looks crammed — that was the recurring mistake.
- **Realistic sizes:** loaders ~90, CLIP loader ~120, LoRA loader ~230, KSampler ~270, multiline prompt ~300, LoadImage with preview ~560–700, SaveImage / Image Comparer / Preview 480×700, widget-heavy custom nodes 150–420.
- **Columns ≥ 150 px apart** (use 440-wide nodes on a 560/600-px grid; 480-wide previews on a 640 grid).
- **Every node inside a group's bounding box; groups never overlap.**
- **Two rows of groups**, left to right in the order the picture flows:
  - Row 1 (y 0, height 1390): READ ME → 1 · MODELS → 2 · INPUTS → 3 · PROMPT → 4 · CAMERA/EXPRESSION → the main arm (sampling) → **5 · OUTPUT**, which grows to the right (saves + comparers side by side).
  - Row 2 (y 1520, height 1450): control arm, then the OPTIONAL stages (SeedVR2, phone finish, relight…).
- **A stage's preview/comparer lives in that stage's group, next to it** (e.g. "Relight vs raw" inside the RELIGHT group). OUTPUT holds the main saves and the raw-vs-reference comparer.
- **Colours: blue `#3f789e` = the main path** (models, inputs, prompt, camera, the main sampling arm, output). **Yellow `#b58b2a` = everything secondary**: control arms (e.g. arm A "text only"), OPTIONAL stages (SeedVR2, phone finish, relight, auto-mask…). READ ME stays blue.
- **Gaps, not just "no overlap":** ≥ 60 px between stacked nodes (bottom of one body to the top of the next title bar) and ≥ 120 px between nodes side by side. The checker enforces both.
- **Optional = bypassable**: a bypassed node must pass its input through (same type in/out) or the graph breaks; nodes without a matching input (e.g. a text encoder, a detector) need a switch/fallback instead.

## After writing — mandatory

Run the checker on the machine that holds the workflows and fix until it prints `OK`:

```bash
python3 scripts/check_layout.py "<ComfyUI>/user/default/workflows/<file>.json"
```

It checks: node overlaps (title bar included), nodes outside every group, group overlaps, titles > 25 chars, dangling links. Then tell the user to close the tab without saving and reopen. Say plainly what changed; if you could not look at it rendered, say so.
