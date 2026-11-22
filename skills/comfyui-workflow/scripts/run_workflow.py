"""Run a saved ComfyUI workflow (the file the Workflows menu saves) from code, with inputs changed by node title.

  python run_workflow.py krea2-text-to-image --set "Prompt.value=a red car" --set "Seed.seed=7"
  python run_workflow.py krea2-text-to-image --list                 # every settable input, current values, groups
  python run_workflow.py all --check --comfyui ~/ComfyUI            # convert + ComfyUI's own validator, no server, no GPU

Run and --list talk to a running server (--server, default http://127.0.0.1:8188) and read the workflow from its Workflows
menu. --check boots ComfyUI on the CPU from --comfyui (run it with that install's .venv/bin/python) and reads the workflows
from <comfyui>/user/default/workflows. A workflow is a name from that menu (no .json), a path to a .json, or `all` with --check.
Values in --set are JSON when they parse (7, true, "x"), plain text otherwise; "@/path/file" uploads a local picture, clip or
audio file to the server's input folder and uses it."""
import argparse, json, os, random, shutil, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

WIDGET_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}
CONTROL = {"fixed", "increment", "decrement", "randomize"}
# [Agent] Frontend-only node types that carry no work: the frontend drops them when it queues, and so do we.
VIRTUAL = {"Reroute", "PrimitiveNode", "Note", "MarkdownNote"}
SUB_IN, SUB_OUT = -10, -20


MISSING = object()


def layout(info, get):
    """[(name, value)] in the order the frontend stores widgets_values; name None for an extra slot.

    get(name, index) gives the stored value or MISSING; a MISSING value takes the input's default."""
    out = []

    def walk(inputs, prefix):
        for sec in ("required", "optional"):
            for name, spec in inputs.get(sec, {}).items():
                t, opts = spec[0], (spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {})
                if opts.get("forceInput"):
                    continue
                full = prefix + name
                if t == "COMFY_DYNAMICCOMBO_V3":
                    # [Agent] A dynamic combo stores its choice, then the widgets of the chosen option, named
                    # "<combo>.<widget>"; the choice decides which ones follow, so read it before walking on.
                    keys = [o["key"] for o in opts["options"]]
                    v = get(full, len(out))
                    v = opts.get("default", keys[0]) if v is MISSING else v
                    out.append((full, v))
                    walk(next((o.get("inputs", {}) for o in opts["options"] if o["key"] == v), {}), full + ".")
                elif isinstance(t, list) or t in WIDGET_TYPES:
                    v = get(full, len(out))
                    if v is MISSING:
                        # [Agent] Files saved before a node gained a widget have fewer values; the frontend fills the
                        # new ones with their defaults when it loads the file, so we do the same.
                        v = opts["default"] if "default" in opts else (t[0] if isinstance(t, list) and t else (opts.get("options") or [MISSING])[0])
                    out.append((full, v))
                    # [Agent] An INT with control_after_generate (and any INT named seed or noise_seed) stores its
                    # control word right after itself; an upload box stores one placeholder.
                    if opts.get("control_after_generate") or (t == "INT" and name in ("seed", "noise_seed")):
                        out.append((None, get(None, len(out)) if get(None, len(out)) is not MISSING else "fixed"))
                    if opts.get("image_upload"):
                        out.append((None, get(None, len(out)) if get(None, len(out)) is not MISSING else "image"))
    order = info.get("input_order", {})
    walk({sec: {k: info["input"][sec][k] for k in order.get(sec, info["input"].get(sec, {}))} for sec in ("required", "optional") if sec in info["input"]}, "")
    return out


def from_list(wv):
    return lambda name, i: wv[i] if i < len(wv) else MISSING


def widget_values(n, info):
    """name -> value of a node's own widgets (not its subgraph inputs)."""
    wv = n.get("widgets_values")
    if isinstance(wv, dict):
        names = {k for k, _ in layout(info, lambda name, i: MISSING) if k}
        return {k: v for k, v in wv.items() if k in names}
    wv = wv or []
    if n["type"] == "Power Lora Loader (rgthree)":
        # [Agent] rgthree's LoRA list is dynamic rows the server reads as lora_1, lora_2, ... dicts, sent next to the header
        # and "add" button placeholders exactly as the frontend sends them.
        rows = [{k: x for k, x in v.items() if x is not None} for v in wv if isinstance(v, dict) and "lora" in v]
        return {"PowerLoraLoaderHeaderWidget": {"type": "PowerLoraLoaderHeaderWidget"},
                **{f"lora_{i + 1}": v for i, v in enumerate(rows)}, "➕ Add Lora": ""}
    return {k: v for k, v in layout(info, from_list(wv)) if k and v is not MISSING}


def instance_widgets(n, defs):
    """input name -> value for a subgraph instance's widgets, from its widgets_values."""
    d = defs[n["type"]]
    inner = {x["id"]: x for x in d["nodes"]}
    targets = {}
    for l in d["links"]:
        if l["origin_id"] == SUB_IN:
            targets.setdefault(l["origin_slot"], []).append((l["target_id"], l["target_slot"]))
    # [Agent] A subgraph input shows a widget when it feeds a widget inside, and widgets_values follows the subgraph's input
    # order. Older files leave those inputs off the instance's socket list, so the definition is the only reliable order.
    wins = [inp["name"] for k, inp in enumerate(d["inputs"])
            if any(t in inner and ts < len(inner[t].get("inputs", [])) and inner[t]["inputs"][ts].get("widget") for t, ts in targets.get(k, []))]
    wv = list(n.get("widgets_values") or [])
    out, j = {}, 0
    for k, name in enumerate(wins):
        if j >= len(wv):
            break
        out[name] = wv[j]
        j += 1
        # [Agent] A promoted seed can carry its control word; skip it only when the counts say it is there.
        if j < len(wv) and wv[j] in CONTROL and len(wv) - j > len(wins) - k - 1:
            j += 1
    return out


class Level:
    """One graph level: the top workflow or one subgraph instance's expanded body."""

    def __init__(self, nodes, links, defs, prefix="", parent=None, owner=None, mode=0):
        # [Agent] mode is the instance's mode pushed down: inside a bypassed or muted subgraph every node counts as that.
        self.nodes = {n["id"]: n for n in nodes}
        self.prefix, self.parent, self.owner, self.mode = prefix, parent, owner, mode
        # [Agent] Top-level links are lists, subgraph links are dicts; both become target socket -> source socket.
        self.into = {}
        for l in links:
            o, os_, t, ts = (l[1], l[2], l[3], l[4]) if isinstance(l, list) else (l["origin_id"], l["origin_slot"], l["target_id"], l["target_slot"])
            self.into[(t, ts)] = (o, os_)
        self.children = {}
        for n in nodes:
            if n["type"] in defs:
                d = defs[n["type"]]
                m = n.get("mode", 0) if self.mode == 0 else self.mode
                self.children[n["id"]] = Level(d["nodes"], d["links"], defs, f"{prefix}{n['id']}:", self, n, m)

    def walk(self):
        yield self
        for c in self.children.values():
            yield from c.walk()


class Converter:
    def __init__(self, wf, oi):
        self.oi = oi
        self.defs = {s["id"]: s for s in wf.get("definitions", {}).get("subgraphs", [])}
        self.top = Level(wf["nodes"], wf["links"], self.defs)

    def resolve_out(self, lv, nid, slot):
        """What a node's output slot really is: ('node', api_id, slot), ('value', v) or None."""
        if nid == SUB_IN:
            # [Agent] Match by name: the instance's socket when it is wired, else its widget value. Files saved by older
            # frontends list fewer or reordered sockets on the instance than the subgraph defines.
            owner, parent = lv.owner, lv.parent
            name = self.defs[owner["type"]]["inputs"][slot]["name"]
            idx = next((i for i, x in enumerate(owner.get("inputs", [])) if x["name"] == name), None)
            if idx is not None and (owner["id"], idx) in parent.into:
                return self.resolve_out(parent, *parent.into[(owner["id"], idx)])
            w = instance_widgets(owner, self.defs)
            return ("value", w[name]) if name in w else None
        n = lv.nodes[nid]
        mode = n.get("mode", 0) if lv.mode == 0 else lv.mode
        if mode == 2:
            return None
        if n["type"] == "PrimitiveNode":
            return ("value", (n.get("widgets_values") or [None])[0])
        if n["type"] == "Reroute":
            return self.resolve_in(lv, nid, 0)
        if mode == 4:
            # [Agent] A bypassed node hands on the input in the same slot when the types match, else the first input of the
            # output's type, the same rule the frontend uses when it queues.
            t = n["outputs"][slot]["type"]
            ins = n.get("inputs", [])
            hit = next((i for i in [slot, *range(len(ins))] if i < len(ins) and ins[i]["type"] == t), None)
            return None if hit is None else self.resolve_in(lv, nid, hit)
        if nid in lv.children:
            child = lv.children[nid]
            src = child.into.get((SUB_OUT, slot))
            return self.resolve_out(child, *src) if src else None
        return ("node", f"{lv.prefix}{nid}", slot)

    def resolve_in(self, lv, nid, idx):
        if (nid, idx) in lv.into:
            return self.resolve_out(lv, *lv.into[(nid, idx)])
        return None

    def api(self):
        out = {}
        for lv in self.top.walk():
            for nid, n in lv.nodes.items():
                mode = n.get("mode", 0) if lv.mode == 0 else lv.mode
                if n["type"] in VIRTUAL or nid in lv.children or mode in (2, 4):
                    continue
                # [Agent] A type the server doesn't know is a frontend-only helper (group bypasser, label) when nothing is
                # wired to it; wired, it is a missing node pack, and it stays in so the validator names it.
                wired = any(i.get("link") is not None for i in n.get("inputs", [])) or any(o.get("links") for o in n.get("outputs", []))
                if n["type"] not in self.oi and not wired:
                    continue
                info = self.oi.get(n["type"], {"input": {}, "input_order": {}})
                inputs = widget_values(n, info)
                for i, inp in enumerate(n.get("inputs", [])):
                    r = self.resolve_in(lv, nid, i)
                    if r:
                        inputs[inp["name"]] = [r[1], r[2]] if r[0] == "node" else r[1]
                title = n.get("title") or info.get("display_name") or n["type"]
                out[f"{lv.prefix}{nid}"] = {"inputs": inputs, "class_type": n["type"], "_meta": {"title": title}}
        return out


# ---------------------------------------------------------------- edits on the UI graph (before conversion)

def all_nodes(wf):
    """(node, path) for every node, path = 'Instance title / inner title' for nodes inside subgraphs."""
    defs = {s["id"]: s for s in wf.get("definitions", {}).get("subgraphs", [])}

    def rec(nodes, path):
        for n in nodes:
            yield n, path
            if n["type"] in defs:
                yield from rec(defs[n["type"]]["nodes"], path + [n.get("title") or defs[n["type"]].get("name") or str(n["id"])])
    yield from rec(wf["nodes"], [])


def title_of(n, oi, defs):
    if n.get("title"):
        return n["title"]
    if n["type"] in defs:
        return defs[n["type"]].get("name") or n["type"]
    return (oi.get(n["type"]) or {}).get("display_name") or n["type"]


def settable(n, oi, defs):
    """name -> (value, choices or None) for every widget a --set can change on this node."""
    linked = {i["name"] for i in n.get("inputs", []) if i.get("link") is not None}
    if n["type"] in defs:
        return {k: (v, None) for k, v in instance_widgets(n, defs).items() if k not in linked}
    if n["type"] == "PrimitiveNode":
        return {"value": ((n.get("widgets_values") or [None])[0], None)}
    if n["type"] not in oi or n["type"] in VIRTUAL:
        return {}
    info = oi[n["type"]]
    out = {}
    for k, v in widget_values(n, info).items():
        if k in linked or k in ("PowerLoraLoaderHeaderWidget", "➕ Add Lora"):
            continue
        spec = info["input"].get("required", {}).get(k) or info["input"].get("optional", {}).get(k)
        choices = spec[0] if spec and isinstance(spec[0], list) else (spec[1].get("options") if spec and spec[0] == "COMBO" else None)
        out[k] = (v, choices)
    return out


def find_node(wf, oi, title):
    defs = {s["id"]: s for s in wf.get("definitions", {}).get("subgraphs", [])}
    hits = [n for n, path in all_nodes(wf) if title in (title_of(n, oi, defs), " / ".join(path + [title_of(n, oi, defs)]), str(n["id"]))]
    if len(hits) != 1:
        raise SystemExit(f"{len(hits)} nodes titled {title!r}; use --list for the exact titles (inner nodes: 'Subgraph / Node')")
    return hits[0], defs


def resolve(wf, oi, item):
    # [Agent] Titles may contain "=" and "." ("Clothes · off = sheet · on = photo's"), so try every "=" from the left and
    # every "." from the right until a real node title matches: "LoRAs.lora_4.strength=0.8" is node "LoRAs", widget
    # "lora_4", key "strength", value 0.8.
    for i, ch in enumerate(item):
        if ch != "=":
            continue
        parts = item[:i].split(".")
        for cut in range(len(parts) - 1, 0, -1):
            try:
                n, defs = find_node(wf, oi, ".".join(parts[:cut]))
            except SystemExit:
                continue
            return n, defs, parts[cut:], item[i + 1:]
    raise SystemExit(f"--set {item!r}: no node with that title; use --list")


def set_value(wf, oi, item):
    n, defs, path, raw = resolve(wf, oi, item)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw
    name, key = path[0], path[1:]
    linked = {i["name"]: i["link"] for i in n.get("inputs", []) if i.get("link") is not None}
    if name in linked:
        raise SystemExit(f"--set {item!r}: {name!r} is wired from another node; set that node instead (--list shows it)")
    wv = n.get("widgets_values")
    if n["type"] in defs:
        vals = instance_widgets(n, defs)
        if name not in vals:
            raise SystemExit(f"--set {item!r}: subgraph inputs are {list(vals)}")
        # [Agent] Rebuild the list without control words so the new value lands in the right slot.
        vals[name] = value
        n["widgets_values"] = list(vals.values())
        return
    if n["type"] == "PrimitiveNode":
        n["widgets_values"][0] = value
        return
    info = oi[n["type"]]
    if isinstance(wv, dict):
        if name not in widget_values(n, info):
            raise SystemExit(f"--set {item!r}: widgets are {list(widget_values(n, info))}")
        if key:
            wv[name][key[0]] = value
        else:
            wv[name] = value
        return
    if n["type"] == "Power Lora Loader (rgthree)":
        rows = [v for v in wv if isinstance(v, dict) and "lora" in v]
        i = int(name.split("_")[-1]) - 1 if name.startswith("lora_") else -1
        if not 0 <= i < len(rows) or not key:
            raise SystemExit(f"--set {item!r}: use lora_N.on / lora_N.lora / lora_N.strength, N = 1..{len(rows)}")
        rows[i][key[0]] = value
        return
    values = widget_values(n, info)
    # [Agent] A dynamic combo's widgets carry dotted names ("resize_type.multiplier"), so the whole path is the name.
    name = ".".join(path)
    if name not in values:
        raise SystemExit(f"--set {item!r}: widgets are {list(values)}")
    values[name] = value
    # [Agent] Rebuild the stored list from names, so a changed dynamic combo brings its own option's widgets along.
    n["widgets_values"] = [v for _, v in layout(info, lambda k, i: values.get(k, MISSING) if k else MISSING)]


def groups(wf):
    return [g for g in wf.get("groups", []) if g.get("title")]


def set_group(wf, item):
    # [Agent] A group is a box on the canvas: its nodes are the ones whose centre lies inside it, the frontend's own rule.
    # "off" bypasses them (the group bypasser buttons), "mute" mutes them (the group muter), "on" runs them; nodes inside a
    # subgraph follow its node.
    title, _, state = item.rpartition("=")
    hits = [g for g in groups(wf) if g["title"] == title]
    if len(hits) != 1 or state not in ("on", "off", "mute"):
        raise SystemExit(f"--group {item!r}: need 'TITLE=on|off|mute' with one of {[g['title'] for g in groups(wf)]}")
    mode = {"on": 0, "off": 4, "mute": 2}[state]
    defs = {s["id"]: s for s in wf.get("definitions", {}).get("subgraphs", [])}

    def setm(n):
        n["mode"] = mode
        for c in defs.get(n["type"], {}).get("nodes", []):
            setm(c)
    for n in in_group(wf, hits[0]):
        setm(n)


def in_group(wf, g):
    x, y, w, h = g["bounding"]
    return [n for n in wf["nodes"] if x <= n["pos"][0] + n["size"][0] / 2 <= x + w and y <= n["pos"][1] + n["size"][1] / 2 <= y + h]


def group_state(wf, g):
    ms = [n.get("mode", 0) for n in in_group(wf, g)]
    on, off = sum(m == 0 for m in ms), sum(m != 0 for m in ms)
    return "on" if not off else "off" if not on else f"mixed ({on} running, {off} bypassed or muted)"


def list_inputs(wf, oi):
    defs = {s["id"]: s for s in wf.get("definitions", {}).get("subgraphs", [])}
    for n, path in all_nodes(wf):
        s = settable(n, oi, defs)
        if not s:
            continue
        mode = {2: "  [muted]", 4: "  [bypassed]"}.get(n.get("mode", 0), "")
        print(f"{' / '.join(path + [title_of(n, oi, defs)])}  ({n['type'] if n['type'] not in defs else 'subgraph'}, id {n['id']}){mode}")
        for k, (v, choices) in s.items():
            c = "" if not choices else f"   one of {len(choices)}: " + (" | ".join(map(str, choices)) if len(choices) <= 8 else " | ".join(map(str, choices[:6])) + " | ...")
            print(f"  {k} = {json.dumps(v, ensure_ascii=False)[:160]}{c}")
    gs = groups(wf)
    if gs:
        print("groups (--group 'TITLE=on|off|mute'; off = bypass):", "; ".join(f"{g['title']} = {group_state(wf, g)}" for g in gs))


def random_seeds(api):
    # [Agent] rgthree's Seed node stores -1 for "random each run" and the frontend draws the number when it queues;
    # we draw it here so the seed that ran is printed and can be reused.
    for k, v in api.items():
        if v["class_type"] == "Seed (rgthree)" and v["inputs"].get("seed") in (-1, -2, -3):
            v["inputs"]["seed"] = random.randint(0, 2**50)
            print(f"seed {v['_meta']['title']} = {v['inputs']['seed']}")


# ---------------------------------------------------------------- server and CPU check

def call(server, path, body=None):
    req = urllib.request.Request(server + path, json.dumps(body).encode() if body is not None else None, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")


def upload(server, item):
    """--set "Title.input=@/local/file": send the file to the server's input folder and set the name it got."""
    target, sep, raw = item.rpartition("=@")
    if not sep:
        return item
    p = Path(raw).expanduser()
    if not p.is_file():
        raise SystemExit(f"--set {item!r}: no file {p}")
    # [Agent] /upload/image stores any file (pictures, clips, audio) in input/; overwrite keeps the name stable across runs.
    b = "----run-workflow-boundary"
    body = (f'--{b}\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
            f'--{b}\r\nContent-Disposition: form-data; name="image"; filename="{p.name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + p.read_bytes() + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(server + "/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        got = json.load(r)
    return f"{target}={json.dumps('/'.join(x for x in (got.get('subfolder'), got['name']) if x))}"


def errors_text(api, node_errors):
    lines = []
    for k, v in node_errors.items():
        t = api.get(k, {}).get("_meta", {}).get("title", k)
        for e in v.get("errors", []):
            lines.append(f"  {t} (id {k}): {e.get('message')}: {e.get('details', '')}"[:400])
    return "\n".join(lines)


def boot(comfyui):
    # [Agent] ComfyUI on the CPU in this process: every node pack loads, nothing touches the GPU, no port opens. The node
    # schemas come out the way /object_info serves them, and the validator is the one /prompt runs.
    import asyncio
    os.chdir(comfyui)
    sys.path.insert(0, comfyui)
    sys.argv = ["main.py", "--cpu"]
    import comfy.options
    comfy.options.enable_args_parsing()
    import nodes, server, execution
    from app.assets.manager import default_asset_manager
    from comfy_api.internal import _ComfyNodeInternal
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ps = server.PromptServer(loop, default_asset_manager())
    loop.run_until_complete(nodes.init_extra_nodes(init_custom_nodes=True))

    def info(cls):
        k = nodes.NODE_CLASS_MAPPINGS[cls]
        if issubclass(k, _ComfyNodeInternal):
            return k.GET_NODE_INFO_V1()
        it = k.INPUT_TYPES()
        return {"input": it, "input_order": {s: list(v) for s, v in it.items()}, "output": k.RETURN_TYPES,
                "display_name": nodes.NODE_DISPLAY_NAME_MAPPINGS.get(cls, cls)}
    oi = {}
    for cls in nodes.NODE_CLASS_MAPPINGS:
        try:
            oi[cls] = info(cls)
        except Exception:
            pass

    def validate(api):
        if hasattr(ps, "node_replace_manager"):
            ps.node_replace_manager.apply_replacements(api)
        ok, err, _, node_errors = loop.run_until_complete(execution.validate_prompt("check", api, None))
        # [Agent] /prompt accepts a graph when one output passes and silently drops the rest; a check that lets that
        # through hides a broken branch, so any node error fails it.
        return ok and not node_errors, err if not ok else {"message": "some outputs fail validation (a run would drop them)"}, node_errors
    return oi, validate


def load(name, server=None, comfyui=None):
    p = Path(name).expanduser()
    if p.suffix == ".json" and p.exists():
        return json.loads(p.read_text())
    if comfyui:
        return json.loads((Path(comfyui) / "user/default/workflows" / f"{name}.json").read_text())
    wf = call(server, "/userdata/" + urllib.parse.quote(f"workflows/{name}.json", safe=""))
    if "nodes" not in wf:
        raise SystemExit(f"no workflow {name!r} on {server}")
    return wf


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workflows", nargs="+", help="workflow name(s) in the Workflows menu, .json path(s), or all (with --check)")
    ap.add_argument("--set", action="append", default=[], metavar="TITLE.INPUT=VALUE")
    ap.add_argument("--group", action="append", default=[], metavar="TITLE=on|off|mute")
    ap.add_argument("--server", default=os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188"))
    ap.add_argument("--comfyui", default=os.environ.get("COMFYUI_DIR"), help="ComfyUI install dir (needed for --check)")
    ap.add_argument("--list", action="store_true", help="print every settable input with its current value, and the groups")
    ap.add_argument("--check", action="store_true", help="convert and validate with ComfyUI's validator on the CPU; queues nothing")
    ap.add_argument("--dry", action="store_true", help="print the API prompt instead of running it")
    a = ap.parse_args()

    if a.check:
        comfyui = str(Path(a.comfyui or "~/ComfyUI").expanduser())
        names = sorted(p.stem for p in (Path(comfyui) / "user/default/workflows").glob("*.json")) if a.workflows == ["all"] else a.workflows
        # [Agent] The boot moves into the ComfyUI folder, so relative paths are fixed first. An @file is copied into
        # input/ the way a run would upload it, so the validator sees the file the run would get.
        names = [str(Path(n).resolve()) if n.endswith(".json") else n for n in names]
        sets = []
        for s in a.set:
            t, _, v = s.partition("=")
            if v.startswith("@"):
                shutil.copy(Path(v[1:]).expanduser(), Path(comfyui) / "input")
                v = json.dumps(Path(v[1:]).name)
            sets.append(f"{t}={v}")
        oi, validate = boot(comfyui)
        bad = 0
        for name in names:
            try:
                wf = load(name, comfyui=comfyui)
                for g in a.group:
                    set_group(wf, g)
                for s in sets:
                    set_value(wf, oi, s)
                api = Converter(wf, oi).api()
                ok, err, ne = validate(api)
            except SystemExit as e:
                ok, err, ne, api = False, {"message": str(e)}, {}, {}
            bad += not ok
            print(f"{name}: {len(api)} nodes {'VALID' if ok else 'INVALID'}", flush=True)
            if not ok:
                print(f"  {err.get('message')} {err.get('details', '')}".rstrip())
                print(errors_text(api, ne))
        raise SystemExit(1 if bad else 0)

    if len(a.workflows) != 1:
        raise SystemExit("one workflow at a time (several only with --check)")
    oi = call(a.server, "/object_info")
    wf = load(a.workflows[0], server=a.server)
    for g in a.group:
        set_group(wf, g)
    for s in a.set:
        set_value(wf, oi, upload(a.server, s) if not (a.list or a.dry) else s)
    if a.list:
        list_inputs(wf, oi)
        return
    api = Converter(wf, oi).api()
    random_seeds(api)
    if a.dry:
        print(json.dumps(api, indent=1, ensure_ascii=False))
        return
    resp = call(a.server, "/prompt", {"prompt": api})
    if "prompt_id" not in resp:
        raise SystemExit(f"{resp.get('error', {}).get('message', resp)}\n{errors_text(api, resp.get('node_errors', {}))}")
    pid = resp["prompt_id"]
    print(f"queued {pid} (position {resp.get('number')})", flush=True)
    if resp.get("node_errors"):
        print(f"WARNING: outputs dropped by the validator:\n{errors_text(api, resp['node_errors'])}", flush=True)
    while pid not in (h := call(a.server, f"/history/{pid}")) or h[pid]["status"].get("completed") is None:
        time.sleep(2)
    status = h[pid]["status"]
    if status["status_str"] != "success":
        m = [x[1] for x in status["messages"] if x[0] == "execution_error"]
        raise SystemExit("failed: " + (f"{m[0].get('node_type')} (id {m[0].get('node_id')}): {m[0].get('exception_message')}" if m else json.dumps(status)[:2000]))
    for nid, out in h[pid]["outputs"].items():
        for f in (x for v in out.values() if isinstance(v, list) for x in v if isinstance(x, dict) and "filename" in x):
            if f.get("type") == "temp":
                continue
            print(f.get("fullpath") or f"{f.get('type', 'output')}/{f.get('subfolder', '')}/{f['filename']}".replace("//", "/"))
    stamps = [m[1]["timestamp"] for m in status["messages"] if m[0] in ("execution_start", "execution_success")]
    print(f"wall_s {(stamps[-1] - stamps[0]) / 1000:.1f}")


if __name__ == "__main__":
    main()
