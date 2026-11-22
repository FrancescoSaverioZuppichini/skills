# Character swap on H3: settings, inputs, evidence and history

The writer's file is `tasks/character-swap.md`. This file holds what the writer doesn't need while writing: the render setup, where each rule came from, the shot-format survey, and what failed. Run ids (`18f`, `W2`, `iteration 3`, …) are the lab's render logs; they are named here so a claim can be traced, never needed to write a prompt.

## Render setup
- **Model:** Singularity v1.3 int8 (`Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8.safetensors`) → `MiniMaxChunkFeedForward` → Pika LoRA `pika_h3_flex_ref2va_v1_bf16.safetensors` → sigma shift 12 / 3; sampler `lcm` on Pika's schedule `1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0` (6 steps), CFG 1; 736×1312 (1 MP).
- **No 4-step speed LoRA** (base H3 + ref2v turbo): worse look (owner, 2026-11-15).
- **Never a ControlNet**, for pose or inpainting: hands at the wrong moments (2026-11-14 full redraw), wrong pose (2026-11-16 repaint-only). Owner's rule.
- **`<Picture 1>`:** the character sheet only, always a Qwen-dressed sheet. Never a sheet dressed by H3 (quarantined 2026-11-17). A face close-up as `<Picture 2>` added nothing (18f with/without); an outfit crop added nothing (21 vs 22).
- **`<Video 1>`:** `python -m cv_tools.motion_guide --input <window.mp4> --output <dir> --mask-grow 0.05`, fed at 368×656 with the window's audio. The woman is blurred inside her SAM 3.1 mask, the blur reaching 5 % of the long side past it (stops her hairstyle and accessories leaking back: reel 02 bun + hoops, iteration 3 → 5); pose skeleton plus eyebrow + mouth dots drawn on top (eye and nose dots came back as glowing eyes, 26/27 → 28). A 576×1024 reference video is slower and lets garment shapes back in (REF59).
- **Length:** 17n + 5 frames at 24 fps (73 = 3 s, 124 = 5.2 s, 201 = 8.4 s). Render 3 s first; long clips drift (8.4 s: pose good on 2 of 4 seeds).
- **Small and far faces:** the R450-2 resolution route (0.5 MP draft → H3 latent upscaler ×2 → 2 Pika steps at 2.1 MP from 0.45). Crops, face passes and paste-backs are banned (owner, 2026-11-22: full frame only).

## Where each rule came from
| Rule | Evidence |
|---|---|
| Never name the drawing | iterations 0–2 painted white dots on her face with 3 different wordings; iteration 3 without them clean on 10 of 10 (bridge, video 2, reels 01–03, seeds 1001/2002) |
| Hide the whole woman | her clothes stayed whenever visible (11b, 12, 18b); with the raw clip H3 kept her face and only recoloured the hair (base0) |
| A masked clothes area alone becomes a plain top | M1, 14, 15a, 15b → whole-woman mask fixed it (16, M5) |
| Never mention stickers or captions | asking to keep them got the guides painted too (25 → 26) |
| Outfit sentence inside the shot | jeans A → B (2026-11-19): nude 2/2 → dressed on every later render (2 seeds, 7 prompts) |
| Moves from the raw frames, no false turns | the jeans "lock" prompt said she turns half away; the raw clip faces the camera. Lock: back view on 3 of 5 seeds; W2 ("keeps her front to the camera the whole time and never turns"): 0 of 5 (facing check, 2026-11-22). A false move line also softened the face (sharpness +3 % to +83 % with W2, 5 of 5 seeds) |
| Face line kept when her head leaves the frame | jeans W2: her head leaves from about frame 42; the renders followed the guide on 5 seeds |
| Moves in prose, not timestamped beats | every passing prompt (16, 18f, iterations 3 and 5) used prose; 0.125 s beats with 850-word prompts never passed |
| Name objects she holds | reel 03 nozzle: kept and used in every render |
| Never name a phone in her hand | the model paints one |
| Prompt length | iterations 3 and 5: 540–670 words |
| Multi-shot tags | one 2-shot test clip, 1 seed (2026-11-22): the guide sets the cut (prose cut at frame 36, tagged at 35; real 36); the tagged prompt held shot 1's framing to the cut, the prose prompt invented a camera swing over frames 30–35 |

## Shot format: official and community (2026-11-22)
- **Official** (MiniMax guide §5.1, `references/h3-official-ref-guide.md`): "`[Shot 1]` marks the opening shot and has no timestamp. Later shots use `[Shot N] At MM:SS.mmm, ...` to mark cut times." Examples: `[Shot 2] At 00:09.000, the shot cuts to an extreme close-up...`; `[Shot 2] At 00:02.800, the camera cuts to a medium close-up of the captain from Shot 1 in profile facing right`.
- **Community:** nobody timestamps a single shot. Multi-shot use varies: [HF discussion 47](https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/47) (`[Shot 2] At 00:03, the camera cuts to…`), [HF discussion 71](https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/71) (shot blocks without times), [ComfyUI Fantastic H3 Prompt Builder](https://github.com/Adudeguyman/ComfyUI-Fantastic-MiniMaxH3-PromptBuilder) (inserts `[Shot N] At MM:SS.mmm,`, warns on a timed `[Shot 1]`), [awesome-minimax-h3-prompts](https://github.com/ecomimagelab/awesome-minimax-h3-prompts) (`CUT TO:`), [ComfyUI's H3 prompt guide](https://docs.comfy.org/tutorials/video/minimax/minimax-h3-prompt-guide) (one timestamp per cut, never a range).

## What failed (don't retry without a new reason)
- Any ControlNet (above).
- Describing the drawn guides in any wording (iterations 0–2). Example of the banned style, iteration 0: "…carries drawn guides: coloured pose-skeleton lines and dots…" → white blobs over her eyes and mouth in every frame.
- Drawing the guides at 70 % / 40 % opacity: painted, only paler (30, 30b).
- Pasting stickers back after the render: visible patches (2026-11-15).
- Repainting only the person (original video as start latent + denoise mask, pose via ControlNet inpaint): wrong pose and hand signs (2026-11-16).
- Timestamped beats every 0.125 s, prompts up to 850 words: never passed.

## Open problems
- Stickers and captions disappear in the full redraw: accepted for now.
- Short hair (bob) after the wider blur on one clip (reel 02, iteration 5).
- Pose drift on long clips: try another seed.
- Sheet details leak (studded wristband, barefoot): iterations 3, 5.
