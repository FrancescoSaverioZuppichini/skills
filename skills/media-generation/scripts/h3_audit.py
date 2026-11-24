#!/usr/bin/env python3
# Audit H3 swap prompts against their task file: the checklist + the fixed template text copied verbatim.
# Both modes live in tasks/video-swap.md: a prompt whose <Subject 1> says "only her face, identity and hair" is checked against its
# "Face-swap template" section, any other against the rest of the file (the character swap). One shot: no timestamp. Several: [Shot 1] bare, [Shot N] At MM:SS.mmm, increasing.
# Moves: one "(at X s)" sentence every 0.5 s from 0.0 on the clip's clock; <d> words only with the lip-sync sentence.
# Usage:
#   h3_audit.py <dir of .txt prompts> [--seconds S]           audit whole prompts
#   h3_audit.py --slots <dir> [--seconds S] [--no-sound]      build the character-swap prompt from one .txt per Clip prompt box
#                                                             (scene_short, kept, …, later_shots) exactly as the workflow's node
#                                                             does, print it, audit it
# --seconds = the clip's length: the word limit grows with it. Exits 1 on any miss.
# Importable: audit(text, seconds=None), template(task, shots), fill(slots, shots, times, sheet, audio, sound).
import argparse, glob, math, os, re, sys

read_task = lambda name: open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks", name + ".md")).read()
# [Agent] The face-swap section carries its own Template, Later shot and Closing sentence lines; cutting it out of the file leaves
# [Agent] the character swap's, so every regex below finds exactly one of each per mode.
SWAP = read_task("video-swap")
FACE = re.search(r"\n## Face-swap template\n(.*?)(?=\n## |\Z)", SWAP, re.S).group(1)
TASKS = {"character": SWAP.replace(FACE, ""), "face": FACE}
# [Agent] The banned words live once, in the task file's "Banned words" list, so the writer and the audit can never disagree.
# Whole words only: "card" must not fire on "cardigan", and scene words like "parking lines" stay allowed.
def banned(kind):
    words = re.search(r"- " + kind + r": `([^`]*)`", TASKS["character"]).group(1).split(", ")
    return r"\b(" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + r")\b"


STICK, GUIDE, OLD = banned("overlays"), banned("drawing"), banned("source wear")
SHEET = {k: re.search(r"- `\{%s\}`: `([^`]*)`" % k, TASKS["character"]).group(1) for k in ("OUTFIT", "CHARACTER_LINE", "OUTFIT_LOCK")}
# [Agent] 750 words fit a 3 s single shot. A later shot adds its fixed block and its own scene; every second past 3 s adds
# room for about 1.5 more move sentences, so long clips are not squeezed into a 3 s budget.
MAX_WORDS, PER_LATER_SHOT, PER_SECOND = 750, 150, 45
SHOT = r"\[Shot (\d+)\](?: At (\d{2}):(\d{2}\.\d{3}),)?"
PER_SHOT = ("TIME", "SCENE", "FRAMING", "MOVES", "CAMERA")


def template(task, shots=1):
    # [Agent] The task's template for a clip with `shots` shots. The audit, the slot builder and the prompt node all build it
    # here, so the multi-shot wording lives once, in the task file. Later shots get their own slots ({SCENE_2}, {TIME_2}, …);
    # shared slots such as {OUTFIT_LOCK} keep their name.
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


SKIP = lambda x: x.endswith(":") or "original sound" in x or "audio reuse" in x or "sound remain" in x or "soundtrack itself is unchanged" in x or x == "N/A"
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
    # strictly increase. The moves' own times are "(at X s)" anchors, so MM:SS times belong to the shot tags only.
    tags = re.findall(SHOT, dd)
    times = [int(m) * 60 + float(s) for _, m, s in tags[1:] if s]
    return (bool(tags) and [int(n) for n, _, _ in tags] == list(range(1, len(tags) + 1)) and not tags[0][2]
            and len(times) == len(tags) - 1 and all(a < b for a, b in zip([0] + times, times))
            and len(re.findall(r"\b\d{2}:\d{2}(\.\d+)?\b", dd)) == len(tags) - 1), len(tags)


def rendered(seconds):
    # [Agent] The workflow renders the longest 17n+5 frames at 24 fps that fit in the clip; nothing after that exists in the video.
    return (17 * math.floor((seconds * 24 - 5) / 17) + 5) / 24


def last_anchor(seconds):
    return math.ceil(rendered(seconds) * 2) / 2 - 0.5


def anchors_ok(dd, seconds=None):
    # [Agent] H3 takes her timing from the move list, so every rendered half second gets its sentence: 0.0, 0.5, 1.0, … with no
    # gap, no restart at a cut, and (with --seconds) ending on the render's last half second, not the clip's.
    times = [float(x) for x in re.findall(r"\(at (\d+(?:\.\d+)?) s\)", dd)]
    return bool(times) and times == [k / 2 for k in range(len(times))] and (seconds is None or times[-1] == last_anchor(seconds))


def sound_ok(t, su, vret):
    keeps = "[video editing + audio reuse]" in su
    if keeps:
        return "(shot length and original sound)" in vret and "The original sound of <Video 1>:" in t
    return ("original sound" not in t.lower() and "(shot length): partially_preserved - the shot length remains" in vret
            and su.strip().startswith("[video editing]"))


def limit(shots, seconds=None):
    return MAX_WORDS + PER_LATER_SHOT * max(shots - 1, 0) + PER_SECOND * max((seconds or 0) - 3, 0)


def audit(t, seconds=None, lip_sync=True):
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
    # [Agent] The sheet's own outfit may use any garment word (a new outfit is often jeans or boots): read it from the prompt's
    # two outfit slots and exempt only that text from the source-wear list.
    # [Agent] A face-only swap names the source's own clothes on purpose ({CLOTHES}, "She wears ...."): exempt that sentence too.
    worn = tl
    exempt = re.findall(r"outfit she wears there \(([^)]*)\)", tl) + re.findall(r"she wears the outfit of <subject 1> in every frame: ([^.]*)\.", tl)
    if kind == "face":
        exempt += re.findall(r"\bshe wears ([^.]*)\.", tl)
    for s in exempt:
        worn = worn.replace(s, "")
    c = {
        "1 banned: overlays": not re.search(STICK, tl),
        "1 banned: drawing": not re.search(GUIDE, tl),
        "2 Video1 = blur, never appears": "heavy blur" in vdef and "never appears" in vdef,
        "3 Video1 partially, not kept": "partially_preserved" in vret and "not kept" in vret.lower(),
        "4 summary: blur not part": bool(re.search(r"blur[^.]*not part", su.lower())),
        "5 clean line": "the picture is clean, with no blur anywhere" in dd.lower(),
        "5 skin tone": "colour of the blur" in tl or "color of the blur" in tl,
        "1 banned: source wear": not re.search(OLD, worn),
        # [Agent] The two sound variants are all-or-nothing: either every original-sound line is there, or none is.
        "4 sound lines match one variant": sound_ok(t, su, vret),
        # [Agent] The lip-sync sentence is a choice per clip (--no-lip-sync): with it she sings along to the vocals she hears,
        # without it her mouth follows the source. Either way it is all or nothing, and never without the sound.
        "4 lip-sync line (with sound)": ("lip-syncs the vocals in the original sound of <video 1>" in tl) == (lip_sync and "audio reuse" in su),
        # [Agent] Sung or spoken words make sense only when she lip-syncs the sound they come from.
        "4 <d> words need the lip-sync line": "<d>" not in tl or "lip-syncs the vocals in the original sound of <video 1>" in tl,
        "6 no standalone Picture": not re.search(r"^<Picture \d>", sd + "\n" + ra, re.M),
        "6 woman not fully kept": not re.search(r"<Subject 2>[^\n]*fully_preserved", ra),
        "7 shots + timestamps": shots_pass,
        "7 moves anchored every 0.5 s": anchors_ok(dd, seconds),
        "9 length (--seconds for clips over 3 s)": len(t.split()) <= limit(n, seconds),
        # [Agent] The outfit sentence dresses her in the sheet's outfit: required in every shot of a character swap (nude
        # renders without it), wrong for a face-only swap, where she keeps her own clothes.
        # [Agent] A face-only swap names her own clothes instead, one "She wears {CLOTHES}." per shot (too short for the fixed-text check).
        "8 outfit / clothes sentence per shot": (tl.count("she wears the outfit of <subject 1> in every frame:") == n) if kind == "character"
            else (tl.count("she wears the outfit of") == 0 and len(re.findall(r"\bshe wears ", tl)) == n),
    }
    miss = [x for x in fixed if norm(x) not in norm(t)] + [x for x, rx in slotted if not rx.search(norm(t))]
    c["9 fixed text verbatim"] = not miss
    miss = [f"changed fixed text: {x}" for x in miss]
    # [Agent] Name the exact banned words that fired, so the writer knows what to rephrase.
    for label, rx, text in (("overlays", STICK, tl), ("drawing", GUIDE, tl), ("source wear", OLD, worn)):
        miss += [f"banned ({label}): {w}" for w in sorted(set(re.findall(rx, text)))]
    return c, miss, kind, n


# [Agent] Slot names and endings exactly as the workflow's Clip prompt node writes them, so --slots previews the very text
# the render gets. Phrases sit before the template's own full stop or comma; sentences stand alone.
BOXES = ("scene_short", "kept", "style", "scene", "framing", "moves", "camera", "light", "sound", "later_shots")
PHRASES = ("SCENE", "KEPT", "LIGHT")


def parse_shots(text):
    shots = []
    for line in filter(None, (l.strip() for l in text.splitlines())):
        m = re.match(r"(%s)\s*:\s*(.*)" % "|".join(PER_SHOT), line)
        if not m:
            raise SystemExit(f"later_shots: every line starts with one of {', '.join(PER_SHOT)} and a colon, got: {line[:80]}")
        if m.group(1) == "TIME":
            shots.append({})
        elif not shots:
            raise SystemExit("later_shots: each shot starts with its TIME line")
        shots[-1][m.group(1)] = m.group(2)
    return shots


def no_sound(text, sound):
    text = text.replace("[video editing + audio reuse]", "[video editing]").replace(", with the original sound", "")
    text = re.sub(r"^<Video 1> \(shot length and original sound\).*$", "<Video 1> (shot length): partially_preserved - the shot length remains; the woman and the blur are not kept.", text, flags=re.M)
    return re.sub(r"(overall_soundscape:\n).*", lambda m: m.group(1) + sound.rstrip(".") + ".", text)


def fill(slots, shots, times, sheet, audio, sound):
    vals = {k: slots[k] for k in ("SCENE_SHORT", "KEPT", "STYLE", "LIGHT")}
    for k, shot in enumerate(shots, 1):
        vals.update({(s if k == 1 else f"{s}_{k}"): shot[s] for s in ("SCENE", "FRAMING", "MOVES", "CAMERA")})
    for k, v in vals.items():
        v = " ".join(v.split())
        vals[k] = v[:1].lower() + v[1:].rstrip(" .,;") if k.split("_")[0] in PHRASES else v if v.endswith((".", "!", "?")) else v + "."
    vals.update({k: v.strip() for k, v in sheet.items()}, SOUND=sound.strip().rstrip(".") or "the sound recorded with the clip",
                **{f"TIME_{k}": t for k, t in enumerate(times, 2)})
    text = template(TASKS["character"], len(shots))
    for k, v in vals.items():
        text = text.replace("{%s}" % k, v)
    return (text if audio else no_sound(text, sound.strip())).strip() + "\n"


def from_slots(d, audio):
    box = lambda k: open(os.path.join(d, k + ".txt")).read().strip() if os.path.exists(os.path.join(d, k + ".txt")) else ""
    later = parse_shots(box("later_shots"))
    shots = [{k.upper(): box(k) for k in ("scene", "framing", "moves", "camera")}] + later
    if empty := [f"shot {i}: {k}" for i, s in enumerate(shots, 1) for k in PER_SHOT[1:] if not s.get(k, "").strip()] + [k for k in ("scene_short", "kept", "style", "light") if not box(k)]:
        raise SystemExit(f"empty slots: {', '.join(empty)}")
    if not audio and not box("sound"):
        raise SystemExit("--no-sound needs sound.txt: what the new video should sound like")
    # [Agent] A new sheet's values go in outfit.txt / character.txt / outfit_lock.txt; without them the task file's apply.
    sheet = {K: box(k) or SHEET[K] for k, K in (("outfit", "OUTFIT"), ("character", "CHARACTER_LINE"), ("outfit_lock", "OUTFIT_LOCK"))}
    slots = {k.upper(): box(k) for k in ("scene_short", "kept", "style", "light")}
    return fill(slots, shots, [s["TIME"] for s in later], sheet, audio, box("sound"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?", help="a folder of whole .txt prompts")
    ap.add_argument("--slots", help="a folder with one .txt per Clip prompt box: builds and audits the character-swap prompt")
    ap.add_argument("--seconds", type=float, help="the clip's length in seconds (the word limit grows past 3 s)")
    ap.add_argument("--no-sound", action="store_true", help="--slots only: the no-sound variant (sound.txt = the new soundscape)")
    ap.add_argument("--no-lip-sync", action="store_true", help="the prompt drops the lip-sync sentence (she does not sing along)")
    a = ap.parse_args()
    if a.slots:
        text = from_slots(a.slots, not a.no_sound)
        open(os.path.join(a.slots, "prompt.full"), "w").write(text)
        print(text)
        prompts = [("prompt", text)]
    elif a.dir:
        prompts = [(os.path.basename(f)[:-4], open(f).read()) for f in sorted(glob.glob(os.path.join(a.dir, "*.txt")))]
    else:
        ap.error("give a folder of prompts or --slots <folder>")
    if not prompts: sys.exit("no .txt prompts in " + a.dir)
    rows = [(name, len(t.split()), *audit(t, a.seconds, not a.no_lip_sync)) for name, t in prompts]
    w = max(len(k) for k in rows[0][2]) + 2
    print("check".ljust(w) + "".join(r[0][-6:].ljust(7) for r in rows))
    for k in rows[0][2]:
        print(k.ljust(w) + "".join(("✅" if r[2][k] else "❌").ljust(7) for r in rows))
    print("words".ljust(w) + "".join(f"{r[1]}/{int(limit(r[5], a.seconds))}".ljust(9) for r in rows))
    print("shots".ljust(w) + "".join(str(r[5]).ljust(7) for r in rows))
    print("template".ljust(w) + "".join(r[4][:4].ljust(7) for r in rows))
    if a.seconds:
        print(f"render: {rendered(a.seconds):.2f} s of {a.seconds:.2f} s; last anchor (at {last_anchor(a.seconds):.1f} s)")
    for name, _, _, miss, _, _ in rows:
        for m in miss: print(f"{name} {m[:160]}")
    sys.exit(0 if all(all(r[2].values()) for r in rows) else 1)
