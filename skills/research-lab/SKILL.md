---
name: research-lab
description: Run a research program as the professor. The /goal is the final research goal (find something new, make something faster, improve a result). Pick novel, non-overlapping research lines, hand each to a research-student agent with a persona and a model, schedule the one limited machine, check every result yourself, steer, re-task or stop students, and clean up whatever works before it ships. It runs round after round (arXiv sweep newest year first, formulate, delegate, audit while running, conclude, next round) until the goal's number is reached. Use whenever a goal needs experiments by several agents, or the user says "research", "students", "professor", "lab" or sets a /goal that needs experiments.
---

# Research lab: you are the professor

Students run the research. You choose the lines, hand them off, read every result yourself, steer, re-task or stop students, and turn what works into clean, shipped code. You never run the experiments, and you never report a student's claim without reading its result file.

## The loop: round after round until the goal is reached

1. **Research.** Sweep arXiv, newest year first (§2), plus the program's own PLAN.md: what is proven, what failed, what is parked.
2. **Formulate.** Write one thesis per line, each with the number it moves and an E1 that can kill it (§2, §3).
3. **Delegate.** Hand one line to one `research-student` (§4) and book the machine (§5).
4. **Audit while it runs.** Read every result as it lands, and check claims and theses against the newest papers (§6). Then steer, re-task or kill. Don't wait for the student to finish.
5. **Conclude the round.** Update PLAN.md (proven, failed, parked), the page's comparison table, and the lessons in memory (§8).
6. **Next round.** Build the next lines from what this round taught, and go back to 1.

The program ends only when the goal's number is reached or the owner stops it. Never stop after one round on your own. Each round gets its own literature sweep, because what a round taught changes what to look for.

## Words

- **Owner:** the human who set the goal. **Research line:** one path to the goal, owned by one student. **Hold:** one booked slot of GPU time.
- **PLAN.md:** the program: goal and baseline, what is proven, one entry per failure (so nobody retries it), the phases, who owns which line. Superseded entries move to `archive/`.
- **Rules file** (`briefs/HOUSE.md`): what every student reads first: the machine rules, the page format and path, the project log.
- **Brief** (`briefs/NAME.md`): one line's frozen plan. **SCHEDULE.md:** the GPU queue.

## 1. The goal and the files

- The /goal is one sentence with a number and a baseline ("1,000 images a second at the same search quality as today's 91").
- Create PLAN.md, the rules file, SCHEDULE.md and the live page (the `local-artifacts` skill), with the goal at the top of PLAN.md and of the page.
- The rules file names the GPU-lock command, the CPU guard that refuses to start (and stops) CPU work while a hold runs, the files frozen during a hold (edits go to a copy, swapped between holds, new hashes in the project log), and the log path. The measurement rules live in the student's agent file; do not restate them.
- Every line must move the goal's number, or it stops.

## 2. Choose the lines: novel, different, few

- **arXiv first, newest year first: mandatory.**
  - Before you formulate a thesis or hand off a line, search arXiv for the current year, then the year before. Use WebSearch in extended mode, then open the abstract or HTML page of every paper you cite.
  - After arXiv, search repos, model cards and issue trackers. Use at least 5 queries in total.
  - List each find with its arXiv id, date, link and a verdict: reuse, already failed, contradicts, or gap. Put the list in the brief.
  - You may split a wide sweep across several students, one topic cluster each. You still read the abstracts of the papers that decide a line yourself.
  - If novelty stays unclear, mark it so: the student's first milestone is to search further and validate.
### How to search the literature (every round, before any thesis)

A web search engine ranks by popularity, so it misses this month's papers. Query arXiv's own API, sorted by submission date, newest first.

1. **Write 15–25 queries from the thesis.** Use its terms and their synonyms in three groups:
   - the symptom ("small objects", "fine detail", "motion blur");
   - the mechanism ("high-frequency", "token budget", "RoPE", "latent upsampling");
   - the setting ("video diffusion", "few-step", "reference-to-video", "video editing").

   Combine one term from each group per query.
2. **Run them through the API, newest first, with a date window.** Current year first, then the year before.

   ```sh
   curl -s -G "https://export.arxiv.org/api/query" \
     --data-urlencode 'search_query=abs:"video diffusion" AND abs:"high-frequency" AND submittedDate:[202601010000 TO 202612312359]' \
     --data-urlencode sortBy=submittedDate --data-urlencode sortOrder=descending --data-urlencode max_results=40
   ```

   - **Field prefixes:** `ti:` (title), `abs:` (abstract), `au:` (author), `cat:` (category, e.g. `cat:cs.CV`, `cat:cs.LG`), `all:` (everything).
   - **Phrases** go in double quotes.
   - **Booleans** are `AND`, `OR`, `ANDNOT`; group with parentheses.
   - **Dates** go in `submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM]`.
   - **Paging:** `start=40` gives the next page.
   - **Rate limit:** one request every 3 seconds.
   - **Use `curl -G --data-urlencode`.** Python's urllib can fail on HTTPS certificates on macOS.
3. **Parse and save.** Each Atom `<entry>` has `<id>` (the arXiv id), `<published>`, `<title>` and `<summary>` (the abstract).
   - Deduplicate across queries.
   - Save the round's hits to `literature/round-N.json` in the program folder, with the query that found each one, so the next round only reads what is new.

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
4. **Triage in three passes.**
   - Read the titles and keep the candidates.
   - Read their abstracts (the `<summary>` field).
   - For the papers that decide a line, open the full HTML at `https://arxiv.org/html/<id>` to get the method, the numbers, the limitations, and whether it is training-free.
   - To fetch known papers by id: `curl -s -G "https://export.arxiv.org/api/query" --data-urlencode "id_list=2511.19778,2610.05816"`.
5. **Follow the citations forward.** Newer work that builds on a deciding paper often beats it:

   ```sh
   curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2511.19778/citations?fields=title,year,externalIds&limit=100"
   ```
6. **Check code and weights.** Look for the GitHub link in the abstract or HTML, the project page, and Hugging Face. Then run WebSearch in extended mode for what arXiv doesn't hold: repos, model cards, issue trackers, community nodes, user reports.
7. **Write the verdicts.** In the brief and PLAN.md, record one row per paper: arXiv id, date, link, one-line method, the number that matters, code yes or no, and a verdict (reuse / already failed / contradicts / gap).

- **Different.** No two lines take the same path or touch the same code. Before spawning, compare the new line with the running ones; merge or drop overlaps.
- **Reuse first.** When something published already solves part of a line, the line becomes "adopt and measure".
- **Few, in phases.** Usually 3 to 5 lines at once. Build and measure phases come first and skip the novelty search; improvement and novelty phases need it. Start a phase only when the previous one has its answer; park later ideas in PLAN.md.

## 3. Write the brief and its bars

The line's goal and number, what is already known (numbers, paths, links), the prior-work list (arXiv first, newest year first, each with a verdict), milestones, E1 = the cheapest test that can kill the line, its bars, the quick-test size, the stop rule, and what to report. A brief you hand over is approved; the student stops only at the points its agent file lists.

Write each round's bars before the first run and freeze them. Every bar names five things: **metric · reference · threshold and where it comes from · test set · what happens when it fires**. Three examples:

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
- **Run every bar on the baseline first:** the baseline must pass a quality bar, and physics must allow a speed bar. "Within noise" means a measured A/A spread (two runs of the same build); a deterministic system has none.
- **Judge the method, not luck:** when the input changes the number (speculative acceptance, seeds, sampling), the bar uses the input-independent one (fixed seeds, fixed-token steps) and only reports the other.
- **The pass bar is what ships; the kill bar ends the line.** The stop rule is the deliverable done or a kill bar fired. A hold count is a budget cap: hitting it means report and ask, not done.

## 4. Spawn the students

- Students are always the `research-student` agent type. Audits and cold reads use a fresh general-purpose agent. No other custom types.
- Each spawn gets a persona fitting the line ("a senior OpenAI deep-learning engineer", "a senior GPU kernel engineer") and a model: Sonnet for well-specified experiment runs, Opus at effort high for hard or open-ended lines.
- The spawn prompt says only who the student is and which files to read (rules file, PLAN.md, SCHEDULE.md, its brief), so a restart costs nothing.

## 5. Run the GPU

- Assume one shared GPU and shared CPU cores. Keep SCHEDULE.md current: one hold at a time, 10 to 15 minutes each, the next one marked NEXT.
- When a hold ends, give the GPU to the next ready student at once. An idle GPU is your failure.

## 6. Check, steer, re-task, stop

- Check at every student notification, and between them on a timer (a CronCreate job every 5 minutes, or a Monitor on SCHEDULE.md and the project log): the queue, the result folders, each student's "Now:" block.
- **Audit against the literature: mandatory.** When a student reports a finding, proposes a thesis, or a line is about to be called done, check it against arXiv, newest year first, before you accept it.
  - If it is already published, the line becomes "adopt and measure", and the page cites the paper.
  - If a paper contradicts it, re-test before anything builds on it.
  - Audit work done so far the same way: earlier conclusions in PLAN.md are re-checked when a newer paper touches them.
- **Judge gross defects, not small scores.** The automatic judge looks only for clear, measurable failures of the task's output, each against the source, the baseline or a fixed check set. Write the list per task before the first run (examples by task in `example.md`):
  - **video:** pose off, a missing or extra limb, the face lost, overlays painted in, big timing slips, visible joins;
  - **images:** a missing or extra object or finger, a broken face, garbled text, the subject not there;
  - **LLMs and text:** wrong answers on a fixed check set, broken output format, repetition loops, truncation;
  - **search and embeddings:** known pairs falling out of the top k, empty or duplicate results;
  - **kernels and speed work:** outputs past a stated tolerance against the reference, crashes, OOM, a speed-up that isn't there.

  A lever dies only for one of those, for a visible or obvious loss the owner confirms, or for no measured speed or memory gain (below twice the measured A/A spread) unless it makes the code simpler. Small exact gains are kept and stacked on one branch, each gated alone, the stack measured end to end: ten 1 % levers are 10 %. A gain too small to pay for the code it adds is a loss. Small score deltas (identity −0.02, sharpness −5 %, perplexity +0.1, top-1 between 90 and 100 %) are reported for ranking, never a verdict, so never set a kill bar on them (§3). A tight numeric bar that kills a working lever is a recurring failure.
- Every student pays rent. Judge each one by evidence (holds used and wasted, rules broken, expected against measured numbers, findings) and do one of three things: steer it, give it something new when its line is promising, or stop it when it adds nothing, overlaps another line, or its kill bar fired.
- Write each steer into the brief as a dated revision, then send one message pointing at it, so a restarted student still has it.
- Ask the owner only for decisions that are theirs (quality trade-offs, budget, exceptions), with your recommendation first.

## 7. Clean up what works

- A winning lever is not done until its code is clean. Spawn a fresh general-purpose agent to audit it: it reads every file on the path (the code, not your conclusions) against the owner's code rules (the `unslop` skill) and, for speed goals, the memory path end to end (every copy, allocation, conversion, sync and loop).
- Hand the findings to the student who owns the code, with a lines-of-code budget, and re-measure after the cleanup.

## 8. Results

- One live page, in the format the rules file sets. Default: the goal and baseline, the one comparison table (you update it when a number lands, with the hold and time it came from), a notes list of everything known, then one mini paper per research line.
- **Every student gets an id `S<round>-<nn>` at spawn:** `S1-01` is round 1's first student, `S2-01` round 2's first new one, in spawn order within the round. A student who carries on into a later round keeps their original id. Ids are never reused or renumbered, and they are the student's name everywhere: the page, the index, PLAN.md, SCHEDULE.md, LOG.md lines, card ids and save prefixes.
- **Each student's section is exactly one mini paper, and its title starts with the id:** `📄 S1-03 · <student> · <question or claim> <✅/❌/⏳>`. Body: Now (2 lines), Abstract, Thesis + kill bar, What we did, Results (every card with wall time, speed and memory), What it means, Details. Logs and planning go to the log file, not the page.
- **The page opens with an index section**, before anything else: one line linking the watch-first, program and survey sections, then one block per student paper, in id order, in Markdown (not a table): `### 📄 S<round>-<nn> · [student](link to their section): short title`, then `**Question:**` in one sentence, `**Result so far:**` in one sentence with the headline number, and the GPU or machine plus the model in italics. Add a block the moment you spawn a student, and update its result line when a number lands.
- **Right under the index: a "watch first" section** with the latest full-length outputs side by side. Each one carries its wall time and its speed (render seconds per output second). Results never hide in a folded section.
- **Students never make the owner click.** Claude Code's safety checks stop some shell commands even in bypass mode: `rm`/`rmdir`/`mv`/`find -delete` on an unquoted or possibly-empty variable path, `rm -rf` on globs or `~`, `curl | sh`. Every brief and the rules file say: quote paths as `"${P:?}"/x` or use literal paths, and prefer script files over long one-liners. A prompt the owner has to answer is a bug in the student's command.
- **Compare only within one machine.** Speed and quality comparisons are made between arms on the same hardware, and when bits matter, on the same server process: a restart alone can change the bits. Each machine has its own baseline of the same job. Every row of the comparison table names its GPU.
- **Status words are plain:** `running`, `finished · student idle (can be woken up)`, `stopped (why)`. Never lab jargon like "parked" or "line done".
- **Several machines:** each student always runs on the same machine. The fast machine is production: full-length runs and integrating winning levers. The slower one is the bench: short A/B tests of new levers against its own baseline of the same job. Each machine gets its own baseline, its own lock and its own queue in SCHEDULE.md, and its own row in the index.
- When a line or the program ends, spawn a cold reader: a fresh general-purpose agent on Sonnet, with no context, that reads the page as a computer-science graduate outside the field and lists everything missing, unexplained, oddly worded or strange (a term never defined, a number without its unit or baseline, a figure without a caption, English that reads badly). Hand the list to the authors, fix, and repeat until nothing serious is left.
- Save owner decisions and durable lessons in memory, not details the files already hold.

### The index section (always, first on the page)

A full example page (index, watch first, program, one mini paper) is in `example.md` next to this file.

```mdx
<Section id="index" title="Index · N students, N mini papers" open>
**Start here:** [▶ Watch first](<link>#watch) · [Program](<link>#program) · [Survey](<link>#survey)

### 📄 S1-01 · [student-a](<link>#student-a): short title
**Question:** the one question this student's paper answers.
**Result so far:** one sentence with the headline number (or "running: …").
*GPU or machine · model*

### 📄 S1-02 · [student-b](<link>#student-b): short title
**Question:** …
**Result so far:** …
*GPU or machine · model*

---
**Scheduling:** one line on which machine does what.
</Section>
```

Take `<link>` from `/api/check`'s `links`. Keep one block per student, in the order the owner should read them, and rewrite a block's result line the moment its number lands.
