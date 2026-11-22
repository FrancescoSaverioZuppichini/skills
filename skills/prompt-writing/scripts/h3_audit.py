#!/usr/bin/env python3
# Audit H3 swap prompts: the task checklist (items 1-9 of tasks/character-swap.md) + the fixed template text copied verbatim.
# A prompt whose <Subject 1> says "only her face, identity and hair" is checked against tasks/face-swap.md, any other against tasks/character-swap.md.
# One shot: no timestamp anywhere. Several shots: the task's multi-shot variant ([Shot 1] bare, [Shot N] At MM:SS.mmm, increasing).
# Usage: h3_audit.py <dir with .txt prompts>   Exits 1 if any prompt fails any check. Importable: audit(text), template(task, shots).
import glob, os, re, sys

read_task = lambda name: open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks", name + ".md")).read()
TASKS = {"character": read_task("character-swap"), "face": read_task("face-swap")}
# [Agent] The banned words live once, in the task file's "Banned words" list, so the writer and the audit can never disagree.
# Whole words only: "card" must not fire on "cardigan", and scene words like "parking lines" stay allowed.
def banned(kind):
    words = re.search(r"- " + kind + r": `([^`]*)`", TASKS["character"]).group(1).split(", ")
    return r"\b(" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + r")\b"


STICK, GUIDE, OLD = banned("overlays"), banned("drawing"), banned("source wear")
OUTFIT = re.search(r"- `\{OUTFIT\}`: `([^`]*)`", TASKS["character"]).group(1).lower()
# [Agent] 750 words for one shot; each later shot adds its fixed block (~35 words) and its own moves.
MAX_WORDS, PER_LATER_SHOT = 750, 150
SHOT = r"\[Shot (\d+)\](?: At (\d{2}):(\d{2}\.\d{3}),)?"
PER_SHOT = ("TIME", "SCENE", "FRAMING", "MOVES", "CAMERA")


def template(task, shots=1):
    # [Agent] The task's template for a clip with `shots` shots. Both the audit and the prompt node build it here, so the
    # multi-shot wording lives once, in the task file. Later shots get their own slots ({SCENE_2}, {TIME_2}, …); shared
    # slots such as {OUTFIT_LOCK} keep their name.
    tpl = re.search(r"### Template\n.*?```\n(.*?)```", task, re.S).group(1)
    if shots == 1:
        return tpl
    later = re.search(r"- Later shot: `([^`]*)`", task)
    if not later:
        raise ValueError("this task has no multi-shot variant")
    one, many = re.search(r"- Closing sentence: `([^`]*)` becomes `([^`]*)`", task).groups()
    blocks = " ".join(re.sub(r"\{(" + "|".join(PER_SHOT) + r")\}", lambda m: "{%s_%d}" % (m.group(1), k), later.group(1).replace("{N}", str(k))) for k in range(2, shots + 1))
    tags = ", ".join(f"[Shot {k}]" for k in range(1, shots + 1))
    return tpl.replace("(throughout [Shot 1])", f"(throughout {tags})").replace("{CAMERA}", "{CAMERA} " + blocks, 1).replace(one, many)


def sec(t, name):
    m = re.search(name + r":\s*\n(.*?)(?=\n[a-z_]+:\s*\n|\Z)", t, re.S)
    return m.group(1) if m else ""


SKIP = lambda x: x.endswith(":") or "original sound" in x or "audio reuse" in x or "sound remain" in x or x == "N/A"
pat = lambda x: r".+?".join(re.escape(re.sub(r"\s+", " ", q)) for q in re.split(r"\{[^}]*\}", x))
norm = lambda s: re.sub(r"\s+", " ", s)


# [Agent] Fixed text = every sentence of the template without a {slot}. Sound sentences are skipped because the no-sound
# variant legitimately rewrites them. Sentences holding a {slot} are still mostly fixed text, so they are checked as
# patterns where each slot may be any text.
def fixed_text(tpl):
    sents = [x.strip() for x in re.split(r"(?<=[.;])\s+|\n", tpl) if x.strip()]
    fixed = [x for x in sents if "{" not in x and not SKIP(x)]
    slotted = [(x, re.compile(pat(x), re.S)) for x in sents if "{" in x and not SKIP(x) and len(re.sub(r"\{[^}]*\}", "", x).strip()) > 12]
    return fixed, slotted


def shots_ok(dd):
    # [Agent] Official format: [Shot 1] has no timestamp; every later shot opens with "At MM:SS.mmm," and the cut times
    # strictly increase. Moves inside a shot stay prose, so the shot tags hold the only timestamps.
    tags = re.findall(SHOT, dd)
    times = [int(m) * 60 + float(s) for _, m, s in tags[1:] if s]
    return (bool(tags) and [int(n) for n, _, _ in tags] == list(range(1, len(tags) + 1)) and not tags[0][2]
            and len(times) == len(tags) - 1 and all(a < b for a, b in zip([0] + times, times))
            and len(re.findall(r"\b\d{2}:\d{2}(\.\d+)?\b", dd)) == len(tags) - 1), len(tags)


def sound_ok(t, su, vret):
    keeps = "[video editing + audio reuse]" in su
    if keeps:
        return "(shot length and original sound)" in vret and "The original sound of <Video 1>:" in t
    return ("original sound" not in t.lower() and "(shot length): partially_preserved - the shot length remains" in vret
            and su.strip().startswith("[video editing]"))


def audit(t):
    tl = t.lower()
    sd, ra, su, dd = (sec(t, k) for k in ("subject_definitions", "retention_analysis", "summary", "detailed_description"))
    kind = "face" if "only her face, identity and hair" in sd else "character"
    shots_pass, n = shots_ok(dd)
    try:
        fixed, slotted = fixed_text(template(TASKS[kind], max(n, 1)))
    except ValueError:
        fixed, slotted = ["(multi-shot variant missing for this task)"], []
    vdef = " ".join(l for l in sd.splitlines() if l.startswith("<Video 1>")).lower()
    vret = " ".join(l for l in ra.splitlines() if l.startswith("<Video 1>"))
    c = {
        "1 banned: overlays": not re.search(STICK, tl),
        "1 banned: drawing": not re.search(GUIDE, tl),
        "2 Video1 = blur, never appears": "heavy blur" in vdef and "never appears" in vdef,
        "3 Video1 partially, not kept": "partially_preserved" in vret and "not kept" in vret.lower(),
        "4 summary: blur not part": bool(re.search(r"blur[^.]*not part", su.lower())),
        "5 clean line": "the picture is clean, with no blur anywhere" in dd.lower(),
        "5 skin tone": "colour of the blur" in tl or "color of the blur" in tl,
        "1 banned: source wear": not re.search(OLD, tl.replace(OUTFIT, "")),
        # [Agent] The two sound variants are all-or-nothing: either every original-sound line is there, or none is.
        "4 sound lines match one variant": sound_ok(t, su, vret),
        "6 no standalone Picture": not re.search(r"^<Picture \d>", sd + "\n" + ra, re.M),
        "6 woman not fully kept": not re.search(r"<Subject 2>[^\n]*fully_preserved", ra),
        "7 shots + timestamps": shots_pass,
        "9 length <= 750 (+150/later shot)": len(t.split()) <= MAX_WORDS + PER_LATER_SHOT * max(n - 1, 0),
        # [Agent] The outfit sentence dresses her in the sheet's outfit: required in every shot of a character swap (nude jeans
        # renders without it), wrong for a face-only swap, where she keeps her own clothes.
        "8 outfit sentence per shot": tl.count("she wears the outfit of <subject 1> in every frame:") == (n if kind == "character" else 0),
    }
    miss = [x for x in fixed if norm(x) not in norm(t)] + [x for x, rx in slotted if not rx.search(norm(t))]
    c["9 fixed text verbatim"] = not miss
    return c, miss, kind, n


if __name__ == "__main__":
    rows = []
    for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.txt"))):
        t = open(f).read()
        rows.append((os.path.basename(f)[:-4], len(t.split()), *audit(t)))
    if not rows: sys.exit("no .txt prompts in " + sys.argv[1])
    w = max(len(k) for k in rows[0][2]) + 2
    print("check".ljust(w) + "".join(r[0][-6:].ljust(7) for r in rows))
    for k in rows[0][2]:
        print(k.ljust(w) + "".join(("✅" if r[2][k] else "❌").ljust(7) for r in rows))
    print("words".ljust(w) + "".join(str(r[1]).ljust(7) for r in rows))
    print("shots".ljust(w) + "".join(str(r[5]).ljust(7) for r in rows))
    print("template".ljust(w) + "".join(r[4][:4].ljust(7) for r in rows))
    for name, _, _, miss, _, _ in rows:
        for m in miss: print(f"{name} changed fixed text: {m[:140]}")
    sys.exit(0 if all(all(r[2].values()) for r in rows) else 1)
