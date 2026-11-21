#!/usr/bin/env python3
# Audit H3 swap prompts (blur + drawn pose, full redraw): the checklist + the fixed template text copied verbatim.
# A prompt whose <Subject 1> says "only her face, identity and hair" is checked against tasks/face-swap.md, any other against tasks/character-swap.md.
# Usage: h3_audit.py <dir with .txt prompts>   Exits 1 if any prompt fails any check.
import argparse, glob, os, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("dir")
A = ap.parse_args()

read_task = lambda name: open(os.path.join(os.path.dirname(__file__), "..", "tasks", name + ".md")).read()
TASK = read_task("character-swap")
# [Agent] Whole words only: "card" must not fire on "cardigan" or "discard", nor "lines" on lane lines in a scene.
STICK = r"\b(stickers?|overlays?|captions?|speech bubbles?|on-screen|cards?)\b"
# [Agent] Rule 8 for any clip: common garment, footwear, jewellery and accessory words. The character's own outfit text is removed
# first, so naming her outfit never trips it. A word list cannot be complete; rule 8 is still checked by eye.
OLD = (r"\b(corsets?|garters?|chokers?|stockings?|pvc|latex|tattoos?|blouses?|necklaces?|pendants?|buns?|ponytails?|updo|braids?|"
       r"sneakers?|trainers|boots?|heels|sandals|shoes|socks|jeans|trousers|pants|sweatpants|joggers|leggings|shorts|hoodies?|"
       r"sweaters?|jumpers?|cardigans?|jackets?|coats?|t-shirts?|tank tops?|crop tops?|sports bras?|bras?|bikinis?|dress|dresses|"
       r"earrings?|bracelets?|rings?|lanyards?|gloves?|glasses|sunglasses|hats?|scrunchies?|hair ties?|belts?)\b")
# [Agent] Anything that names the drawing on the input: naming it, even to exclude it, is what made H3 paint it.
GUIDE = r"\bskeleton|\bkeypoints?\b|\bguides?\b|\bdrawn\b|\bdrawing\b|\b(face|white|coloured|colored|pose) (dots|marks)\b|\bdots\b|\b(pose|drawn) lines?\b"
OUTFIT = re.search(r"- `\{OUTFIT\}`: `([^`]*)`", TASK).group(1).lower()
MAX_WORDS = 750

def sec(t, name):
    m = re.search(name + r":\s*\n(.*?)(?=\n[a-z_]+:\s*\n|\Z)", t, re.S)
    return m.group(1) if m else ""

SKIP = lambda x: x.endswith(":") or "original sound" in x or "audio reuse" in x or "sound remain" in x or x == "N/A"
pat = lambda x: r".+?".join(re.escape(re.sub(r"\s+", " ", q)) for q in re.split(r"\{[^}]*\}", x))
norm = lambda s: re.sub(r"\s+", " ", s)

# [Agent] Fixed text = every sentence of the task's template without a {slot}. Sound sentences are skipped because the
# no-sound variant legitimately rewrites them. Sentences holding a {slot} are still mostly fixed text, so they are checked
# as patterns where each slot may be any text.
def fixed_text(task):
    tpl = re.search(r"### Template\n.*?```\n(.*?)```", task, re.S).group(1)
    sents = [x.strip() for x in re.split(r"(?<=[.;])\s+|\n", tpl) if x.strip()]
    fixed = [x for x in sents if "{" not in x and not SKIP(x)]
    slotted = [(x, re.compile(pat(x), re.S)) for x in sents if "{" in x and not SKIP(x) and len(re.sub(r"\{[^}]*\}", "", x).strip()) > 12]
    return fixed, slotted

TEMPLATES = {"character": fixed_text(TASK), "face": fixed_text(read_task("face-swap"))}

rows = []
for f in sorted(glob.glob(os.path.join(A.dir, "*.txt"))):
    t = open(f).read(); tl = t.lower()
    sd, ra, su, dd = (sec(t, k) for k in ("subject_definitions", "retention_analysis", "summary", "detailed_description"))
    kind = "face" if "only her face, identity and hair" in sd else "character"
    FIXED, SLOTTED = TEMPLATES[kind]
    vdef = " ".join(l for l in sd.splitlines() if l.startswith("<Video 1>")).lower()
    vret = " ".join(l for l in ra.splitlines() if l.startswith("<Video 1>"))
    c = {
        "1 no stickers/overlays": not re.search(STICK, tl),
        "2 drawing never named": not re.search(GUIDE, tl),
        "3 Video1 = blur, never appears": "heavy blur" in vdef and "never appears" in vdef,
        "4 Video1 partially, not kept": "partially_preserved" in vret and "not kept" in vret.lower(),
        "5 summary: blur not part": bool(re.search(r"blur[^.]*not part", su.lower())),
        "6 clean line": "the picture is clean, with no blur anywhere" in dd.lower(),
        "7 skin tone": "colour of the blur" in tl or "color of the blur" in tl,
        "8 source garments unnamed": not re.search(OLD, tl.replace(OUTFIT, "")),
        "9 no standalone Picture": not re.search(r"^<Picture \d>", sd + "\n" + ra, re.M),
        "10 woman not fully kept": not re.search(r"<Subject 2>[^\n]*fully_preserved", ra),
        "11 no timestamps": not re.search(r"\b\d{2}:\d{2}(\.\d+)?\b", dd),
        f"length <= {MAX_WORDS} words": len(t.split()) <= MAX_WORDS,
        # [Agent] The outfit sentence dresses her in the sheet's outfit: required for a character swap (nude jeans renders
        # without it), wrong for a face-only swap, where she keeps her own clothes.
        "14 outfit sentence fits task": ("she wears the outfit of <subject 1> in every frame:" in tl) == (kind == "character"),
    }
    miss = [x for x in FIXED if norm(x) not in norm(t)] + [x for x, rx in SLOTTED if not rx.search(norm(t))]
    c["13 fixed text verbatim"] = not miss
    rows.append((os.path.basename(f)[:-4], len(t.split()), c, miss, kind))

if not rows: sys.exit("no .txt prompts in " + A.dir)
w = max(len(k) for k in rows[0][2]) + 2
print("check".ljust(w) + "".join(r[0][-6:].ljust(7) for r in rows))
for k in rows[0][2]:
    print(k.ljust(w) + "".join(("✅" if r[2][k] else "❌").ljust(7) for r in rows))
print("words".ljust(w) + "".join(str(r[1]).ljust(7) for r in rows))
print("template".ljust(w) + "".join(r[4][:4].ljust(7) for r in rows))
for name, _, _, miss, _ in rows:
    for m in miss: print(f"{name} changed fixed text: {m[:140]}")
sys.exit(0 if all(all(r[2].values()) for r in rows) else 1)
