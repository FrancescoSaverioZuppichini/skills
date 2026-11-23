# Qwen Image 2.1 edit: how to prompt it

Used by: `image-character-swap`, `image-outfit-swap`, `image-remove-anything`, `image-character-sheet`.

## How it reads a prompt
- **Pictures are named by their order:** `<image1>`, `<image2>`, … in the order they're wired into `TextEncodeQwenImage21`. Image 1 is the canvas the edit starts from; the others are references.
- **Write an instruction, not a caption:** say what changes and what stays, in plain sentences. "Edit `<image1>`: remove … Keep …"
- **Name what stays.** Lighting, background, pose, framing and clothes stay only if you say so. Our clothes-first wording kept the photo's clothes 8 of 8 times, against 0 of 8 without it (2026-11-05, strong).
- **Describe the person you want,** in one line: hair, eyes, build ("long straight medium chestnut-brown hair, warm brown eyes"). Never describe the person being replaced.
- **`resolution = 0`** on the encoder means Image 1's exact size. The sizes come from the source photo; don't type them.
- **CFG 1, empty negative.** The workflows sample at CFG 1, where a negative prompt does nothing. Put everything in the positive.

## Words that matter
- **Braces:** write "orthodontic dental braces". Bare "braces" means suspenders, and never write "silver" (2026-11-06, strong).
- **"Change only the …"** keeps a local edit local: teeth, hair, one garment.
- **Never name what you remove** ("no tattoo") in a swap prompt: it comes back. Remove-anything is the exception; there, naming the things to remove IS the task.

## Don't
- **Lower the denoise to keep the pose or texture:** dead, tried months ago (2026-11-21).
- **Swap only the head or face onto a real person:** never. The whole person is replaced, or nothing is (2026-11-03).
- **Grey out the source person before the edit:** the model needs to see her to keep the pose (2026-11-03).
