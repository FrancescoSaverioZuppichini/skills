# MiniMax H3 (reference to video): how to prompt

**Source:** MiniMax's full-reference prompt guide, the format H3 was trained on (`references/h3-official-ref-guide.md`, verbatim; the community spec is `references/h3-singularity-spec.md`). This file is the short version; each video task builds its fixed template on it.

**Default: ~1 MP** (Size node "from image", 0.92 MP, multiple 32: a 9:16 source renders 736×1312; the guide video is fed at exactly half). REFINE drops the main pass to a 0.50 MP draft by itself and doubles it to 2.1 MP; there is no size to set by hand. **Spark-H3** (group 8, on by default) makes the main pass ~20 % faster with the same video; **Lean attention** keeps sage from crashing on long clips. How the guide video reaches H3: the video task's Run section.

## How H3 prompts are made
- H3 is trained on long prompts written by MiniMax's closed rewriter from a short request plus the inputs; MiniMax calls that step "critical to the quality of the final output". We rebuild the rewriter's output with fixed task templates plus slots written from the source.
- Write in English, except dialogue, lyrics and visible on-screen text.

## Six sections, in this order
| Section | Holds |
|---|---|
| `subject_definitions` | one line per tracked thing: label, role, main features |
| `summary` | `[task prefix]` + one short paragraph |
| `retention_analysis` | per label: where it appears + how much is kept |
| `detailed_description` | shot by shot, in playback order: composition, positions, scene, light, actions, camera, sound |
| `overall_soundscape` | ambience and physical sound |
| `non_diegetic_music` | score only the audience hears, or N/A |

## Labels
| Label | Use |
|---|---|
| `<Subject N>` | visible content to reuse or change: a person, scene, clothing, prop, style, action or pose |
| `<Picture N>` | an image used as a concrete frame (first, key or last). If it only supplies a subject, cite it inside that `<Subject>` line instead of giving it its own line |
| `<Video N>` | the editing source, the continuation start, or a whole-video timing structure |
| `<Audio N>` | an audio signal that is copied or referenced |
| `[Shot N]` | marks a shot. In `detailed_description` each shot opens with it: `[Shot 1]` with no timestamp, every later shot `[Shot N] At MM:SS.mmm,` at its cut. In `retention_analysis` it says where a label appears: `(throughout [Shot 1], [Shot 2])` |

A label keeps the same meaning in every section. Numbering is per type, in input order; shots are numbered in playback order.

## Task prefixes (combine with ` + `)
`video editing` (an existing video is modified) · `video continuation` · `reference generation` (assets guide character, scene, style, motion or camera without being a frame or the edited source) · `keyframe completion` (an image is a concrete frame) · `audio reuse` (the same signal is reused) · `audio reference` (only timbre, style or content).

## Retention verbs
- Visual: `fully_preserved` (kept whole) · `partially_preserved` (the label is still used, some features change) · `attribute_transfer` (features move to another subject) · `weak_reference` (broad similarity only).
- Audio: `fully_copy` · `partially_copy` · `reference` (timbre, rhythm or style only) · `weak_reference`.

## Shots and timestamps
The official rule (guide §5.1), verbatim: "`[Shot 1]` marks the opening shot and has no timestamp. Later shots use `[Shot N] At MM:SS.mmm, ...` to mark cut times."

Its example, verbatim:
```text
The target video is in a cinematic, literary music-video style with soft lighting and a slightly desaturated color palette.
[Shot 1] The scene opens in a crowded urban street...
[Shot 2] At 00:09.000, the shot cuts to an extreme close-up...
```
- One shot: no timestamp anywhere; moves are prose in playback order.
- Several shots: each later shot opens with its cut time, taken from the source (`cv_tools.shots` → `shots.json` → `start`), times strictly increasing; moves inside a shot stay prose. Retention lines list every shot: `(throughout [Shot 1], [Shot 2])`.
- Skeleton of a two-shot description (each task file has its full two-shot template, exactly what its audit accepts):
  ```text
  <one style sentence> [Shot 1] <who does what, where: scene, framing, moves, camera> [Shot 2] At <MM:SS.mmm>, the shot cuts to <who, where: scene, framing, moves, camera> <closing lines>
  ```
- Dialogue goes inside `<d>[Language] …</d>` with a speaker id `(S1)`. Our swap tasks never transcribe speech: they reuse the clip's sound.

## Length
- The official guide: "For generation tasks, `detailed_description` is normally 350-500 English words … Video-editing descriptions scale with the complexity of the source video and do not have to follow the generation-task range. A single shot does not automatically justify a shorter description."
- Ours, measured on swaps: a 3 s single shot passes at 540–670 words in total. Scale with the clip: about 30–45 words of moves per second of each shot. `h3_audit.py --seconds` raises its limit the same way.
- Long prompts made of 0.125 s timestamped beats (850 words) never passed. Moves are prose.

## Length of the video
H3 renders 17n + 5 frames at 24 fps: 73 = 3 s, 124 = 5.2 s, 201 = 8.4 s, 241 = 10 s. The swap workflow renders the longest such length that fits the guide it gets. Render the whole clip, the part asked for, or one shot; never cut shorter by default.

## Never
- Name anything drawn on an input (skeleton, dots, lines, guides), even to exclude it: H3 paints it (2026-11-14, strong).
- Name what is hidden or removed: describe only the result.
- Write the aspect ratio or resolution: the render size sets them.
- Use a ControlNet for pose or inpainting (failed 2026-11-14 and 11-16; the user's hard rule).
- Change the sampling contract per task: Singularity v1.3 int8 + Pika LoRA, `lcm` on Pika's own 6 knots (`1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0`), shift 12 / 3, CFG 1. Pika's README: a generic 6-step schedule "does not reproduce" its contract. Never stack Pika with a speed LoRA. Test any distilled model on its author's own schedule first.
