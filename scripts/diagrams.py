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


# ---------- entry point ----------
def available(d, colors=None):
    """Return {kind: dot} for every diagram that can be built from dir `d`."""
    out = {}
    cmap = _read(d, "context-map.md")
    contexts = parse_contexts(_read(d, "bounded-contexts.md"))
    relations = parse_context_map(cmap)
    if relations or len(contexts) > 1:
        out["context-map"] = context_map_dot(contexts, relations, colors)
    return out
