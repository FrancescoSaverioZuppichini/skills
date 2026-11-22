---
name: comfyui-workflow
description: Use EVERY time you make, edit or run a ComfyUI workflow (the UI JSON in ComfyUI/user/default/workflows): adding or moving nodes and groups, wiring, layout, naming, sizes, optional stages, or running a saved workflow from code. Holds the naming convention, the layout rules, the open-tab rule, the layout checker and the runner.
---

# ComfyUI workflows: make, edit, run

`<skill>` below is this skill's folder; the scripts are `<skill>/scripts/check_layout.py` and `<skill>/scripts/run_workflow.py`.

## Rules
1. **One workflow per task, named `<model>-<task>`,** lowercase with hyphens.
   - `<model>`: the model as it's published, version included (`minimax-h3`, `qwen`, `krea2`, `seedvr2`, `qwen3`).
   - `<task>`: full words, no abbreviations: `reference-to-video`, `text-to-image`, `character-swap`, `outfit-swap`, `remove-anything`, `upscale`, `text-to-speech`, `censor`.
   - The same task on a different model is a different workflow. No `-test`, `-v2`, `-researching` or temp copies: change the task's one workflow in place.
2. **Delete what isn't used.** No archive folders, no `.bak` files: keep the workflows folder in git, and git is the backup.
3. **Close the tab before writing an existing file.** An open ComfyUI tab autosaves its own copy over the file, and you can't see from outside whether it's open. So ask the user to close it with "Don't save", wait for their yes, write, then tell them to reopen it. If they can't answer, don't write. Creating a new file, reading, `--list`, `--check` and runs are safe.
4. **Copy node JSON, never invent it.** Take a node's shape (inputs with `widget`, outputs, `properties`, `widgets_values` order) from a working workflow, or from `curl <server>/object_info/<NodeClass>`.
5. **No hand-typed sizes.** One size node feeds every width/height: from the source image or clip when the workflow copies one, otherwise a ratio + megapixels (ComfyUI core: `ResolutionSelector`; a custom size node can also read a source's shape).
6. **Optional stages switch off cleanly.** One toggle per optional group. Off must leave exactly the main graph: use a switch (core `If/Else`), or nodes that pass their input through when bypassed (same type in and out). A text encoder or a detector can't pass through, so it needs a switch.
7. **A READ ME note in every workflow:** what it does, the inputs the user sets, the modes, measured times. Long explanations go there, never into node titles.

## Layout
- **Two rows of groups,** left to right in the order the data flows (y = the group's top edge):
  - Row 1, the main path (y 0): READ ME → MODELS → INPUTS → PROMPT → the main stages → OUTPUT (saves and comparers side by side, growing right).
  - Row 2, the optional stages (y ≈ 1520, below row 1's tallest group plus a gap).
- **A stage's preview or comparer sits inside that stage's group.**
- **Colours:** blue `#3f789e` for the main path and the READ ME; yellow `#b58b2a` for optional stages and control arms.
- **Every node inside a group; groups never overlap.**
- **Titles ≤ 25 characters.** ComfyUI widens a node to fit its title. Distinct titles: the runner finds inputs by title.
- **`pos` is the top of the node body;** the 32 px title bar is drawn above it.
  - Stacked: the checker wants ≥ 60 px between one body's bottom and the next title bar, so place the next node at `y + height + 100`.
  - Side by side: ≥ 120 px between nodes; 440-wide nodes on a 560–600 px grid.
- **Typical heights,** as a starting point (the checker uses each node's stored `size`): loader ~90, CLIP loader ~120, LoRA loader ~230, sampler ~270, multiline prompt ~300, image loader with preview 560–700, save or preview 480×700.

**After every write,** run the checker until it prints `OK`. It exits 1 on any problem. It checks overlaps (title bar included), nodes outside groups, group overlaps, long titles and dangling links. It does **not** check colours or the READ ME: look at those yourself.

```bash
python3 <skill>/scripts/check_layout.py <ComfyUI>/user/default/workflows/<name>.json
```

## Run a workflow from code
ComfyUI runs graphs in **API format** (a flat map of nodes and inputs), not the saved UI file. The runner converts the saved workflow on the fly, so code runs exactly what's in the Workflows menu.

1. **Server up?** `curl -s <server>/system_stats`. The server defaults to `http://127.0.0.1:8188` (or `$COMFYUI_URL`, or `--server`).
2. **See the inputs:** `python3 <skill>/scripts/run_workflow.py <name> --list`. It prints every node title, its settable inputs with their current values, and each group's state. Nodes inside a subgraph show as `Subgraph / Node`.
3. **Run it** with your changes, using the titles and inputs `--list` showed:
   ```bash
   python3 <skill>/scripts/run_workflow.py <name> \
     --set "Seed.seed=1234" \
     --set "Load Image.image=@/path/to/my.png" \
     --group "Upscale=off"
   ```
   It prints each output file, the wall time and any random seed it drew. It exits non-zero on a validation error.

**Options:**
- `--set "<title>.<input>=<value>"`: repeat as needed. Values are JSON when they parse (`7`, `true`, `"x"`). `@<local file>` uploads the file to the server's input folder and sets its name (loader inputs only; skipped by `--dry` and `--list`).
- `--group "<title>=on|off|mute"`: `off` bypasses the group's nodes (inputs pass through), `mute` stops them.
- `--dry`: prints the API prompt instead of running it.
- `--check`: converts and validates with ComfyUI's own validator on the CPU, with no server and no GPU. Run it with that install's Python: `<ComfyUI>/.venv/bin/python <skill>/scripts/run_workflow.py all --check --comfyui <ComfyUI>`. It reads the workflows from `<ComfyUI>/user/default/workflows` (default `--comfyui`: `$COMFYUI_DIR`, then `~/ComfyUI`). `all`, or several names, works only with `--check`.

A normal run reads the workflow from the server's Workflows menu, or from a `.json` path, and needs the server either way.
