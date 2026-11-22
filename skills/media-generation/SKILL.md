---
name: media-generation
description: Use EVERY time you make an image, video or voice with the lab's ComfyUI workflows, or write, review or audit a prompt for one: character swap in a video or a photo, face swap, outfit swap, remove anything from a photo, text to image, clone a reference image's vibe, character sheet, upscale, censor, text to speech. Each task says which workflow, which inputs, what to write, the run command, how to check the result and the lessons we paid for; each model says how to prompt it.
---

# Media generation

## Pick your task
| You want | Task file | Workflow | Model |
|---|---|---|---|
| A character replaces the whole person in a video | `tasks/video-character-swap.md` | `minimax-h3-reference-to-video` | `models/minimax-h3.md` |
| Only the face and hair in a video (on request, with consent) | `tasks/video-face-swap.md` | `minimax-h3-reference-to-video` | `models/minimax-h3.md` |
| A character replaces the whole person in a photo | `tasks/image-character-swap.md` | `qwen-character-swap` | `models/qwen-image-edit.md` |
| Dress a person or a character sheet in an outfit from a picture | `tasks/image-outfit-swap.md` | `qwen-outfit-swap` | `models/qwen-image-edit.md` |
| Remove text, logos, tattoos, jewellery or anything else from a photo | `tasks/image-remove-anything.md` | `qwen-remove-anything` | `models/qwen-image-edit.md` |
| Build a character sheet (front, back, head) | `tasks/image-character-sheet.md` | `qwen-character-sheet-build` + `seedvr2-upsample` | `models/qwen-image-edit.md` |
| An image from a text description | `tasks/image-text-to-image.md` | `krea2-text-to-image` | `models/krea2.md` |
| A new image with a reference photo's look, the character in it | `tasks/image-clone-vibe.md` | `krea2-clone-vibe` | `models/krea2.md` |
| Upscale an image ×2 or ×4 | `tasks/image-upscale.md` | `seedvr2-upsample` | no prompt |
| Censor nudity in an image | `tasks/image-censor.md` | `nudenet-censor` | no prompt |
| Speech from text in a cloned voice | `tasks/speech-text-to-speech.md` | `qwen3-text-to-speech` | `models/qwen3-tts.md` |

Workflows live in ComfyUI's Workflows menu. Make, edit or run them with the `comfyui-workflow` skill. Every task's run command uses its runner:

```bash
RUN="python3 <comfyui-workflow skill>/scripts/run_workflow.py"   # e.g. ~/.claude/skills/comfyui-workflow
$RUN <workflow> --list      # inputs and groups, before your first run of a workflow
```

`--set "Title.input=@/local/file"` uploads a local file into that loader.

## Rules for every task
1. **Ask before you guess.** Each task lists what to ask when the request doesn't say: which character sheet, which outfit, which part of the clip, sound or not.
2. **Prompts are general.** Write what is true for this input, in the task's template; never tune a prompt to make one result pass.
3. **Describe only what you want.** Never name what you remove or what's drawn or overlaid on the input: these models draw what the prompt names, "no" or not.
4. **Sizes come from the source.** Width, height and video length follow the input (the size node), unless the task says otherwise.
5. **Check your own work.** Run the task's check (a script where there is one), then look at the result yourself before you hand it over.
6. **Show the inputs with the outputs** when you report, and give the run time.
7. **Every lesson carries its date and evidence** (strong = fixed on several runs; medium = one before/after; open = no fix yet).

## Files
- `models/<model>.md`: how to prompt the model, from its official guide plus what we measured.
- `tasks/<task>.md`: the recipe: goal, ask-if-unsure, inputs, what you write, run, check, lessons.
- `scripts/h3_audit.py <dir>`: checks MiniMax H3 swap prompts (both video tasks). Exit 1 = fix and rerun.
- `references/`: official guides, evidence and history per task.
