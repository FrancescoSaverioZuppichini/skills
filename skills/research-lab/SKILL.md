---
name: research-lab
description: Run a research program as the professor. The /goal is the final research goal (find something new, make something faster, improve a result). Every round runs the same numbered steps: literature, measure and profile first, choose novel non-overlapping lines, design the bars, brief research-student agents, schedule the limited machines, run cheapest-kill experiments, audit while they run, ship what works on every machine, close the round. Rounds repeat until the goal's number is reached. Use whenever a goal needs experiments by several agents, or the user says "research", "students", "professor", "lab" or sets a /goal that needs experiments.
---

# Research lab: you are the professor

Students run the research. You choose the lines, hand them off, read every result yourself, steer, re-task or stop students, and turn what works into clean, shipped code. You never run the experiments, and you never report a student's claim without reading its result file.

## Words

- **Owner:** the human who set the goal. **Round:** one pass through the steps below. **Research line:** one path to the goal, owned by one student. **Hold:** one booked slot of a machine's GPU.
- **PLAN.md:** the program: goal and baseline, what is proven, one entry per failure (so nobody retries it), what is parked, who owns which line. Superseded entries move to `archive/`.
- **Rules file** (`briefs/HOUSE.md`): what every student reads first: machine rules, locks, the page path, the project log. **Brief** (`briefs/<id>.md`): one line's frozen plan. **SCHEDULE.md:** each machine's queue and the file claims.
- **Dumps:** real intermediate tensors captured from one run on real inputs. **Ladder:** a sequence of tests ordered by cost.

## The round, step by step

Every round runs these steps in order. The program repeats rounds until the goal's number is reached or the owner stops it; never stop after one round on your own.

1. **Goal and files** (round 1; later rounds update them).
2. **Literature:** arXiv newest year first, then code and repos.
3. **Measure before planning:** calibrate each machine, profile the baseline, dump real tensors.
4. **Choose the lines:** priced from the profile, novel, different, few.
5. **Design the bars,** before any experiment runs.
6. **Write the briefs and spawn the students.**
7. **Schedule the hardware:** price the round, critical path first.
8. **Run the experiments:** every variant climbs its ladder until it dies or ships.
9. **Audit while it runs:** steer, re-task, stop.
10. **Ship what works:** clean code, gated on every machine.
11. **Close the round** and start the next.

## 1. Goal and files

- The /goal is one sentence with a number and a baseline ("1,000 images a second at the same search quality as today's 91").
- Create PLAN.md, the rules file, SCHEDULE.md and the live page (the `local-artifacts` skill), with the goal at the top of PLAN.md and of the page.
- The rules file names, per machine:
  - the GPU-lock command and the CPU guard that stops CPU work during a hold;
  - the files frozen during a hold (edits go to a copy, swapped between holds);
  - the log path.

  The measurement rules live in the student agent file; do not restate them.
- Every line must move the goal's number, or it stops.

## 2. Literature

Before any thesis, every round: what this round taught changes what to look for. A web search ranks by popularity and misses this month's papers, so query arXiv's own API, newest first.

1. **Write 15–25 queries** from the thesis, one term from each of three groups per query:
   - the symptom ("small objects", "motion blur");
   - the mechanism ("high-frequency", "token budget", "RoPE");
   - the setting ("video diffusion", "few-step").
2. **Run them newest first, current year, then the year before:**

   ```sh
   curl -s -G "https://export.arxiv.org/api/query" \
     --data-urlencode 'search_query=abs:"video diffusion" AND abs:"high-frequency" AND submittedDate:[202601010000 TO 202612312359]' \
     --data-urlencode sortBy=submittedDate --data-urlencode sortOrder=descending --data-urlencode max_results=40
   ```

   - **Field prefixes:** `ti:`, `abs:`, `au:`, `cat:` (`cat:cs.LG`), `all:`.
   - **Syntax:** phrases in double quotes; `AND`, `OR`, `ANDNOT` with parentheses; dates as `submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM]`.
   - **Paging:** `start=40`.
   - **Rate limit:** one request every 3 s. On HTTP 429, use arxiv.org's search page and Semantic Scholar instead of waiting.
   - **Client:** use `curl -G --data-urlencode` (Python's urllib can fail on HTTPS certificates on macOS).
3. **Parse and save:**
   - Each Atom `<entry>` has `<id>`, `<published>`, `<title>` and `<summary>`.
   - Deduplicate, and save to `literature/round-N.json` with the query that found each hit, so the next round only reads what is new.

   ```python
   import subprocess, xml.etree.ElementTree as ET
   ns = {"a": "http://www.w3.org/2005/Atom"}
   xml = subprocess.run(["curl", "-s", "-G", "https://export.arxiv.org/api/query", "--data-urlencode", f"search_query={q}",
                         "--data-urlencode", "sortBy=submittedDate", "--data-urlencode", "sortOrder=descending",
                         "--data-urlencode", "max_results=40"], capture_output=True).stdout
   for e in ET.fromstring(xml).findall("a:entry", ns):
       arxiv_id = e.find("a:id", ns).text.rsplit("/", 1)[-1]
       date, title = e.find("a:published", ns).text[:10], " ".join(e.find("a:title", ns).text.split())
       abstract = " ".join(e.find("a:summary", ns).text.split())
   ```
4. **Triage in three passes:** titles, then abstracts, then the full HTML (`https://arxiv.org/html/<id>`) of the papers that decide a line: method, numbers, limits, training-free or not. Known ids: `--data-urlencode "id_list=2511.19778,2610.05816"`.
5. **Follow citations forward:** newer work that builds on a deciding paper often beats it.

   ```sh
   curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2511.19778/citations?fields=title,year,externalIds&limit=100"
   ```
6. **Check code, weights and other engines:** GitHub links, project pages, Hugging Face, issue trackers. Then use WebSearch in extended mode for what arXiv doesn't hold.
7. **Write the verdicts:** one row per paper or project in the brief and PLAN.md: id, date, link, one-line method, the number that matters, code yes or no, verdict (reuse / already failed / contradicts / gap).

A wide sweep can be split across students, one topic cluster each. You still read the abstracts that decide a line yourself.

## 3. Measure before planning

The round's first holds measure; nothing is planned from guesses.

1. **Calibrate each machine:** an A/A run of the baseline, two runs of the same build, with clocks and power limit locked or at least recorded. Its spread is the noise every later threshold uses.
2. **Profile the baseline:** time per kernel or stage, each against its own floor. The floor is bytes ÷ bandwidth for memory-bound work and operations ÷ peak for compute-bound work. Untraced timing gives the numbers; profilers attribute the time.
3. **Dump once, replay many:**
   - **Capture:** the real intermediate tensors (activations, caches, attention inputs and outputs, routing choices, latents) from one run on real inputs, with source and settings recorded.
   - **Replay:** every later variant is tested on those dumps first, in seconds, without starting the full system: error against a high-precision reference, closeness to the current version, time at the real shapes.
   - **Real over synthetic:** real dumps beat synthetic data even for timing, because routing, lengths and data-dependent formats change it.
   - **Cleanup:** raw dumps are deleted when the round no longer needs them.

## 4. Choose the lines

- **Priced:** each line names the µs, MiB or quality points it can move. That number comes from the profile (the gap to the floor) or from first principles, never from hope.
- **Novel:** check every idea against §2. When something published already solves part of it, the line becomes "adopt and measure". If novelty stays unclear, the student's first milestone is to search further and validate.
- **Different:** no two lines take the same path or edit the same files. Before spawning, compare a new line with the running ones; merge or drop overlaps.
- **Few, in phases:** usually 3 to 5 lines at once. Build-and-measure phases come first and skip the novelty search; improvement phases need it. Start a phase only when the previous one has its answer; park later ideas in PLAN.md.

## 5. Design the bars

Write every bar before the first run and freeze it; change it only by a dated revision. Every bar names five things: **metric · reference · threshold and where it comes from · test set · what happens when it fires**.

| goal | bar | metric · reference | threshold (source) | test set · when it fires |
|---|---|---|---|---|
| an LLM engine fits 2× the context on the same GPU at today's speed | memory (pass) | peak GPU memory at the new context · absolute | ≤ the card minus a measured headroom (the goal) | one full-length input · "does not fit" |
| | speed (pass) | step time with input-independent settings vs the baseline build, same GPU and window | ≥ 0.85× (the goal; bytes moved per step give the ceiling) | the fixed benchmark rows · lever dead |
| a video workflow renders 30 % faster with no visible loss | speed (pass) | wall time per output second vs the baseline workflow, same GPU | ≤ 0.70× (the goal) | 5 fixed source clips · lever dead |
| | quality (kill) | gross defects vs the baseline render | face lost, a limb missing or extra, pose off, visible joins | the same 5 clips side by side · lever dead |
| image search answers 2× faster with the same results | quality (kill) | known pairs in the top 10 vs the baseline index | more misses than the baseline's own count | a fixed labelled set of 500 queries · lever dead |
| | no regression (pass) | every other benchmark row vs the baseline, same window | ≤ 5× the measured A/A spread | the fixed rows · revert |

- **A threshold comes from the goal or from physics** (bytes ÷ bandwidth, memory needed, the measured spread), never from a round number.
- **The reference must be able to run.** Where none fits (a size only the new method reaches), use absolute checks plus the trend from where both run.
- **Run every bar on the baseline first:** the baseline must pass a quality bar, and physics must allow a speed bar. "Within noise" means the measured A/A spread; a deterministic system has none.
- **Judge the method, not luck:** when the input changes the number (speculative acceptance, seeds, sampling), the bar uses the input-independent one (fixed seeds, fixed-token steps) and only reports the other.
- **Kill on gross defects and physical limits only.** Write the defect list per task:
  - **video:** pose off, a missing or extra limb, the face lost, overlays painted in, big timing slips, visible joins;
  - **images:** a missing or extra object or finger, a broken face, garbled text, the subject not there;
  - **LLMs and text:** wrong answers on a fixed check set, broken output format, repetition loops, truncation;
  - **search and embeddings:** known pairs falling out of the top k, empty or duplicate results;
  - **kernels and speed work:** outputs past a stated tolerance against the reference, crashes, OOM.

  Small score deltas (identity −0.02, sharpness −5 %, perplexity +0.1, top-1 between 90 and 100 %) are reported for ranking, never a verdict. A tight numeric bar that kills a working lever is a recurring failure.
- **Small exact gains stack:**
  - **Keep** a lever if it is exact and measurably faster (≥ 2× the A/A spread), or simpler with no measured loss.
  - **Kill** it if it is slower, changes bits it claimed to keep, or adds code its measured gain doesn't pay for.
  - Winners stack on one branch, each gated alone, and the stack is measured end to end: ten 1 % levers are 10 %.
- **The pass bar is what ships; the kill bar ends the line.** The stop rule is a deliverable done or a kill bar fired. A hold count is a budget cap: hitting it means report and ask, not done.

## 6. Write the briefs and spawn the students

- **The brief:**
  - the line's goal and its priced number;
  - what is known (numbers, paths, links) and the prior-work list with verdicts;
  - the files the student claims;
  - milestones, E1 (the cheapest test that can kill the line, usually a replay on the dumps), and the bars from §5;
  - the stop rule and what to report.

  A brief you hand over is approved; the student stops only at the points its agent file lists.
- **Students** are always the `research-student` agent type; audits and cold reads use a fresh general-purpose agent. Each spawn gets:
  - a persona fitting the line ("a senior OpenAI GPU kernel engineer");
  - a model: Sonnet for well-specified measurement runs, Opus at effort high for open-ended or hard lines;
  - an id `S<round>-<nn>`, in spawn order within the round, never reused or renumbered, used everywhere (page, PLAN.md, SCHEDULE.md, log lines, card ids).
- **The spawn prompt** says only who the student is and which files to read (rules file, PLAN.md, SCHEDULE.md, its brief), so a restart costs nothing.
- **File claims:** a student adds a row to SCHEDULE.md before editing code, and never edits a file someone else claims.
- **No click prompts:** the rules file tells students to quote paths as `"${P:?}"/x` or write them literally, and to prefer script files over long one-liners. `rm`/`mv` on an unquoted or possibly-empty variable path, `rm -rf` on globs or `~`, and `curl | sh` stop for the owner's approval, and a prompt the owner has to answer is a bug in the student's command.

## 7. Schedule the hardware

- **Price the round before it starts:** GPU hours per machine for each line. The busiest machine sets the round's length; say the estimate, and cut or reorder until it is acceptable.
- **Critical path first:** side lines pause when they compete for the critical machine; they keep their context and resume later.
- **CPU before GPU:** whatever dumps, code or arithmetic can decide is decided there. Builds happen outside holds.
- **Holds:** one at a time per machine, ≤ 15 minutes, their length stated in SCHEDULE.md, stopped as soon as the question is answered. When a hold ends, the next ready student gets the GPU at once: an idle GPU is your failure.
- **Pay expensive setup once:** one long input carries all the probes (read once, questions asked through the prefix cache); one model load serves several variants; a scaled-down input tests the pipeline before the full size.
- **Two or more different machines:**
  - What depends on the machine (speed, memory, kernel tuning) is measured on each one. Everything else (correctness tests, replays, quality screening, functional runs) goes to whichever machine is free and faster.
  - Each machine has its own lock, queue, baseline, noise calibration and log. A student may book on either, but holds one at a time.

## 8. Run the experiments

The hardware is the scarce resource, so run as few experiments as the decisions need.
- **Only decisive experiments:** before a run, write what each possible outcome would make you do. If no outcome changes a decision, don't run it.
- **Physics fills what it can:** a variant that cannot fit, or whose bytes per step already exceed the bar, gets its cell from the arithmetic or one load attempt, not a run.
- **Each line has a hold budget** set from its price in §7. Repeats stop at what the measured noise requires.
- **Reuse before rerunning:** a same-window baseline, a dump, or an earlier run of the same build answers the question.

Every lever or variant climbs a ladder ordered by cost and stops at the rung where it dies. That rung and the measured reason fill its cell, so a kill is data, not a gap.

| question | rung 1 (seconds) | rung 2 (minutes) | rung 3 (only survivors) |
|---|---|---|---|
| is a kernel change faster? | replay of that kernel on the dumps at the real shapes | quick end-to-end A/B | full benchmark |
| does a compression format keep quality? | replay on the dumped tensors vs the high-precision reference | short input end to end vs the reference | long input + the full quality suite |
| does a variant fit in memory? | one load attempt at the target size | one full-length input | quality runs |
| does a video or image pipeline change break outputs? | 2 seconds of one clip at few steps, checked for gross defects | the 5-clip set at full steps | full-length renders |

- **A replay can kill but never prove speed.** A kernel slower alone is not faster in the system. One faster alone can still slow the real step (cache contention, extra launches, competing streams), so every survivor gets one end-to-end run on real inputs before any verdict.
- **Full protocol for finalists only:** the one or two variants that reach the last rung get the same complete protocol on every machine. The matrix per machine has every cell filled with a measurement, or with the rung, arithmetic or load attempt that ended the variant.
- **One A/B for a big effect,** A/B/A/B interleaved in random order for small ones; the full benchmark only for final tables. The measurement standard (warm-up, untraced timing, spread, machine fingerprint) is in the student agent file.

## 9. Audit while it runs

- Check at every student notification, and between them on a timer (a CronCreate job every 5 minutes, or a Monitor on SCHEDULE.md and the project log): the queues, the result folders, each student's "Now:" block.
- **Read the result file before you relay any claim,** and open every image or plot yourself.
- **Audit against the literature:** when a student reports a finding or a line is about to be called done, check it against arXiv, newest year first. If it is already published, the line becomes "adopt and measure" and the page cites the paper. If a paper contradicts it, re-test before anything builds on it.
- **Every student pays rent.** Judge each one by evidence (holds used and wasted, rules broken, expected against measured numbers, findings), then steer it, give it something new, or stop it when it adds nothing, overlaps another line, or its kill bar fired. Stop leftover background waiters too.
- Write each steer into the brief as a dated revision, then send one message pointing at it, so a restarted student still has it.
- Ask the owner only for decisions that are theirs (quality trade-offs, budget, model switches, exceptions), with your recommendation first.

## 10. Ship what works

- **Clean before done:** a fresh general-purpose agent audits a winning lever. It reads every file on the path (the code, not your conclusions) against the owner's code rules (the `unslop` skill) and, for speed goals, the memory path end to end. The owning student fixes the findings within a lines-of-code budget, then re-measures.
- **Every machine before merge:** a change that lands for one machine is gated on every other machine before it merges (bits, references, benchmark).
- **Per-machine paths:** faster on all machines → one path. Faster on one, slower on another → both paths stay in one code base, picked at runtime by a hardware property (cache size, core count, supported number formats) or a measured per-machine table, each path gated on its own machine. Never fork the code per machine.
- **The PR** lists every change, its gates and benchmarks per machine, and which machine runs which path. The owner merges.

## 11. Close the round

- Update PLAN.md (proven, failed with the measured reason, parked), the page's comparison table and index, and the round's literature file.
- Save owner decisions and durable lessons in memory, not details the files already hold.
- When a line or the program ends, spawn a cold reader: a fresh general-purpose agent on Sonnet, with no context. It reads the page as a computer-science graduate outside the field and lists everything missing, unexplained or badly worded (a term never defined, a number without its unit or baseline, a figure without a caption). Fix the page and repeat until nothing serious is left.
- Then build the next round's lines from what this one taught, and go back to step 2.

## The page

One live page, in the format the rules file sets (default: the `local-artifacts` skill). A full example is in `example.md` next to this file. The order is fixed:

1. **Index**, first: one line linking the watch-first, program and survey sections, then one block per student in id order, written in Markdown (not a table). Add a block the moment you spawn a student; rewrite its result line when a number lands.
2. **Watch first:** the latest full-length outputs side by side, each with its wall time and speed.
3. **Program:** goal, baseline, the comparison table (one per machine; every row names its machine), notes.
4. **One mini paper per student:** title `📄 S1-03 · <student> · <claim> <✅/❌/⏳>`; body Now (2 lines), Abstract, Thesis + kill bar, What we did, Results (every card with wall time, speed and memory), What it means, Details.

- **Compare only within one machine,** and when bits matter, within one server process: a restart alone can change the bits.
- **Results never hide:** killed lines stay with ❌, and nothing sits in a folded section.
- **Status words are plain:** `running`, `paused (why)`, `finished`, `stopped (why)`.

```mdx
<Section id="index" title="Index · N students, N mini papers" open>
**Start here:** [▶ Watch first](<link>#watch) · [Program](<link>#program) · [Survey](<link>#survey)

### 📄 S1-01 · [student-a](<link>#student-a): short title
**Question:** the one question this student's paper answers.
**Result so far:** one sentence with the headline number (or "running: …").
*machine · model*

---
**Scheduling:** one line on which machine does what.
</Section>
```

Take `<link>` from `/api/check`'s `links`.
