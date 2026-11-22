# Example lab page (page.mdx)

This is the shape every lab page takes. It is a made-up program, "render a 15 s video swap at 1 MP, faster", with three students on two GPUs. The order is fixed: the index first, then "watch first", then the program, then one mini paper per student, newest results on top.

```mdx
---
title: "Long video swap · faster at 1 MP"
description: Lab page for the long-video program.
order: newest-first
---

<Section id="index" title="Index · 3 students, 3 mini papers" open>
**Start here:** [▶ Watch first](<link>#watch) · [Program](<link>#program) · [Survey](<link>#survey)

### 📄 S-01 · [windows](<link>#windows): Long clips in windows
**Question:** Can a 15 s clip render at 1 MP in windows, each with its own guide slice, with no visible joins?
**Result so far:** 15 s in 371 s (24.6 s per video second); join 2 fails, fix running.
*fast GPU · Sonnet*

### 📄 S-02 · [spark](<link>#spark): Sparse attention from a paper
**Question:** Does the paper's block-sparse attention speed up the render without hurting the face?
**Result so far:** running: 5 s A/B at 20 % and 40 % density.
*slow GPU (bench) · Opus*

### 📄 S-03 · [judge](<link>#judge): Timing and quality judge
**Question:** Does each render keep the source's timing, identity and sharpness?
**Result so far:** time anchors in the prompt cut the lag from 18 frames to 0.6.
*CPU · Sonnet*

---
**Scheduling:** the fast GPU is production (full-length runs, winners). The slow GPU is the bench (5 s A/B tests against its own 5 s baseline).
</Section>

<Section id="watch" title="▶ Watch first · full-length renders" open>
<Gallery title="Full 15 s">
  <Media id="watch-src" src="in/source.mp4" title="Source" badges={["⏱ source, not generated"]} />
  <Media id="watch-s01" src="out/windows-e2.mp4" title="S-01 windows · 1 MP" caption="In step until 10 s; join 2 fails." badges={["⏱ 371 s", "24.6 s per video s", "23.8 GB"]} compare="watch-src" />
</Gallery>
</Section>

<Section id="program" title="Program · goal and scoreboard">
**Goal:** a 15 s render at 1 MP, faster and with less memory than one pass, with no quality loss.

| render | size | ⏱ | s per video s | VRAM | lag | identity | verdict |
|---|---|---|---|---|---|---|---|
| S-01 windows E2 | 768×1376 | 371 s | 24.6 | 23.8 GB | 2.5 / 15.6 | 0.697 | ⚠ join 2 |
</Section>

<Section id="windows" title="📄 S-01 · windows · Windows keep 1 MP 15 s renders in step ⏳">
**Now:** E3 running (anchored prompts). Next: 30 s.

**Abstract.** Three or four plain sentences: the question, what we did, and the headline number.

**Thesis.** One falsifiable sentence. **Dead if** a stated bar is missed.

**What we did.** The setup, in plain words.

**Results.** A table, then every render card with ⏱, s per video second and VRAM.

**What it means.** One paragraph.

**Details.** Scripts, paths, commits.
</Section>
```

**Rules this example shows:**
- **Student ids** (`S-01`, `S-02`, …) are given at spawn and never reused. Every section title starts with the id.
- **The index** has one `###` block per student, never a table, each with Question, Result so far, and GPU · model.
- **Every render card** carries ⏱, s per video second and VRAM. Results never hide in a folded section.

## Gross-defect judges for other kinds of research

The page layout stays the same for any program. What changes is the output, the baseline and the defect list the judge checks. Write the list before the first run. Numbers like these are info, never a verdict: identity, sharpness, perplexity, a recall@10 move under a point.

| program | output | baseline | gross defects the judge flags | dies only if |
|---|---|---|---|---|
| Faster long-video generation | a 15 s video | the same job, dense, one 5 s run per GPU | pose off; a missing or extra limb; the face lost; guides or subtitles painted in; a move > 0.25 s early or late; a visible join | a defect, a visible loss on a side by side, or no speed-up |
| Faster image model (e.g. fewer steps, int8) | 20 fixed prompts × 2 seeds | the original model, same prompts and seeds | the subject missing; extra fingers or limbs; broken faces; garbled text that the prompt asked to be clean | a defect on more images than the baseline has, or no speed-up |
| LLM inference speed-up (e.g. quantization, speculative decoding) | answers to a fixed check set (100 Q&A, 20 JSON tasks) | the full-precision model on the same set | a wrong answer where the baseline is right; invalid JSON; repetition loops; truncation | more wrong answers than the baseline's run-to-run spread, or no tokens/s gain |
| Faster embedding search | top-10 results for 200 known query → document pairs | the exact (brute-force) search | a known pair falling out of the top 10; empty or duplicate results | more pairs lost than an agreed small count, or no QPS / memory gain |
| Custom GPU kernel | the output tensors | the reference kernel on the same inputs | max abs difference over the stated tolerance; NaN or Inf; crash or OOM at the target shapes | any of those, or slower than the reference |

### One index block per kind of student, so the page reads the same everywhere

```mdx
### 📄 S-04 · [quant](<link>#quant): int8 weights for the 8B model
**Question:** Does int8 keep the answers on the check set while decoding faster?
**Result so far:** 1.7× tokens/s; 0 new wrong answers out of 100; JSON valid 20/20.
*fast GPU · Sonnet*

### 📄 S-05 · [ann](<link>#ann): HNSW instead of brute force
**Question:** Does HNSW keep the known pairs in the top 10 at 10× the QPS?
**Result so far:** 12× QPS; 2 of 200 pairs drop to rank 11–12, shown on the page.
*CPU box · Sonnet*
```
