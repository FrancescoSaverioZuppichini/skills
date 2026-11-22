---
name: comfyui-workflow
description: Use EVERY time you make, edit or run a ComfyUI workflow (the UI JSON in ComfyUI/user/default/workflows): adding or moving nodes and groups, wiring, layout, naming, sizes, optional stages, or running a saved workflow from code. Holds the naming convention, the layout rules, the open-tab rule, the layout checker (scripts/check_layout.py) and the runner (scripts/run_workflow.py).
---

# ComfyUI workflows: make, edit, run

## Rules
1. **One workflow per task, named `<model>-<task>`:** lowercase, hyphens, full words, no abbreviations (`minimax-h3-reference-to-video`, `qwen-character-swap`, `krea2-text-to-image`). No `-test`, `-researching`, `-v2` or temp copies. Change the task's one workflow in place.
2. **Delete what isn't used.** No archive folders, no `.bak` files: git is the backup.
3. **Close the tab first.** An open ComfyUI tab autosaves its own copy over the file. Ask the user to close it with "Don't save" before you write, and to reopen it after. Never write a file that's open in a tab.
4. **Copy node JSON, never invent it.** Take a node's shape (inputs with `widget`, outputs, `properties`, `widgets_values` order) from a working workflow, or read it from `curl <server>/object_info/<NodeClass>`.
5. **No hand-typed sizes.** One size node feeds every width/height: from the source image or clip when the workflow copies one, otherwise a ratio + megapixels. (Our pack's `Size` node does both; ComfyUI core's `ResolutionSelector` does ratio + megapixels only.)
6. **Optional stages switch off cleanly.** One toggle per optional group. Off must leave exactly the main graph: use a switch (core If/Else) or nodes whose input passes through when bypassed. A text encoder or a detector has no pass-through, so it needs a switch.
7. **A READ ME note in every workflow:** what it does, its inputs, its modes and measured times. Long explanations go there, never into node titles.

## Layout
- **Two rows of groups,** left to right in the order the data flows:
  - Row 1, the main path (y 0): READ ME → MODELS → INPUTS → PROMPT → the main stages → OUTPUT (saves and comparers side by side, growing right).
  - Row 2, the optional stages (y ≈ 1520).
- **A stage's preview or comparer sits inside that stage's group.**
- **Colours:** blue `#3f789e` for the main path and the READ ME; yellow `#b58b2a` for optional stages and control arms.
- **Every node inside a group; groups never overlap.**
- **Titles ≤ 25 characters.** ComfyUI widens a node to fit its title.
- **`pos` is the top of the node body;** the ~32 px title bar is drawn above it.
  - Stack with `next y = y + rendered height + 100` (60 px clear plus the next title bar).
  - Leave ≥ 120 px between nodes side by side; columns ≥ 150 px apart (440-wide nodes on a 560–600 px grid).
- **Typical heights:** loader ~90, CLIP loader ~120, LoRA loader ~230, sampler ~270, multiline prompt ~300, image loader with preview 560–700, save or preview 480×700.

**After every write,** run the checker until it prints `OK`. It checks overlaps (title bar included), nodes outside groups, group overlaps, long titles and dangling links.

```bash
python3 scripts/check_layout.py "<ComfyUI>/user/default/workflows/<name>.json"
```

Say plainly what changed, and that the user should reopen the tab.

## Run a workflow from code
ComfyUI runs graphs in **API format** (a flat map of nodes and inputs), not the UI file. `scripts/run_workflow.py` converts the saved UI workflow on the fly with the server's `/object_info`, so code runs exactly what's in the menu.

```bash
python3 scripts/run_workflow.py <workflow name or path.json> \
  --set "<node title>.<input>=<value>" ...     # repeat per input; values are JSON when they parse (7, true, "x")
  [--server http://127.0.0.1:8188]             # default
  [--dry]                                      # print the API prompt instead of running it
```

- It posts `/prompt`, waits on `/history/<prompt_id>`, and prints every output file and the wall time.
- Find inputs by node **title** (what the UI shows). Give nodes distinct titles.
- Under the hood: `POST /prompt {"prompt": <api graph>}` returns a `prompt_id`; `GET /history/<id>` holds the outputs when it's done; the `/ws` websocket streams progress. In the UI, **Workflow → Export (API)** gives the same API graph by hand.
