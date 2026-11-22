#!/usr/bin/env python3
"""Check a ComfyUI UI workflow JSON for the layout mistakes a reviewer catches by eye.

  python3 check_layout.py workflow.json        -> prints problems, or OK; exit 1 on problems
"""
import json
import sys

TITLE_BAR = 32
MAX_TITLE = 25

w = json.load(open(sys.argv[1]))
nodes = {x["id"]: x for x in w["nodes"]}
groups = w.get("groups", [])
links = {l[0]: l for l in w.get("links", [])}


def box(x):
    # [Agent] The stored pos is the top of the body; the title bar is drawn above it, so it counts for overlaps.
    return (x["pos"][0], x["pos"][1] - TITLE_BAR, x["pos"][0] + x["size"][0], x["pos"][1] + x["size"][1])


def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def inside(b, g):
    gx, gy, gw, gh = g["bounding"]
    return gx <= b[0] and b[2] <= gx + gw and gy <= b[1] and b[3] <= gy + gh


problems = []
boxes = {k: box(x) for k, x in nodes.items()}
ids = sorted(boxes)
for i, a in enumerate(ids):
    for b in ids[i + 1:]:
        if overlap(boxes[a], boxes[b]):
            problems.append(f"overlap: {a} '{nodes[a].get('title') or nodes[a]['type']}' x {b} '{nodes[b].get('title') or nodes[b]['type']}'")
# [Agent] "Not touching" is not enough: reviewers reject nodes crammed together. Stacked nodes (sharing x-range) need >= 60 px between the
# bottom of one body and the top of the next title bar; nodes side by side (sharing y-range) need >= 120 px.
MIN_V, MIN_H = 60, 120
for i, a in enumerate(ids):
    for b in ids[i + 1:]:
        A, B = boxes[a], boxes[b]
        if overlap(A, B):
            continue
        x_share = A[0] < B[2] and B[0] < A[2]
        y_share = A[1] < B[3] and B[1] < A[3]
        gap_v = max(B[1] - A[3], A[1] - B[3])
        gap_h = max(B[0] - A[2], A[0] - B[2])
        if x_share and 0 <= gap_v < MIN_V:
            problems.append(f"too close vertically ({int(gap_v)} px): {a} '{nodes[a].get('title') or nodes[a]['type']}' / {b} '{nodes[b].get('title') or nodes[b]['type']}'")
        if y_share and 0 <= gap_h < MIN_H:
            problems.append(f"too close horizontally ({int(gap_h)} px): {a} '{nodes[a].get('title') or nodes[a]['type']}' / {b} '{nodes[b].get('title') or nodes[b]['type']}'")
if groups:
    for k, b in boxes.items():
        if not any(inside(b, g) for g in groups):
            problems.append(f"outside every group: {k} '{nodes[k].get('title') or nodes[k]['type']}' at {nodes[k]['pos']}")
    gb = [g["bounding"] for g in groups]
    for i in range(len(gb)):
        for j in range(i + 1, len(gb)):
            a = (gb[i][0], gb[i][1], gb[i][0] + gb[i][2], gb[i][1] + gb[i][3])
            b = (gb[j][0], gb[j][1], gb[j][0] + gb[j][2], gb[j][1] + gb[j][3])
            if overlap(a, b):
                problems.append(f"group overlap: '{groups[i]['title']}' x '{groups[j]['title']}'")
for k, x in nodes.items():
    t = x.get("title") or ""
    if len(t) > MAX_TITLE:
        problems.append(f"title > {MAX_TITLE} chars: {k} '{t}'")
for lid, l in links.items():
    src, dst = nodes.get(l[1]), nodes.get(l[3])
    if src is None or dst is None:
        problems.append(f"link {lid} points to a missing node: {l}")
        continue
    if l[4] >= len(dst.get("inputs", [])) or dst["inputs"][l[4]].get("link") != lid:
        problems.append(f"link {lid} not registered on the input of node {l[3]}")
    if lid not in (src["outputs"][l[2]].get("links") or []):
        problems.append(f"link {lid} not registered on the output of node {l[1]}")

print("\n".join(problems) if problems else f"OK — {len(nodes)} nodes, {len(groups)} groups, {len(links)} links")
sys.exit(1 if problems else 0)
