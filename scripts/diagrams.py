#!/usr/bin/env python3
"""diagrams.py — Turn DDD model artifacts (docs/domain/*.md) into Graphviz DOT.

Companion to build_site.py. Reads the *structured* parts of the markdown
artifacts (the Context Map relation table, the Bounded Context list) and emits
DOT source. build_site.py embeds that DOT and a vendored Graphviz-in-WASM
renderer (viz-standalone.js) so the diagrams render in-browser, fully offline.

The markdown stays the source of truth; the DOT (and the SVG the browser draws
from it) is a regenerated artifact. If a model file is missing or unparseable,
the corresponding diagram is simply absent — never a hard error.

Phase A ships one diagram kind: "context-map". More kinds (workflow,
aggregate-event, glossary) plug into the same `dot_for(kind, dir)` entry point.
"""
import hashlib
import os
import re


# ---------- shared ----------
# Fallback palette for contexts that have no explicit color in _site.json.
PALETTE = ["#22c55e", "#3b82f6", "#f59e0b", "#a855f7",
           "#ec4899", "#14b8a6", "#ef4444", "#eab308"]

# Subdomain classification → node emphasis (jig uses weight/style to rank nodes).
SUBDOMAIN_STYLE = {
    "Core":       {"penwidth": "2.6", "style": "filled,bold"},
    "Supporting": {"penwidth": "1.3", "style": "filled"},
    "Generic":    {"penwidth": "1.0", "style": "filled,dashed"},
    "":           {"penwidth": "1.3", "style": "filled"},
}

# Relationship type → short marker shown on the edge (DDD Distilled Ch.4).
REL_ABBR = {
    "Partnership": "P",
    "Shared Kernel": "SK",
    "Customer-Supplier": "C/S",
    "Customer/Supplier": "C/S",
    "Conformist": "CF",
    "Anticorruption Layer": "ACL",
    "Open Host Service": "OHS",
    "Published Language": "PL",
    "Separate Ways": "SW",
    "Big Ball of Mud": "BBoM",
}
# Peer (non-directional) relationships are drawn with arrows on both ends.
PEER_RELS = {"Partnership", "Shared Kernel"}
# Relationships (or any note carrying 🔴) that should read as a problem: red edge.
PROBLEM_RELS = {"Separate Ways", "Big Ball of Mud"}


def _esc(s):
    """Escape a string for use inside a DOT double-quoted label."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _slug(s):
    """Stable, collision-resistant, DOT-safe id for a diagram/graph name.

    Pure-ASCII names keep a readable slug ("Place Order" -> "place-order").
    Non-ASCII names (e.g. Japanese headings 注文 / 請求, which would both reduce
    to an empty slug and collide) get a short hash of the full name appended, so
    distinct names always map to distinct ids.
    """
    s = s.strip()
    base = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    if base and not re.search(r"[^\x00-\x7f]", s):
        return base
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]
    return (base + "-" + h) if base else "x" + h


# Shared dark-theme defaults so every diagram kind looks consistent.
_NODE_DEFAULTS = ('node [shape=box, style=filled, fontname="sans-serif", '
                  'fontsize=12, fillcolor="#1e293b", color="#94a3b8", '
                  'fontcolor="#e2e8f0", margin="0.18,0.10"];')
_EDGE_DEFAULTS = ('edge [fontname="sans-serif", fontsize=10, color="#94a3b8", '
                  'fontcolor="#cbd5e1"];')


def _header(name, rankdir="LR"):
    # quote the graph id: _slug() can yield hyphens (e.g. "wf_place-order"),
    # which Graphviz/viz rejects as a bare identifier.
    return ['digraph "%s" {' % _esc(name),
            '  rankdir="%s";' % rankdir,
            '  bgcolor="transparent";',
            "  " + _NODE_DEFAULTS,
            "  " + _EDGE_DEFAULTS]


def _read(d, name):
    p = os.path.join(d, name)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return fh.read()


# ---------- parsing ----------
def parse_contexts(md):
    """`### {Name} ({Core|Supporting|Generic})` → {name: {"subdomain": kind}}.

    Order is preserved (dicts are insertion-ordered) so colors stay stable.
    """
    out = {}
    if not md:
        return out
    for m in re.finditer(r"^###\s+(.+?)\s*$", md, re.M):
        head = m.group(1).strip()
        name, kind = head, ""
        paren = re.search(r"\(([^)]*)\)\s*$", head)
        if paren:
            inside = paren.group(1)
            for k in ("Core", "Supporting", "Generic"):
                if k.lower() in inside.lower():
                    kind = k
                    break
            name = head[:paren.start()].strip()
        if name:
            out[name] = {"subdomain": kind}
    return out


def _cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_context_map(md):
    """Find the relation table (header has Upstream + Downstream) → list of rows.

    Each row: {upstream, downstream, relation, integration, note}. Columns are
    matched by header name, so extra/reordered columns are tolerated.
    """
    rows = []
    if not md:
        return rows
    lines = md.split("\n")
    for i, line in enumerate(lines):
        if "|" not in line:
            continue
        header = [h.lower() for h in _cells(line)]
        if not any("upstream" in h for h in header):
            continue
        if not any("downstream" in h for h in header):
            continue
        # separator row must follow
        if i + 1 >= len(lines) or "-" not in lines[i + 1]:
            continue

        def col(*names):
            for idx, h in enumerate(header):
                if any(n in h for n in names):
                    return idx
            return None

        ci = {
            "upstream": col("upstream"),
            "downstream": col("downstream"),
            "relation": col("関係", "relation"),
            "integration": col("統合", "integration"),
            "note": col("備考", "note"),
        }
        j = i + 2
        while j < len(lines) and "|" in lines[j] and lines[j].strip():
            cs = _cells(lines[j])

            def get(key):
                k = ci[key]
                return cs[k].strip() if k is not None and k < len(cs) else ""

            up, down = get("upstream"), get("downstream")
            if up and down and up != "---":
                rows.append({
                    "upstream": up, "downstream": down,
                    "relation": get("relation"),
                    "integration": get("integration"),
                    "note": get("note"),
                })
            j += 1
        break
    return rows


def _norm_rel(rel):
    """Map a free-text relation cell to a canonical relationship name."""
    r = rel.strip()
    low = r.lower()
    for canon in REL_ABBR:
        if canon.lower() in low:
            return canon
    # bold markdown / stray markers
    cleaned = re.sub(r"[*`]", "", r).strip()
    return cleaned


# ---------- DOT generation ----------
def context_map_dot(contexts, relations, colors=None):
    """Context Map → DOT. Nodes = bounded contexts, edges = relationships.

    Conventions borrowed from jig and adapted to DDD Distilled:
      - node color from _site.json["colors"] or an auto palette
      - subdomain (Core/Supporting/Generic) → border weight / dash
      - peer relationships (Partnership/Shared Kernel) → arrows both ends
      - problem relationships or 🔴 notes → red edge (jig's cyclic-dep red)
      - relationship marker (C/S, ACL, OHS ...) shown as the edge label
    """
    colors = colors or {}
    # ensure every endpoint is a node, even if not in bounded-contexts.md
    names = list(contexts.keys())
    for rel in relations:
        for end in (rel["upstream"], rel["downstream"]):
            if end not in contexts:
                contexts[end] = {"subdomain": ""}
                names.append(end)

    def color_for(name, idx):
        return colors.get(name) or PALETTE[idx % len(PALETTE)]

    out = ["digraph context_map {",
           '  rankdir="LR";',
           "  bgcolor=\"transparent\";",
           '  node [shape=box, style=filled, fontname="sans-serif", '
           'fontsize=12, fillcolor="#1e293b", color="#94a3b8", '
           'fontcolor="#e2e8f0", margin="0.18,0.10"];',
           '  edge [fontname="sans-serif", fontsize=10, color="#94a3b8", '
           'fontcolor="#cbd5e1"];']

    for idx, name in enumerate(names):
        meta = contexts[name]
        st = SUBDOMAIN_STYLE.get(meta.get("subdomain", ""), SUBDOMAIN_STYLE[""])
        accent = color_for(name, idx)
        is_bbom = "Big Ball of Mud" in (meta.get("subdomain") or "")
        fill = "#7c2d12" if is_bbom else "#1e293b"
        label = name
        sub = meta.get("subdomain")
        if sub:
            # real newline; _esc() turns it into DOT's \n line break
            label = "%s\n(%s)" % (name, sub)
        out.append(
            '  "%s" [label="%s", color="%s", fillcolor="%s", '
            'penwidth="%s", style="%s"];'
            % (_esc(name), _esc(label), accent, fill,
               st["penwidth"], st["style"]))

    for rel in relations:
        up, down = rel["upstream"], rel["downstream"]
        canon = _norm_rel(rel["relation"])
        marker = REL_ABBR.get(canon, canon)
        note = rel.get("note", "")
        integ = rel.get("integration", "")
        parts = [p for p in (marker, integ) if p]
        label = " · ".join(parts)
        is_problem = canon in PROBLEM_RELS or "🔴" in note or "🔴" in label
        attrs = ['label="%s"' % _esc(label)] if label else []
        if canon in PEER_RELS:
            attrs.append('dir="both"')
        if canon == "Anticorruption Layer" or "ACL" in (integ + note):
            attrs.append('arrowhead="diamond"')
        if is_problem:
            attrs.append('color="#ef4444"')
            attrs.append('fontcolor="#fca5a5"')
            attrs.append('penwidth="2.0"')
        out.append('  "%s" -> "%s" [%s];'
                   % (_esc(up), _esc(down), ", ".join(attrs)))

    out.append("}")
    return "\n".join(out)


# ---------- workflows (Phase 9) ----------
# Side-effect category → edge color (the DMMF "I/O at the edges" story).
EFFECT_COLOR = {
    "readonly": "#60a5fa",   # read-only master lookup
    "write":    "#f59e0b",   # state mutation / persistence
    "message":  "#a855f7",   # send-message / fire-and-forget
    "pure":     "#94a3b8",   # no I/O
}


def _classify_effect(text):
    t = text.lower()
    if "send" in t or "messag" in t or "メッセージ" in t:
        return "message"
    if "write" in t or "書" in t:
        return "write"
    if "read" in t or "照会" in t or "参照" in t:
        return "readonly"
    return "pure"


def _split_events(text):
    """`BillableOrderPlaced(成功時), OrderPlaced(常に)` → ['BillableOrderPlaced', ...]."""
    out = []
    for chunk in re.split(r"[,、]", text):
        m = re.match(r"\s*`?([A-Za-z][A-Za-z0-9_]+)", chunk)
        if m and m.group(1).lower() not in ("なし", "none"):
            out.append(m.group(1))
    return out


def _arrows(line):
    """Split a `A → B -> C` chain into ['A','B','C'] (handles →, ->, ⇒)."""
    parts = re.split(r"\s*(?:→|⇒|->)\s*", line.strip())
    return [re.sub(r"[`*]", "", p).strip() for p in parts if p.strip()]


def parse_workflows(md):
    """Parse `## Workflow N: Name (BC)` blocks → list of workflow dicts.

    Each: {name, bc, stages:[type...], steps:[{name,effect,events,fails}...]}.
    """
    if not md:
        return []
    heads = list(re.finditer(r"^##\s+Workflow\s+\d+\s*[:：]\s*(.+?)\s*$", md, re.M))
    out = []
    for k, h in enumerate(heads):
        body = md[h.end():(heads[k + 1].start() if k + 1 < len(heads) else len(md))]
        raw = h.group(1).strip()
        bc = ""
        pm = re.search(r"\(([^)]*)\)\s*$", raw)
        name = raw
        if pm:
            bc = pm.group(1).replace("BC", "").strip()
            name = raw[:pm.start()].strip()

        # stages: first arrow-bearing line inside any fence under "### ステージ"
        stages = []
        sec = re.search(r"###\s+ステージ.*?```(.*?)```", body, re.S)
        if sec:
            for ln in sec.group(1).split("\n"):
                if "→" in ln or "->" in ln or "⇒" in ln:
                    stages = _arrows(ln)
                    break

        # steps
        steps = []
        for sm in re.finditer(r"^####\s+Step\s*\d*\s*[:：]?\s*(.+?)\s*$", body, re.M):
            sname = re.sub(r"[`*]", "", sm.group(1)).strip()
            sbody = body[sm.end():]
            nxt = re.search(r"^####\s", sbody, re.M)
            if nxt:
                sbody = sbody[:nxt.start()]
            effect, events, fails = "pure", [], False

            def field(label):
                m = re.search(r"^\s*[-*]\s*%s\s*[:：]\s*(.+)$" % label, sbody, re.M)
                return m.group(1).strip() if m else ""

            eff = field(r"副作用")
            if eff:
                effect = _classify_effect(eff)
            ev = field(r"発行\s*(?:Event|イベント)")
            if ev:
                events = _split_events(ev)
            err = field(r"エラー")
            out_t = field(r"出力")
            if (err and err.replace("なし", "").strip()) or "Result" in out_t or "Error" in out_t:
                fails = True
            steps.append({"name": sname, "effect": effect,
                          "events": events, "fails": fails})

        if stages or steps:
            out.append({"name": name, "bc": bc, "stages": stages, "steps": steps})
    return out


def parse_workflow_relations(md):
    """`PlaceOrder --[OrderPlaced]--> ShipOrder` lines → [{from,event,to}]."""
    out = []
    if not md:
        return out
    for m in re.finditer(r"([A-Za-z][\w]*)\s*--\[([^\]]*)\]-->\s*([A-Za-z][\w]*)", md):
        out.append({"from": m.group(1), "event": m.group(2).strip(), "to": m.group(3)})
    return out


def workflow_pipeline_dot(wf):
    """One workflow → railway-style pipeline DOT.

    Stage types are the boxes (rising trust left→right). Steps are the edges,
    colored by side-effect (read/write/message/pure). Emitted events hang off
    the produced stage as gold notes. Fallible steps fork to a red error sink
    (Result / OR-type = the DMMF two-track railway).
    """
    stages = wf["stages"]
    steps = wf["steps"]
    out = _header("wf_" + _slug(wf["name"]))
    if not stages:
        # no stage chain to draw
        return None

    for i, st in enumerate(stages):
        edge = "#22c55e" if i == 0 else ("#7dd3fc" if i == len(stages) - 1 else "#94a3b8")
        out.append('  "%s" [label="%s", color="%s", penwidth="1.6"];'
                   % (_esc(st), _esc(st), edge))

    err_id = "__err_%s" % _slug(wf["name"])
    needs_err = False
    evt_seen = set()

    for i in range(len(stages) - 1):
        src, dst = stages[i], stages[i + 1]
        step = steps[i] if i < len(steps) else None
        if step:
            color = EFFECT_COLOR.get(step["effect"], "#94a3b8")
            label = step["name"]
            out.append('  "%s" -> "%s" [label="%s", color="%s", '
                       'penwidth="1.8", fontcolor="%s"];'
                       % (_esc(src), _esc(dst), _esc(label), color, color))
            if step["fails"]:
                needs_err = True
                out.append('  "%s" -> "%s" [color="#ef4444", style="dashed", '
                           'arrowhead="empty"];' % (_esc(src), _esc(err_id)))
            for ev in step["events"]:
                nid = "evt_%s" % _slug(ev)
                if nid not in evt_seen:
                    evt_seen.add(nid)
                    out.append('  "%s" [label="%s", shape=note, fillcolor="#422006", '
                               'color="#f59e0b", fontcolor="#fde68a"];'
                               % (nid, _esc(ev)))
                out.append('  "%s" -> "%s" [color="#f59e0b", style="dotted", '
                           'arrowhead="none", constraint=false];'
                           % (_esc(dst), nid))
        else:
            out.append('  "%s" -> "%s";' % (_esc(src), _esc(dst)))

    # events emitted by trailing steps (beyond the stage chain) → last stage
    for step in steps[max(len(stages) - 1, 0):]:
        for ev in step["events"]:
            nid = "evt_%s" % _slug(ev)
            if nid not in evt_seen:
                evt_seen.add(nid)
                out.append('  "%s" [label="%s", shape=note, fillcolor="#422006", '
                           'color="#f59e0b", fontcolor="#fde68a"];' % (nid, _esc(ev)))
            out.append('  "%s" -> "%s" [color="#f59e0b", style="dotted", '
                       'arrowhead="none", constraint=false];'
                       % (_esc(stages[-1]), nid))
        if step["fails"]:
            needs_err = True
            out.append('  "%s" -> "%s" [color="#ef4444", style="dashed", '
                       'arrowhead="empty"];' % (_esc(stages[-1]), _esc(err_id)))

    if needs_err:
        out.append('  "%s" [label="⚠ %s Error", shape=box, style="filled,dashed", '
                   'fillcolor="#450a0a", color="#ef4444", fontcolor="#fca5a5"];'
                   % (_esc(err_id), _esc(wf["name"])))
    out.append("}")
    return "\n".join(out)


def workflow_relations_dot(rels):
    """Workflow-to-workflow event graph: nodes=workflows, edges=domain events."""
    if not rels:
        return None
    out = _header("wf_relations")
    names = []
    for r in rels:
        for n in (r["from"], r["to"]):
            if n not in names:
                names.append(n)
    for n in names:
        out.append('  "%s" [color="#7dd3fc", penwidth="1.6"];' % _esc(n))
    for r in rels:
        lbl = r["event"]
        out.append('  "%s" -> "%s" [label="%s", color="#a855f7", '
                   'fontcolor="#d8b4fe", penwidth="1.5"];'
                   % (_esc(r["from"]), _esc(r["to"]), _esc(lbl)))
    out.append("}")
    return "\n".join(out)


def wf_pipeline_id(name):
    return "wf-" + _slug(name)


# ---------- aggregates ⇄ events (Phase 5/6) ----------
def _agg_name(raw):
    """`Name (Bounded Context: BC)` → ('Name', 'BC'); tolerates plain `(BC)`."""
    m = re.search(r"\(.*?Bounded Context\s*[:：]\s*([^)]*)\)", raw)
    if m:
        return raw[:m.start()].strip(), m.group(1).strip()
    p = re.search(r"\(([^)]*)\)\s*$", raw)
    if p:
        return raw[:p.start()].strip(), p.group(1).strip()
    return raw.strip(), ""


def parse_aggregates(md):
    """`### Aggregate` blocks → [{name, bc, commands:[{name, event}]}].

    Commands come from the `**操作**` bullets: `` `cmd(...)`: desc → 発行: `Event` ``.
    """
    out = []
    if not md:
        return out
    heads = list(re.finditer(r"^###\s+(.+?)\s*$", md, re.M))
    for k, h in enumerate(heads):
        name, bc = _agg_name(h.group(1).strip())
        body = md[h.end():(heads[k + 1].start() if k + 1 < len(heads) else len(md))]
        ops = re.search(r"\*\*操作\*\*\s*[:：]?(.*?)(?:\n\s*\*\*[^\n*]+\*\*\s*[:：]|\Z)",
                        body, re.S)
        scope = ops.group(1) if ops else body
        commands = []
        for line in scope.split("\n"):
            lm = re.match(r"\s*[-*]\s*`?([A-Za-z]\w*)\s*\(", line)
            if not lm:
                continue
            ev = None
            em = re.search(r"発行\s*[:：]\s*`?([A-Za-z]\w*)", line)
            if em:
                ev = em.group(1)
            commands.append({"name": lm.group(1), "event": ev})
        out.append({"name": name, "bc": bc, "commands": commands})
    return out


def parse_domain_events(md):
    """`#### EventName` blocks → {EventName: {source, trigger, consumers:[...]}}."""
    idx = {}
    if not md:
        return idx
    heads = list(re.finditer(r"^####\s+(.+?)\s*$", md, re.M))
    for k, h in enumerate(heads):
        name = re.sub(r"[`*]", "", h.group(1)).strip()
        body = md[h.end():(heads[k + 1].start() if k + 1 < len(heads) else len(md))]

        def f(label):
            mm = re.search(r"\*\*%s\*\*\s*[:：]\s*(.+)" % label, body)
            return re.sub(r"[`*]", "", mm.group(1)).strip() if mm else ""

        cons = f(r"Consumer")
        consumers = [c.strip() for c in re.split(r"[,、/]", cons) if c.strip()]
        idx[name] = {"source": f(r"発生元 Aggregate"),
                     "trigger": f(r"トリガー"), "consumers": consumers}
    return idx


def parse_event_flow(md):
    """`Context A --{Event}--> Context B` lines → [{from, event, to}]."""
    out = []
    if not md:
        return out
    for line in md.split("\n"):
        m = re.match(r"\s*(.+?)\s*--\{([^}]*)\}-->\s*(.+?)\s*$", line)
        if m:
            out.append({"from": m.group(1).strip(), "event": m.group(2).strip(),
                        "to": m.group(3).strip()})
    return out


def aggregate_flow_dot(agg, eidx):
    """One aggregate → Event Storming flow: command → aggregate → event → consumer.

    Colors follow Event Storming sticky conventions: command=blue, aggregate=amber,
    domain event=orange note, downstream consumer=sky (dashed = eventual consistency).
    """
    cmds = agg["commands"]
    events = []
    for c in cmds:
        if c["event"] and c["event"] not in events:
            events.append(c["event"])
    for ename, info in eidx.items():
        if info.get("source") == agg["name"] and ename not in events:
            events.append(ename)
    if not cmds and not events:
        return None

    aid = "agg_%s" % _slug(agg["name"])
    out = _header("agg_" + _slug(agg["name"]))
    out.append('  "%s" [label="%s", color="#f59e0b", penwidth="2.0", '
               'fillcolor="#1f2937"];' % (aid, _esc(agg["name"])))
    for c in cmds:
        cid = "cmd_%s" % _slug(c["name"])
        out.append('  "%s" [label="%s", shape=cds, color="#3b82f6", '
                   'fontcolor="#bfdbfe"];' % (cid, _esc(c["name"])))
        out.append('  "%s" -> "%s" [color="#3b82f6"];' % (cid, aid))
    seen = set()
    for ev in events:
        eid = "evt_%s" % _slug(ev)
        if eid not in seen:
            seen.add(eid)
            out.append('  "%s" [label="%s", shape=note, fillcolor="#422006", '
                       'color="#f59e0b", fontcolor="#fde68a"];' % (eid, _esc(ev)))
        out.append('  "%s" -> "%s" [color="#f59e0b"];' % (aid, eid))
        for cons in eidx.get(ev, {}).get("consumers", []):
            coid = "cons_%s" % _slug(cons)
            out.append('  "%s" [label="%s", color="#7dd3fc", '
                       'style="filled,dashed", fontcolor="#bae6fd"];'
                       % (coid, _esc(cons)))
            out.append('  "%s" -> "%s" [color="#7dd3fc", style="dashed"];'
                       % (eid, coid))
    out.append("}")
    return "\n".join(out)


def event_flow_dot(flows):
    """Cross-context event flow: contexts as nodes, domain events as edges."""
    if not flows:
        return None
    out = _header("event_flow")
    names = []
    for f in flows:
        for n in (f["from"], f["to"]):
            if n not in names:
                names.append(n)
    for n in names:
        out.append('  "%s" [color="#7dd3fc", penwidth="1.6"];' % _esc(n))
    for f in flows:
        out.append('  "%s" -> "%s" [label="%s", color="#f59e0b", '
                   'fontcolor="#fde68a", penwidth="1.5"];'
                   % (_esc(f["from"]), _esc(f["to"]), _esc(f["event"])))
    out.append("}")
    return "\n".join(out)


def agg_flow_id(name):
    return "agg-" + _slug(name)


# ---------- entry point ----------
def available(d, colors=None):
    """Return {id: dot} for every diagram that can be built from dir `d`."""
    out = {}
    cmap = _read(d, "context-map.md")
    contexts = parse_contexts(_read(d, "bounded-contexts.md"))
    relations = parse_context_map(cmap)
    if relations or len(contexts) > 1:
        out["context-map"] = context_map_dot(contexts, relations, colors)

    wmd = _read(d, "workflows.md")
    for wf in parse_workflows(wmd):
        dot = workflow_pipeline_dot(wf)
        if dot:
            out[wf_pipeline_id(wf["name"])] = dot
    rels = workflow_relations_dot(parse_workflow_relations(wmd))
    if rels:
        out["wf-relations"] = rels

    emd = _read(d, "domain-events.md")
    eidx = parse_domain_events(emd)
    for agg in parse_aggregates(_read(d, "aggregates.md")):
        dot = aggregate_flow_dot(agg, eidx)
        if dot:
            out[agg_flow_id(agg["name"])] = dot
    eflow = event_flow_dot(parse_event_flow(emd))
    if eflow:
        out["event-flow"] = eflow
    return out


def autoplace(slug, md, ids):
    """Insert `<!-- ddd:diagram:ID -->` markers into `md` at sensible anchors.

    Centralizes placement so build_site.py stays generic. Skipping is per-ID:
    a hand-placed `<!-- ddd:diagram:X -->` only suppresses *that* diagram's
    auto-insertion, so adding one explicit marker in a multi-diagram file
    (workflows.md / aggregates.md) doesn't drop every other generated diagram.
    Returns the (possibly) rewritten markdown.
    """
    def present(i):
        return ("ddd:diagram:%s" % i) in md

    if "context-map" in ids:
        if slug == "context-map":
            if not present("context-map"):
                return re.sub(r"(^#\s+.+$)", r"\1\n\n<!-- ddd:diagram:context-map -->",
                              md, count=1, flags=re.M)
            return md
        if slug == "bounded-contexts":
            # The contexts phase template puts a "## Context Map 概要図" here, possibly
            # with a hand-drawn ASCII fence AND/OR the template's own marker. Normalize
            # the region right under that heading to exactly ONE marker and NO stale
            # <pre> fence — and do it even when a marker is already present, otherwise a
            # marker + a later hand-drawn fence would both render.
            hm = re.search(r"^#{2,}\s+.*Context\s*Map.*$", md, re.M)
            if hm:
                # consume consecutive blank lines / existing markers / one ASCII fence
                tok = re.compile(
                    r"[ \t]*\n"
                    r"|[ \t]*<!--\s*ddd:diagram:context-map\s*-->[ \t]*\n?"
                    r"|[ \t]*```[\s\S]*?```[ \t]*\n?")
                i = hm.end()
                while True:
                    m = tok.match(md, i)
                    if not m or m.end() == i:
                        break
                    i = m.end()
                return md[:hm.end()] + "\n\n<!-- ddd:diagram:context-map -->\n" + md[i:]
            if not present("context-map"):
                return re.sub(r"(^#\s+.+$)", r"\1\n\n<!-- ddd:diagram:context-map -->",
                              md, count=1, flags=re.M)
            return md

    if slug == "workflows":
        # one pipeline per workflow, placed after that workflow's stage fence;
        # the relations graph after the relations fence.
        heads = list(re.finditer(r"^##\s+Workflow\s+\d+\s*[:：]\s*(.+?)\s*$", md, re.M))
        inserts = []  # (position, text)
        for k, h in enumerate(heads):
            seg_end = heads[k + 1].start() if k + 1 < len(heads) else len(md)
            raw = h.group(1).strip()
            name = re.sub(r"\([^)]*\)\s*$", "", raw).strip()
            wid = wf_pipeline_id(name)
            if wid not in ids or present(wid):
                continue
            fence = re.search(r"###\s+ステージ.*?```.*?```", md[h.end():seg_end], re.S)
            if fence:
                pos = h.end() + fence.end()
                inserts.append((pos, "\n\n<!-- ddd:diagram:%s -->" % wid))
        if "wf-relations" in ids and not present("wf-relations"):
            rel = re.search(r"##\s+ワークフロー間の関係図.*?```.*?```", md, re.S)
            if rel:
                inserts.append((rel.end(), "\n\n<!-- ddd:diagram:wf-relations -->"))
        for pos, text in sorted(inserts, reverse=True):
            md = md[:pos] + text + md[pos:]
        return md

    if slug == "aggregates":
        inserts = []
        for h in re.finditer(r"^###\s+(.+?)\s*$", md, re.M):
            name, _ = _agg_name(h.group(1).strip())
            aid = agg_flow_id(name)
            if aid in ids and not present(aid):
                inserts.append((h.end(), "\n\n<!-- ddd:diagram:%s -->" % aid))
        for pos, text in sorted(inserts, reverse=True):
            md = md[:pos] + text + md[pos:]
        return md

    if slug == "domain-events" and "event-flow" in ids and not present("event-flow"):
        m = re.search(r"^##\s+Event Flow.*$", md, re.M)
        if m:
            md = md[:m.end()] + "\n\n<!-- ddd:diagram:event-flow -->" + md[m.end():]
        return md

    return md
