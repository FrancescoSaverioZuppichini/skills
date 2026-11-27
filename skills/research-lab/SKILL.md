---
name: research-lab
description: Run a research program as the professor. The /goal is the final research goal (find something new, make something faster, improve a result). Every round runs the same numbered steps: goal and files, measure first (a measurement student calibrates, profiles, dumps real data and freezes the test sets) while the professor runs the big literature sweep (hundreds of papers, GitHub, forums, competing projects) with helper agents, choose novel non-overlapping lines, design the bars, price and schedule the limited machines, brief research-student agents, run cheapest-kill experiments, audit while they run, ship what works on every machine, close the round. Rounds loop on their own: when a round's winners merge, the professor picks the next round's goal and starts it; side quests fill idle machine time. Use whenever a goal needs experiments by several agents, or the user says "research", "students", "professor", "lab" or sets a /goal that needs experiments.
---

# Research lab: you are the professor

Students run the research. You choose the lines, write their briefs, read every result yourself, steer, re-task or stop students, and turn what works into clean, shipped code. You never run experiments yourself: even the round's first measurements are a student's line. You never report a student's claim without reading its result file.

## Words

- **Owner:** the human who set the program's direction. **Program:** a self-running loop of rounds. **Round:** one pass through the steps below, with its own goal.
- **Side quest:** a small line that only fills idle machine time (a competitor benchmark, a calibration, a cheap lever); lowest priority, pre-empted by the critical path.
- **Line:** one path to the goal, owned by one student. A **support line** (measurement, a quality judge) moves no number itself but serves the lines that do.
- **Lever** or **variant:** one concrete change a line tests (a kernel, a format, a setting).
- **Hold:** one booked slot, ≤ 15 minutes, of a machine's scarce resource (a GPU, or the CPUs, disk or network a job saturates). A **hold budget** is a number of holds.
- **Price:** what a lever can move (µs, MiB, quality points), from a measurement or first principles. **Cost:** the machine time an experiment or a line needs.
- **Critical path:** the lines the round's goal waits on; a **side line** is everything else.
- **A/A spread:** the noise of a measurement. Run the baseline 3 times in one window; the spread is max − min of the 3 results, in the metric's units (or as a % of their median). For a long training run it is the spread across 3 seeds; for a deterministic job's outputs it is zero, so its bar is an exact diff.
- **Same window:** within one hold, or one student's consecutive holds on one machine, with no reboot, driver, clock-setting or build change in between.
- **Dumps:** real intermediate data captured from one run on real inputs (tensors, batches, checkpoints, sampled rows, query logs). **Ladder:** a sequence of tests ordered by cost.
- **Pass bar:** what a variant must meet to ship; below it, the variant is "not shipped" (no gain, too slow, does not fit). **Kill bar:** a gross defect or a physical limit; hitting it makes the variant "dead" at once.
- **E1:** a line's first experiment, the cheapest test that can kill it.
- **Finalist:** a variant that survived every rung of its ladder. **Matrix:** one table per machine, a row per variant, a column per measurement in the protocol.

## The files

```
<program>/
  PLAN.md            goal, baseline, proven, failed (with the measured reason), parked, who owns what
  SCHEDULE.md        per machine: the hold queue; at the end, the file-claims table
  LOG.md             one line per hold or finding: "<YYYY-MM-DD HH:MM> <id> <what> <number>"
  briefs/HOUSE.md    the rules file
  briefs/<id>.md     one frozen brief per line, dated revisions appended
  literature/round-N.json   every hit, with the query that found it
  results/<id>/      every result file a number on the page comes from
  work/<id>/         each student's worktree or scratch folder
```

**One home per fact:**
- numbers live in result files, and the page shows them;
- literature verdicts live in `literature/` and the page's Survey section; PLAN.md cites only those that decide a line;
- decisions and failures live in PLAN.md;
- the queue and file claims live in SCHEDULE.md;
- events live in LOG.md.

Superseded entries are deleted, not archived: version control keeps the history.

**The rules file (`briefs/HOUSE.md`) must contain, per machine:**
- how to reach it and where the code lives;
- how commits move between machines;
- the GPU-lock command;
- the cores reserved for CPU work, so builds never compete with a hold;
- how a stale lock is cleared;
- the disk budget for dumps.

It also holds the page path, with the page instructions copied in (students have no skill loader). You write it; what you cannot find on the machines (access, locks, budgets), ask the owner once. Measurement rules stay in the student agent file.

**SCHEDULE.md rows:**
- queue: `| n | <id> | <what>, <stated length> min | QUEUED / RUNNING / DONE <time>: <result> |`;
- file claims: `| <id> | <files> | <since> |`.

## The top rule: you own the map, students own the depth

The broad sweep (what exists, who is doing what: papers, repositories, forums, competing projects) is yours, with helper agents. It happens in round 1 and whenever a round enters unknown territory. A deep dive on a direction that is already known is a survey line for a research student: it returns priced, novelty-checked ideas with their kill tests, not a reading list.

## The program is a loop of rounds

The program never waits for permission to continue:
1. **Each round has one goal:** a sentence with a number and a baseline, derived from the program's direction.
2. **A round ends** when its goal is reached or it plateaus (no lever passed its bars).
3. **Its winners ship and merge** (step 9).
4. **You pick the next round's goal yourself:** the biggest remaining gap, or the best opportunity the round uncovered. Write it in PLAN.md and start the next round.

The owner can redirect at any time. The loop stops only when the owner stops it, or when no next goal is worth a round: then report and propose. While the owner is away, keep going; decisions that are theirs (quality trade-offs, switching to a different model or data, budget) wait for them.

## The round, step by step

1. **Goal and files** (round 1; later rounds update them).
2. **Measure first and do the big literature sweep,** in parallel: a measurement student on the machines, the sweep yourself with helper agents.
3. **Choose the lines,** once the profile and the sweep are in.
4. **Design the bars** and freeze the test sets.
5. **Cost the round and schedule the machines.**
6. **Write the briefs and spawn the students.**
7. **Run the experiments.**
8. **Audit while they run.**
9. **Ship what works.**
10. **Close the round,** then start the next at step 2.


## 1. Goal and files

- The program's direction comes from the /goal; each round's goal is one sentence with a number and a baseline ("1,000 images a second at the same search quality as today's 91"). If the baseline is unknown, the measurement student's first result fills it. For a discovery goal, the number is the measurable answer that would settle the question.
- Create the files above and the live page (the `local-artifacts` skill), with the goal at the top of PLAN.md and of the page.
- Every line must move the goal's number or serve a line that does, or it stops.

## 2. Measure first, and sweep the literature

**Measurement line**, the round's first student (`S<round>-01`, spawned at once by step 6's rules, with its own mini paper). It delivers:

1. **Calibration per machine:** the A/A spread of the baseline, with clocks, power limit and temperature recorded (locked where the rules file allows).
2. **A profile of the baseline:** time per stage (a GPU kernel, a model call, a data loader, a training step, a pipeline node, a query), each against its own floor. The floor is the binding resource's limit: bytes ÷ memory bandwidth, operations ÷ peak, rows ÷ disk or network throughput. Untraced runs give the numbers; profiler runs only attribute them.
3. **Dumps:** the real intermediate data from one run on real inputs, with source and settings recorded. Examples: an LLM's activations and caches, a diffusion model's latents, a search system's query embeddings and candidate lists, a training run's batches and an early checkpoint, a data pipeline's sampled input rows and intermediate tables. Later variants are tested on them first (step 7). Raw dumps stay within the rules file's disk budget and are deleted when the round no longer needs them.
4. **The test sets and the baseline's results on them:** the fixed inputs the bars will use (clips, prompts, labelled queries), split into development inputs (for tuning) and held-out inputs (only for reporting). Step 4 freezes them with the bars, and the measurement student runs every new bar on the baseline.

**The big literature sweep**, at the same time: mandatory in round 1 and whenever a round enters unknown territory, and yours (a known direction gets a survey line instead, see the top rule). It covers hundreds of papers and every other place the answer may already exist: GitHub, model cards, issue trackers, forums (Reddit, Hacker News, Discord logs), blogs and competing projects. Queries come from the goal and from the profile's biggest costs. Split it across **helper agents** (fresh general-purpose agents, one topic cluster or source each) that return lists with verdicts, never across research students; then read the deciding papers and projects yourself. Students receive the verdicts in their briefs. A web search ranks by popularity and misses this month's papers, so query arXiv's own API, newest first:

1. **Write 15–25 queries,** one term from each of three groups per query:
   - the symptom ("motion blur", "loss spikes", "tail latency");
   - the mechanism ("high-frequency", "learning-rate warmup", "columnar scan");
   - the setting ("video diffusion", "LLM pretraining", "ETL pipeline").
2. **Run them newest first, current year, then the year before.** One request every 3 s. On HTTP 429, use arxiv.org's search page and Semantic Scholar instead of waiting. Use `curl -G --data-urlencode` (Python's urllib can fail on HTTPS certificates on macOS).

   ```sh
   curl -s -G "https://export.arxiv.org/api/query" \
     --data-urlencode 'search_query=abs:"video diffusion" AND abs:"high-frequency" AND submittedDate:[202601010000 TO 202612312359]' \
     --data-urlencode sortBy=submittedDate --data-urlencode sortOrder=descending --data-urlencode max_results=40
   ```

   - **Field prefixes:** `ti:`, `abs:`, `au:`, `cat:` (`cat:cs.LG`, `cat:cs.CV`, `cat:cs.DB`, `cat:cs.DC`), `all:`. Systems and data-engineering work often lives in docs, blogs and issue trackers: give step 6 the same weight there.
   - **Syntax:** phrases in double quotes; `AND`, `OR`, `ANDNOT` with parentheses.
   - **Paging:** `start=40`.
   - **Known ids:** `--data-urlencode "id_list=2511.19778,2610.05816"`.
3. **Parse, deduplicate and save** each Atom `<entry>` (`<id>`, `<published>`, `<title>`, `<summary>`) to `literature/round-N.json` with its query, so the next round reads only what is new. A sketch:

   ```python
   import subprocess, xml.etree.ElementTree as ET
   ns = {"a": "http://www.w3.org/2005/Atom"}
   xml = subprocess.run(["curl", "-s", "-G", "https://export.arxiv.org/api/query", "--data-urlencode", f"search_query={q}",
                         "--data-urlencode", "sortBy=submittedDate", "--data-urlencode", "sortOrder=descending",
                         "--data-urlencode", "max_results=40"], capture_output=True).stdout
   for e in ET.fromstring(xml).findall("a:entry", ns):
       arxiv_id = e.find("a:id", ns).text.rsplit("/", 1)[-1]
       date, title = e.find("a:published", ns).text[:10], " ".join(e.find("a:title", ns).text.split())
   ```
4. **Triage in three passes:** titles, then abstracts, then the full HTML (`https://arxiv.org/html/<id>`) of the papers that decide a line (method, numbers, limits).
5. **Follow citations forward:** `curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:<id>/citations?fields=title,year,externalIds&limit=100"`.
6. **Check code, weights and competing projects:** GitHub (repositories and their issues), project pages, Hugging Face, and the forums and blogs where practitioners report numbers. Use the most thorough web search you have, and run the competing projects' own claims through your bars before you believe them.
7. **Write the verdicts:** one row per paper or project in `literature/round-N.json` and the page's Survey section (id, date, link, one-line method, the number that matters, code yes or no, verdict: reuse / already failed / contradicts / gap); briefs and PLAN.md cite the ones that decide a line.

## 3. Choose the lines

- **Priced:** each line names what it can move, from the profile (the gap to the floor) or from first principles.
- **Novel:** check every idea against the sweep. When something published or shipped already solves part of it, the line becomes "adopt and measure". If novelty stays unclear, the student's first milestone is to search further.
- **Different:** no two lines take the same path or edit the same files.
- **Few:** 3 to 5 lines at once, plus their support lines. Ideas that wait for another line's answer are parked in PLAN.md.

## 4. Design the bars

Write every bar before the first run, have the measurement student run it on the baseline, and freeze it with its test sets; change it only by a dated revision. Every bar names **metric · reference · threshold (and where it comes from) · test set · what happens when it fires**, and the direction (≥ or ≤) is stated.

| goal | bar | metric · reference | threshold (source) | test set · when it fires |
|---|---|---|---|---|
| an LLM engine fits 2× the context on the same GPU at today's speed | memory (pass) | peak GPU memory at the new context · absolute | ≤ the card minus a measured headroom (the goal) | one full-length input · not shipped: "does not fit" |
| | speed (pass) | per-step time vs the baseline build, same GPU and window | new ≤ 1/0.85 × baseline (the goal allows 15 %; bytes moved per step give the floor) | the fixed benchmark rows · not shipped |
| a video workflow renders 30 % faster with no visible loss | speed (pass) | wall time per output second vs the baseline workflow, same GPU | new ≤ 0.70 × baseline (the goal) | 5 frozen source clips · not shipped |
| | quality (kill) | gross defects vs the baseline render | face lost, a limb missing or extra, pose off, visible joins | the same 5 clips side by side · dead |
| image search answers 2× faster with the same results | quality (kill) | known pairs in the top 10 vs the baseline index | more misses than the baseline's own count | 500 frozen labelled queries · dead |
| | no regression (pass) | every other benchmark row vs the baseline, same window | no row slower than 5× the A/A spread | the fixed rows · not shipped |
| a training recipe reaches the baseline's accuracy in half the GPU hours | quality (pass) | held-out accuracy at the end vs the baseline recipe, 3 seeds each | new mean ≥ baseline mean − the baseline's seed spread (the goal: same accuracy) | the frozen held-out set · not shipped |
| | stability (kill) | loss curve | NaN or divergence, or a loss spike the baseline never shows | the first 5 % of the run · dead |
| a data pipeline runs 2× faster with the same output | output (kill) | row-level diff vs the baseline's output | any row added, lost or changed (the goal: same output) | a frozen 1 % sample, then a full shard · dead |
| | speed (pass) | rows per second, same machine and window | new ≥ 2 × baseline (the goal) | the same shard · not shipped |

- **A threshold comes from the goal or from physics** (the floor, the memory needed, the measured spread), never picked because it looks tidy.
- **The reference must be able to run.** Where none fits (a size only the new method reaches), use absolute checks plus the trend from where both run.
- **The spread is about measurements, not outputs.** A deterministic system's outputs repeat exactly, but its timings and sampled scores still have a spread.
- **Judge the method, not luck:** when something outside the method moves the number (random seeds, sampling, which inputs happen to be easy, an LLM's draft acceptance), the bar uses a measure that removes it (fixed seeds, the frozen input set, per-step time) and only reports the other.
- **Kill bars are gross defects and physical limits** (no gain only means "not shipped"). Write the defect list per task. Whoever runs the check (the student, a judge line, or a vision model) opens the outputs, and flags only what is clear against the reference:
  - **video:** pose off, a missing or extra limb, the face lost, overlays painted in, big timing slips, visible joins;
  - **images:** a missing or extra object or finger, a broken face, garbled text, the subject not there;
  - **LLMs and text:** wrong answers on the frozen check set, broken output format, repetition loops, truncation;
  - **search and embeddings:** known pairs falling out of the top k, empty or duplicate results;
  - **kernels and numerics:** outputs past a stated tolerance against the reference, NaN, crashes, out of memory;
  - **training:** NaN or divergent loss, spikes the baseline never shows, held-out score below the baseline by more than the seed spread, train/test leakage;
  - **data pipelines:** rows lost, duplicated or changed against the baseline, schema changes, nulls where there were none, non-reproducible output.

  Small score deltas (identity −0.02, sharpness −5 %, perplexity +0.1, top-1 agreement between 90 and 100 %) are reported for ranking, never a kill. A tight numeric bar that kills a working lever is a recurring failure.
- **Small gains stack.** For speed and cost levers:
  - **Keep** a lever if its outputs are unchanged and it is faster by at least 2× the spread, or simpler with no measured loss.
  - It is **not shipped** if it is slower or its gain doesn't pay for the code it adds, and **dead** if it changes outputs it claimed to keep.
  - Winners stack on one branch, each gated alone, and the stack is measured end to end: ten 1 % levers are 10 %.

  For quality levers (a training change, a new method), keep one that beats the baseline on the held-out set by more than the seed spread, and stack them the same way.

## 5. Cost the round and schedule the machines

- **Cost before spawning:** the machine hours each line needs on each machine, from its ladder (step 7). The busiest machine sets the round's length. Say the estimate, then cut or reorder until it is acceptable, and give each line a **hold budget**.
- **Critical path first:** side lines pause when they compete for a critical machine. A paused student keeps its context and resumes by message.
- **Never serialize what can run side by side:** start every job whose inputs exist now. Write the test, validation and benchmark scripts while the code they check is being written. Run the review during the work, not after it. Wire the integration the moment the last piece lands. A plan that is a chain of hand-offs, each waiting on the previous one, wastes hours of wall time.
- **Side quests fill idle time:** when a machine would sit idle, a side quest with a small brief and its own bars takes the slot, and gives it back the moment the critical path needs it.
- **CPU before GPU:** whatever the dumps, the code or arithmetic can decide is decided without a hold. CPU work and builds run on the cores the rules file reserves for them, so they never compete with a hold.
- **Holds:** one at a time per machine, ≤ 15 minutes, booked by the student in SCHEDULE.md with the stated length, stopped as soon as the question is answered. A final table may book a longer hold, stated in its row. A job longer than a hold (a training run, a full data pass) checkpoints and resumes from its last checkpoint; its early checkpoints are rungs of its ladder. You order the queue by the critical path. When a hold ends, the next ready student takes the lock at once: an idle machine is your failure. A job longer than one hold books its consecutive holds in one row, up front.
- **Pay expensive setup once:** one expensive input carries all the probes (a long document holding every question, one video holding every test moment), and its processed state is reused. One model load serves several variants. A scaled-down input (1 % of the rows, a smaller model, a few hundred steps) tests the pipeline before the full size.
- **Two or more different machines:**
  - What depends on the machine (speed, memory, tuning) is measured on each one.
  - Machine-independent work (correctness tests, replays, quality screening, functional runs) goes to whichever machine has the shortest queue. Its comparisons are always against a reference computed on that same machine.
  - Each machine has its own lock, queue, calibration, baseline and log.

## 6. Write the briefs and spawn the students

- **The brief** (`briefs/<id>.md`), frozen once handed over:
  - the line's goal and price;
  - what is known (numbers, paths, links) and the prior-work verdicts;
  - the files the student claims;
  - milestones, E1 (usually a replay on the dumps) and the line's ladder (step 7);
  - the bars from step 4, with their test sets;
  - the hold budget;
  - the stop rule: the deliverable done or a kill bar fired, with the hold budget as a cap (reaching it means report and ask);
  - what to report.
- **Students** are always the `research-student` agent type; audits and cold reads use a fresh general-purpose agent. Each spawn gets:
  - a persona fitting the line ("a senior GPU kernel engineer", "a senior diffusion-model researcher", "a senior search-infrastructure engineer");
  - a model: **Sonnet by default** (every port, package, measurement, integration and review); Opus at effort high only when the student must design. A Sonnet prompt is complete and short: who it is, the files to read, its worktree and scope, the acceptance with numbers, the GPU and lock rules, the shell rules, and the report's length;
  - an id `S<round>-<nn>` in spawn order, never reused or renumbered, used everywhere (page, PLAN.md, SCHEDULE.md, LOG.md, card ids).
- **Token budget:** every tool call resends the agent's whole context, so an agent's cost is its context × its calls, and long-lived agents dominate the bill.
  - One agent, one bounded deliverable: it reports and ends. No lead that integrates for hours; integrating a milestone is its own bounded job for a fresh agent that reads the branch and the notes.
  - No background waiters inside an agent (every wake re-reads the whole context): block on the lock inside one command, or end and be resumed.
  - Quiet tools: few, large tool calls; read with `tail`, `grep` and counts, never whole logs or large files.
  - Sonnet for anything specified (ports, packages, measurements, integration, unslop reviews); Opus only where the student must design.
  - A stopped agent resumes from its saved work by message; never respawn a job that exists.
- **The spawn prompt** says only who the student is and which files to read (rules file, PLAN.md, SCHEDULE.md, its brief), so a restart costs nothing. The student creates its own page section; you add its index block. A judge line is briefed like any other: its deliverable is the defect check on every variant's outputs.
- **Talking to students:**
  - steer with a dated revision appended to the brief plus one message pointing at it (SendMessage);
  - pause or stop with a message, or TaskStop for a student that keeps waking on leftover waiters;
  - resume a stopped student by messaging it (its context is kept);
  - read the logs and queues on demand; a Monitor wakes you on every event, so use one only when few events are expected.
- **No approval prompts:** the rules file tells students to quote paths as `"${P:?}"/x` or write them literally, and to put anything longer than a few lines in a script file. Deleting or moving on an unquoted or possibly-empty variable path, `rm -rf` on globs or `~`, and piping a download into a shell can stop for the owner's approval, and a prompt the owner has to answer is a bug in the student's command.

## 7. Run the experiments

The hardware is the scarce resource, so run as few experiments as the decisions need.
- **Only decisive experiments:** before a run, write what each possible outcome would make you do. If no outcome changes a decision, don't run it.
- **Physics fills what it can:** a variant that cannot fit, or whose cost by arithmetic already misses the bar, gets its matrix cell from that arithmetic or one load attempt, not a run.
- **Reuse before rerunning:** a same-window baseline, a dump or an earlier run of the same build answers the question.

Every variant climbs its ladder and stops at the rung where it dies; that rung and the measured reason fill its matrix cell.

| question | rung 1 (seconds) | rung 2 (minutes) | rung 3 (finalists) |
|---|---|---|---|
| is a component change faster (kernel, model call, index)? | replay of that component on the dumps at the real sizes | quick end-to-end A/B | full benchmark |
| does a compression format keep quality? | replay on the dumps vs the high-precision reference | short input end to end vs the reference | long input + the full quality suite |
| does a variant fit in memory? | one load attempt at the target size | one full-length input | quality runs |
| does a video or image pipeline change break outputs? | 2 seconds of one clip at few steps, checked for gross defects | the 5 frozen clips at full steps | full-length renders |
| does a training change help? | a few hundred steps on a small model: loss falls, no NaN | the full model to an early checkpoint vs the baseline's curve at the same step | full runs, 3 seeds each |
| is a data-pipeline change correct and faster? | 1 % sample, row-level diff vs the baseline | one full shard, diff and rows per second | the whole dataset |
| does an effect exist (a discovery question)? | a cheap probe on existing data or dumps | one controlled experiment on the development inputs | a replication on the held-out inputs |

- **A replay can kill but never prove speed.** A component slower alone is not faster in the system. One faster alone can still slow the whole (cache contention, extra launches or calls, competing work on the same device), so a speed claim needs one end-to-end run on real inputs.
- **Repeats:** if the effect is above 5× the A/A spread, one A/B pair is enough. Otherwise interleave A/B pairs in random order after one warm-up: at least 2 pairs, adding pairs until every pair orders the same way, at most 4; if they still disagree, the result is "no measurable difference". Report the median and the range. Long runs that cannot be interleaved (training) compare seed sets instead of A/B pairs, and deterministic outputs compare by exact diff. The student agent file holds the measurement details.
- **Finalists only** (at most 2 per question) get the full protocol on every machine. The matrix lives in the page's Program section, one table per machine; students fill their rows, and every cell holds a measurement, or the rung, arithmetic or load attempt that ended the variant.

## 8. Audit while they run

- Check at every student notification and on a timer: the queues, the result folders, each student's "Now:" block.
- **Read the result file before you relay any claim,** and open every image or plot yourself.
- **Audit against the literature:** when a student reports a finding or a line is about to be called done, check it against arXiv, newest year first, and against competing projects. Already published or shipped: the line becomes "adopt and measure", cited on the page. Contradicted: re-test before anything builds on it.
- **Steer early:** check each student's work as it lands, not only its reports. A student burning holds, breaking rules, measuring the wrong thing or chasing a dead end gets a dated revision and a message at once.
- **Every student pays rent.** Judge each one by evidence (holds used and wasted, rules broken, expected against measured numbers, findings). Then steer it, give it something new, or stop it when it adds nothing, overlaps another line, or its kill bar fired.
- Ask the owner only for decisions that are theirs (quality trade-offs, budget, switching to a different model or data, exceptions), with your recommendation first.

## 9. Ship what works

- **Clean before done:** a fresh general-purpose agent audits a winning lever. It reads every file on the path (the code, not your conclusions) against the owner's code rules (the `unslop` skill if installed). For speed goals it also reads the memory path end to end; for training, reproducibility (seeds, data order, versions); for data pipelines, idempotence and the row-level diff. The owning student fixes the findings, keeping the change no larger than its gain justifies, and re-measures.
- **Every machine before merge:** a change that lands for one machine is gated on every other machine before it merges (outputs against the reference, the quality checks, the benchmark).
- **Per-machine paths:**
  - faster on every machine → one path;
  - faster on one, slower on another → both paths stay in one code base, picked at runtime by a hardware property (cache size, core count, supported number formats) or a measured per-machine table;
  - each path is gated on its own machine;
  - never fork the code per machine.
- **The deliverable** (a pull request, a recipe, a dataset, a report) has one section per student, written by that student (or by you from its mini paper if it has stopped, said so):
  - what changed, commit by commit;
  - **why**: the measurement that motivated it;
  - the gates it passed;
  - the numbers per machine;
  - what was tried and dropped, with the reason.

  It also says which machine runs which path. The owner accepts it.

## 10. Close the round

- Update PLAN.md (proven, failed with the measured reason, parked) and the page's tables and index.
- **Wipe the round's temporary files** on every machine and in local scratch:
  - **delete:** worktrees, clones and build folders of merged or killed branches; measurement-only binaries and drivers; dumps; raw traces nobody cites; stale scratch scripts;
  - **keep:** result files the page cites, branches of parked work, and the baseline builds still in use;
  - log what was deleted, with sizes.
- Save owner decisions and durable lessons in your persistent memory if you have one (otherwise in PLAN.md), not details the files already hold.
- When a line or the program ends, spawn a cold reader: a fresh general-purpose agent on Sonnet, with no context. It reads the page as a computer-science graduate outside the field and lists everything missing, unexplained or badly worded. Fix what is serious; at most 3 passes.
- Pick the next round's goal (see the loop above), write it in PLAN.md, and go back to step 2.

## The page

One live page (default: the `local-artifacts` skill, whose essentials the rules file copies for students: the `Section`, `Gallery`, `Media`, `Code` and `Note` components, the page check, targeted edits only; without it, one Markdown file with the same sections). The order is fixed:

1. **Index:** a link line to the next three sections, then one Markdown block per student in id order (not a table). Add a block the moment you spawn a student; rewrite its result line when a number lands.
2. **Watch first:** the latest full outputs side by side: renders, answers, loss curves, output diffs, or the headline numbers when nothing is visual.
3. **Program:** goal, baseline, one comparison table per machine (every row names its machine), notes.
4. **Survey:** the literature and competitor verdicts.
5. **One mini paper per student,** newest results on top: title `📄 S1-03 · <student> · <claim> <✅/❌/~/⏳>`; body Now, Abstract, Thesis + kill bar, What we did, Results, What it means, Details.

- **Compare only within one machine,** and when exact outputs matter, within one process: a restart alone can change them.
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

`<link>` is the page URL; the page check prints a link per section. A full example page is in `example.md` next to this file.
