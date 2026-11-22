"""Run a saved ComfyUI workflow (the UI file from the Workflows menu) from code, with inputs changed by node title.
  python run_workflow.py minimax-h3-reference-to-video --set "Seed.noise_seed=7" [--server http://127.0.0.1:8188]
The UI file is read from the server (or a local .json path), turned into an API prompt with the server's /object_info, posted, and
waited on. Prints every output file and the render time. Values are JSON when they parse (7, true, "x"), plain text otherwise."""
import argparse, json, time, urllib.parse, urllib.request
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("workflow", help="name in the Workflows menu (without .json) or a path to a UI .json")
ap.add_argument("--set", action="append", default=[], metavar="TITLE.INPUT=VALUE")
ap.add_argument("--server", default="http://127.0.0.1:8188")
ap.add_argument("--dry", action="store_true", help="print the API prompt instead of running it")
a = ap.parse_args()


def call(path, body=None):
    req = urllib.request.Request(a.server + path, json.dumps(body).encode() if body is not None else None, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def widget_names(info):
    # [Agent] The order the frontend stores widgets_values in: declared order; an INT with control_after_generate and an image
    # upload box each store one extra value right after their own.
    names = []
    for sec in ("required", "optional"):
        for name in info["input_order"].get(sec, []):
            spec = info["input"][sec][name]
            opts = spec[1] if len(spec) > 1 else {}
            if isinstance(spec[0], list) or spec[0] in ("INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"):
                names += [name] + [None] * (bool(opts.get("control_after_generate")) + bool(opts.get("image_upload")))
    return names


def to_api(wf, oi):
    if wf.get("definitions", {}).get("subgraphs"):
        raise SystemExit("subgraphs are not supported")
    nodes = {n["id"]: n for n in wf["nodes"]}
    link = {l[0]: (l[1], l[2], l[3], l[4]) for l in wf["links"]}
    into = {(d, ds): (s, ss) for s, ss, d, ds in link.values()}

    def source(nid, slot):
        # [Agent] Follow a link back through nodes that do no work: a Reroute or a bypassed node (mode 4) passes on its input of
        # the same type, the way the frontend does it when it queues. A frontend primitive gives nothing: its value already sits
        # in the widget it feeds.
        n = nodes[nid]
        if n["type"] not in oi and n["type"] != "Reroute":
            return None
        if n["type"] == "Reroute" or n.get("mode") == 4:
            t = n["outputs"][slot]["type"]
            for i, inp in enumerate(n.get("inputs", [])):
                if (nid, i) in into and (n["type"] == "Reroute" or inp["type"] == t):
                    return source(*into[(nid, i)])
            return None
        return [str(nid), slot]

    api = {}
    for nid, n in nodes.items():
        # [Agent] Frontend-only nodes (notes, primitives that already wrote their value into the widget they feed, group
        # bypassers) have no server class; muted (2) and bypassed (4) nodes do not run.
        if n["type"] not in oi or n.get("mode", 0) in (2, 4):
            continue
        info = oi[n["type"]]
        wv = n.get("widgets_values_named") or n.get("widgets_values") or []
        if isinstance(wv, dict):
            inputs = {k: v for k, v in wv.items() if k in widget_names(info)}
        else:
            inputs = {k: v for k, v in zip(widget_names(info), wv) if k}
        for i, inp in enumerate(n.get("inputs", [])):
            if (nid, i) in into and (src := source(*into[(nid, i)])):
                inputs[inp["name"]] = src
        api[str(nid)] = {"class_type": n["type"], "inputs": inputs, "_meta": {"title": n.get("title") or n["type"]}}
    return api


def override(api, item):
    target, value = item.split("=", 1)
    title, name = target.rsplit(".", 1)
    hit = [k for k, v in api.items() if v["_meta"]["title"] == title or k == title]
    if len(hit) != 1:
        raise SystemExit(f"--set {item!r}: {len(hit)} nodes titled {title!r}")
    try:
        value = json.loads(value)
    except json.JSONDecodeError:
        pass
    api[hit[0]]["inputs"][name] = value


if Path(a.workflow).suffix == ".json" and Path(a.workflow).exists():
    wf = json.loads(Path(a.workflow).read_text())
else:
    wf = call("/userdata/" + urllib.parse.quote(f"workflows/{a.workflow}.json", safe=""))
api = to_api(wf, call("/object_info"))
for item in a.set:
    override(api, item)
if a.dry:
    print(json.dumps(api, indent=1)); raise SystemExit
resp = call("/prompt", {"prompt": api})
if "prompt_id" not in resp:
    raise SystemExit(json.dumps(resp, indent=1)[:3000])
pid = resp["prompt_id"]
while pid not in (h := call(f"/history/{pid}")) or h[pid]["status"].get("completed") is None:
    time.sleep(3)
status = h[pid]["status"]
if status["status_str"] != "success":
    raise SystemExit(json.dumps(status["messages"][-1:], indent=1)[:3000])
for nid, out in h[pid]["outputs"].items():
    for f in (x for v in out.values() if isinstance(v, list) for x in v if isinstance(x, dict) and "filename" in x):
        print(f.get("fullpath") or f"{f.get('type', 'output')}/{f.get('subfolder', '')}/{f['filename']}".replace("//", "/"))
stamps = [m[1]["timestamp"] for m in status["messages"] if m[0] in ("execution_start", "execution_success")]
print(f"wall_s {(stamps[-1] - stamps[0]) / 1000:.1f}")
