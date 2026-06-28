#!/usr/bin/env python3
"""emit_intent.py — Export the DDD model (docs/domain/*.md) as a contract-shaped
intent.json for downstream tools (e.g. crawl-kit's intent layer).

Self-contained: Python 3 standard library only (no pip install).

WHY THIS EXISTS
    distill-ddd owns *intent* — "what we MEANT to build". Downstream verification
    tools need that intent as data, not prose. This is the "emit at the source"
    boundary: the skill stays independent and only a contract-shaped JSON crosses
    over. Markdown stays the human artifact; this is its machine-readable twin.

WHAT IT EMITS
    The meaningful intent↔structure diff axis is EVENTS and STATE TRANSITIONS
    (domain behaviour is left out on purpose — too fine-grained to diff
    mechanically). So the payload leads with those two, plus a thin concept list
    for canonical-id seeding:

    {
      "concepts": [
        {"name", "kind", "context", "aliases": [], "attributes": []}
      ],
      "events": [
        {"name", "aggregate", "context", "trigger", "properties": [], "consumer"}
      ],
      "stateTransitions": [
        {"aggregate", "context", "from", "to", "trigger", "event"}
      ]
    }

    - concepts          ← aggregates.md headings, aliases enriched from glossary.md
    - events            ← domain-events.md  ("## イベント一覧")
    - stateTransitions  ← the explicit "**状態遷移**:" block under each aggregate in
                          aggregates.md. These are DECIDED INTERACTIVELY during the
                          `aggregates` phase (not guessed from prose), so the export
                          is deterministic. Canonical line shape:
                              - {from} → {to} : `{trigger}` → `{event}`
                          where `: trigger → event` is optional.

    The shape is a superset of the legacy glossary fixture ({"concepts": [...]}),
    so existing consumers keep working. attributes are not mined from prose here
    (use the `types` phase for that); they are emitted as [] to preserve the shape.

USAGE
    python3 emit_intent.py [DIR] [-o OUT]
        DIR   directory of *.md artifacts (default: docs/domain)
        -o    output path     (default: DIR/intent.json)

Labels are matched in Japanese and English so the export works whichever language
the session was run in.
"""
import sys, os, re, json, argparse


# ---------- low-level markdown helpers ----------

HEADING = re.compile(r"^(#{2,4})\s+(.*?)\s*$")
# "- **Label**: value"  /  "* **Label** ： value"  (label may hold spaces)
BULLET = re.compile(r"^(?P<indent>\s*)[-*]\s+(?P<rest>.*)$")
LABELLED = re.compile(r"^\*\*(?P<label>[^*]+?)\*\*\s*[:：]\s*(?P<value>.*)$")
BACKTICK = re.compile(r"`([^`]+)`")
# "→ 発行: `Event`" / "emits: `Event`" / "publishes `Event`"
EMITS = re.compile(r"(?:発行|emits?|publishes?)\s*[:：]?\s*`([^`]+)`")
ARROW = re.compile(r"\s*(?:→|->|⇒|=>)\s*")
# "{from} → {to} : {meta}"  (meta optional)
TRANSITION = re.compile(
    r"^(?P<from>.+?)\s*(?:→|->|⇒|=>)\s*(?P<to>[^:：]+?)\s*(?:[:：]\s*(?P<meta>.*))?$")


def strip_annotation(text):
    """Heading/value text up to the first annotation marker — '（', '(', '★'."""
    return re.split(r"[（(★]", text, maxsplit=1)[0].strip()


def first_backtick(text):
    """The first `code` span, else the text trimmed of a trailing annotation."""
    m = BACKTICK.search(text)
    return m.group(1).strip() if m else strip_annotation(text)


def labelled_bullet(rest, *labels):
    """If `rest` is `**Label**: value` and Label matches (case-insensitively) any
    of `labels`, return value; else None. With no labels, return (label, value)."""
    m = LABELLED.match(rest)
    if not m:
        return None
    label = m.group("label").strip().lower()
    value = m.group("value").strip()
    if not labels:
        return (label, value)
    return value if any(label == l.lower() for l in labels) else None


# field label aliases (JP + EN)
L_AGGREGATE = ("発生元 Aggregate", "発生元", "Aggregate", "Source Aggregate", "Origin Aggregate")
L_TRIGGER = ("トリガー", "Trigger", "Command")
L_PROPERTIES = ("プロパティ", "Properties", "Payload")
L_CONSUMER = ("Consumer", "受信", "Subscriber")
L_TRANSITIONS = ("状態遷移", "State Transitions", "State Transition", "Transitions")


# ---------- events (domain-events.md) ----------

def parse_events(md):
    """Extract domain events. Structure (phase-events.md template):
        ### {Context}
        #### {EventName}
        - **発生元 Aggregate**: {agg}
        - **トリガー**: `{cmd}`
        - **プロパティ**:
          - `{prop}`: {type}
        - **Consumer**: {ctx}
    """
    events = []
    context = ""
    cur = None
    collecting_props = False

    def flush():
        if cur is not None:
            events.append(cur)

    for line in md.splitlines():
        h = HEADING.match(line)
        if h:
            level, text = len(h.group(1)), h.group(2)
            if level == 3:
                flush(); cur = None; collecting_props = False
                context = strip_annotation(text)
            elif level == 4:
                flush()
                cur = {"name": strip_annotation(text), "aggregate": "",
                       "context": context, "trigger": "", "properties": [],
                       "consumer": ""}
                collecting_props = False
            else:  # level 2 ends any event section
                flush(); cur = None; collecting_props = False
            continue
        if cur is None:
            continue
        b = BULLET.match(line)
        if not b:
            continue
        indent, rest = len(b.group("indent")), b.group("rest")
        if indent == 0:
            collecting_props = False
            kv = labelled_bullet(rest)
            if not kv:
                continue
            label, value = kv
            if any(label == l.lower() for l in L_AGGREGATE):
                cur["aggregate"] = strip_annotation(value)
            elif any(label == l.lower() for l in L_TRIGGER):
                cur["trigger"] = first_backtick(value)
            elif any(label == l.lower() for l in L_CONSUMER):
                cur["consumer"] = strip_annotation(value)
            elif any(label == l.lower() for l in L_PROPERTIES):
                collecting_props = True
        elif collecting_props:  # nested property bullet
            name = first_backtick(rest).split(":")[0].strip()
            name = re.split(r"\s", name, maxsplit=1)[0]
            if name and name not in cur["properties"]:
                cur["properties"].append(name)
    flush()
    return events


# ---------- aggregates (aggregates.md) → concepts + transitions ----------

def _heading_context(text):
    """'VerificationRun（BC: Verification）' → ('VerificationRun', 'Verification')."""
    name = strip_annotation(text)
    m = re.search(r"(?:BC|Bounded Context)\s*[:：]\s*([^）)]+)", text)
    return name, (m.group(1).strip() if m else "")


def parse_aggregates(md):
    """Return (concepts, transitions). One concept per `### Agg（BC: X）` heading
    under "## 集約一覧"; transitions from that aggregate's explicit "**状態遷移**:"
    block (decided during the aggregates phase — see emit_intent docstring)."""
    concepts = []
    transitions = []
    agg, context = "", ""
    in_list_section = False
    collecting_transitions = False

    for line in md.splitlines():
        h = HEADING.match(line)
        if h:
            level, text = len(h.group(1)), h.group(2)
            if level == 2:
                in_list_section = bool(re.search(r"集約一覧|Aggregates?", text, re.I))
                agg, context, collecting_transitions = "", "", False
            elif level == 3 and in_list_section:
                agg, context = _heading_context(text)
                collecting_transitions = False
                if agg:
                    concepts.append({"name": agg, "kind": "aggregate-root",
                                     "context": context, "aliases": [],
                                     "attributes": []})
            continue
        if not agg:
            continue
        b = BULLET.match(line)
        if not b:
            continue
        indent, rest = len(b.group("indent")), b.group("rest")
        if indent == 0:
            collecting_transitions = labelled_bullet(rest, *L_TRANSITIONS) == ""
        elif collecting_transitions:
            t = _parse_transition(rest, agg, context)
            if t:
                transitions.append(t)
    return concepts, transitions


def _parse_transition(rest, agg, context):
    """`Draft → Placed : `place()` → `OrderPlaced`` → a transition record.
    The `: trigger → event` tail is optional; `発行`/`emits` marks the event."""
    m = TRANSITION.match(rest)
    if not m:
        return None
    frm = first_backtick(m.group("from"))
    to = first_backtick(m.group("to"))
    if not frm or not to:
        return None
    trigger = event = None
    meta = (m.group("meta") or "").strip()
    if meta:
        ticks = BACKTICK.findall(meta)
        emitted = EMITS.search(meta)
        if emitted:
            event = emitted.group(1)
            trigger = next((t for t in ticks if t != event), None)
        elif ARROW.search(meta) and len(ticks) >= 2:
            trigger, event = ticks[0], ticks[1]
        elif ticks:
            trigger = ticks[0]
    return {"aggregate": agg, "context": context, "from": frm, "to": to,
            "trigger": trigger, "event": event}


# ---------- glossary (glossary.md) → alias enrichment ----------

def parse_glossary(md):
    """Rows of `| 用語 | 英語 | 定義 |` tables → [(term, english, context)]."""
    rows = []
    context = ""
    for line in md.splitlines():
        h = HEADING.match(line)
        if h:
            if len(h.group(1)) == 2:
                context = strip_annotation(h.group(2))
            continue
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            term, english = cells[0], cells[1]
            if not term or term in ("用語", "Term") or set(term) <= set("-—: "):
                continue
            rows.append((term, english, context))
    return rows


def enrich_concepts(concepts, glossary_rows):
    """Add glossary English as the canonical alias; add glossary-only terms."""
    by_name = {c["name"].lower(): c for c in concepts}
    for term, english, context in glossary_rows:
        match = by_name.get((english or "").lower()) or by_name.get(term.lower())
        if match:
            for alias in (term, english):
                if alias and alias != match["name"] and alias not in match["aliases"]:
                    match["aliases"].append(alias)
        else:
            name = english or term
            concept = {"name": name, "kind": None, "context": context,
                       "aliases": [term] if term != name else [], "attributes": []}
            concepts.append(concept)
            by_name[name.lower()] = concept
    return concepts


# ---------- assembly ----------

def _read(domain_dir, name):
    path = os.path.join(domain_dir, name)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def build_intent(domain_dir):
    events_md = _read(domain_dir, "domain-events.md")
    aggregates_md = _read(domain_dir, "aggregates.md")
    glossary_md = _read(domain_dir, "glossary.md")

    events = parse_events(events_md) if events_md else []
    concepts, transitions = (parse_aggregates(aggregates_md)
                             if aggregates_md else ([], []))
    if glossary_md:
        enrich_concepts(concepts, parse_glossary(glossary_md))

    return {"concepts": concepts, "events": events,
            "stateTransitions": transitions}


def main(argv):
    ap = argparse.ArgumentParser(
        prog="emit_intent.py",
        description="Export docs/domain/*.md as a contract-shaped intent.json.")
    ap.add_argument("dir", nargs="?", default="docs/domain",
                    help="directory of *.md artifacts (default: docs/domain)")
    ap.add_argument("-o", "--out", help="output path (default: DIR/intent.json)")
    args = ap.parse_args(argv[1:])

    if not os.path.isdir(args.dir):
        print("error: not a directory: %s" % args.dir, file=sys.stderr)
        return 2

    intent = build_intent(args.dir)
    if not intent["events"] and not intent["concepts"]:
        print("warning: no events or concepts found — is %s a DDD model dir "
              "(expects domain-events.md / aggregates.md)?" % args.dir,
              file=sys.stderr)

    out = args.out or os.path.join(args.dir, "intent.json")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(intent, ensure_ascii=False, indent=2) + "\n")

    print("intent: %d concept(s), %d event(s), %d transition(s) → %s"
          % (len(intent["concepts"]), len(intent["events"]),
             len(intent["stateTransitions"]), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
