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
