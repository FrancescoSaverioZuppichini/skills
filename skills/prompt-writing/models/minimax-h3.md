# MiniMax H3: the common prompt format (every task)

Source: MiniMax's official full-reference guide (link in `references/README.md`; it has no licence, so it is linked, not copied). This file is the short version. Each task's H3 subsection builds on it.

## How H3 prompts are made
- H3 is trained on prompts written by MiniMax's closed rewriter, H3-Context-IR. It reads a short request plus the inputs and writes the long prompt. MiniMax calls that step "critical to the quality of the final output".
- The open release ships only the rewriter's output spec, not its system prompt. We rebuild the rewriter with an LLM, using the official guide and the task's subsection as its instructions.

## Six sections, in this order (full-reference / Ref2VA)
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
| `<Picture N>` | an image used as a concrete frame (first, key or last) or composition anchor. If it only supplies a subject, cite it inside that `<Subject>` line instead of giving it its own line. |
| `<Video N>` | the editing source, the continuation start, or a whole-video timing structure |
| `<Audio N>` | an audio signal that is copied or referenced |

A label keeps the same meaning in every section.

## Task prefixes (combine with ` + `)
`video editing` (an existing video is modified) · `video continuation` · `reference generation` (assets guide character, scene, style, motion or camera without being a frame or the edited source) · `keyframe completion` (an image is a concrete frame) · `audio reuse` (the same signal is reused) · `audio reference` (only timbre, style or content is referenced).

## Retention verbs
- Visual:
  - `fully_preserved`: the role is kept whole;
  - `partially_preserved`: the label is still used, but some features change;
  - `attribute_transfer`: features move to a different subject;
  - `weak_reference`: only broad similarity is kept.
- Audio:
  - `fully_copy`: the whole source is the final track;
  - `partially_copy`: part of it is copied, or layers are added, removed or replaced;
  - `reference`: only timbre, rhythm or style;
  - `weak_reference`.

## Description rules
- "As detailed and explicit as possible." For generation tasks, 350–500 words. For editing, the length scales with the source clip.
- Timestamps where the action changes: `At 00:02.000 …`. Dialogue goes inside `<d>[Language] …</d>`, with the speaker id `(S1)`.
- Write in English, except dialogue, lyrics and visible on-screen text.
