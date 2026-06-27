#!/usr/bin/env python3
"""test_diagrams.py — stdlib-only checks for diagrams.py (run: python3 this).

No pytest dependency (matches the publish toolchain's "standard library only"
rule). Exits non-zero on the first failed assertion.
"""
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diagrams  # noqa: E402
import build_site  # noqa: E402


CONTEXTS_MD = """# Bounded Contexts
### Spotly (Core)
### PMS (Supporting)
### Cleaning (Generic)
### Identity
"""

MAP_MD = """# Context Map
## 関係一覧
| Upstream | Downstream | 関係 | 統合方式 | 備考 |
|----------|-----------|------|---------|------|
| PMS | Spotly | Customer-Supplier | REST + ACL | 在庫 |
| Spotly | PMS | Partnership | Shared DB | 🔴 密 |
| Cleaning | Legacy | Separate Ways | — | 切る |
"""


def test_parse_contexts():
    c = diagrams.parse_contexts(CONTEXTS_MD)
    assert list(c) == ["Spotly", "PMS", "Cleaning", "Identity"], c
    assert c["Spotly"]["subdomain"] == "Core"
    assert c["Cleaning"]["subdomain"] == "Generic"
    assert c["Identity"]["subdomain"] == ""  # no parens → unclassified


def test_parse_context_map():
    rows = diagrams.parse_context_map(MAP_MD)
    assert len(rows) == 3, rows
    assert rows[0]["upstream"] == "PMS" and rows[0]["downstream"] == "Spotly"
    assert rows[0]["integration"] == "REST + ACL"
    assert "🔴" in rows[1]["note"]


def test_dot_conventions():
    c = diagrams.parse_contexts(CONTEXTS_MD)
    rows = diagrams.parse_context_map(MAP_MD)
    dot = diagrams.context_map_dot(c, rows)
    # nodes for every endpoint, incl. one only present in the map (Legacy)
    for name in ("Spotly", "PMS", "Cleaning", "Identity", "Legacy"):
        assert '"%s"' % name in dot, name
    # subdomain styling
    assert "penwidth=\"2.6\"" in dot  # Core emphasized
    assert "filled,dashed" in dot     # Generic dashed
    # label line-break is DOT's \n (single backslash), not a literal \\n
    assert "Spotly\\n(Core)" in dot
    assert "Spotly\\\\n" not in dot
    # ACL → diamond arrowhead; C/S marker present
    assert "arrowhead=\"diamond\"" in dot
    assert "C/S" in dot
    # Partnership → bidirectional; problem (🔴 / Separate Ways) → red edge
    assert "dir=\"both\"" in dot
    assert dot.count("#ef4444") >= 2  # partnership(🔴) + separate-ways
    # valid-ish DOT shell
    assert dot.startswith("digraph context_map {") and dot.rstrip().endswith("}")


WORKFLOWS_MD = """# Workflows
## Workflow 1: PlaceOrder (Order-Taking BC)
### ステージ(中間型の系列)
```
UnvalidatedOrder → ValidatedOrder → PricedOrder
```
### ステップ
#### Step 1: validateOrder
- 出力: `Result<ValidatedOrder, ValidationError>`
- 副作用: read-only
- エラー: `InvalidProductCode`
- 発行 Event: なし
#### Step 2: priceOrder
- 出力: `Result<PricedOrder, PricingError>`
- 副作用: write
- 発行 Event: `BillableOrderPlaced`(成功時)
## ワークフロー間の関係図
```
PlaceOrder --[OrderPlaced]--> ShipOrder
```
"""


def test_parse_workflows():
    wfs = diagrams.parse_workflows(WORKFLOWS_MD)
    assert len(wfs) == 1
    wf = wfs[0]
    assert wf["name"] == "PlaceOrder" and wf["bc"] == "Order-Taking"
    assert wf["stages"] == ["UnvalidatedOrder", "ValidatedOrder", "PricedOrder"]
    assert wf["steps"][0]["effect"] == "readonly" and wf["steps"][0]["fails"]
    assert wf["steps"][1]["effect"] == "write"
    assert wf["steps"][1]["events"] == ["BillableOrderPlaced"]


def test_workflow_pipeline_dot():
    wf = diagrams.parse_workflows(WORKFLOWS_MD)[0]
    dot = diagrams.workflow_pipeline_dot(wf)
    # stage nodes + step edges
    assert '"UnvalidatedOrder" -> "ValidatedOrder"' in dot
    assert "validateOrder" in dot and "priceOrder" in dot
    # event note + error sink (railway)
    assert "shape=note" in dot and "BillableOrderPlaced" in dot
    assert "Error" in dot and "#ef4444" in dot
    assert diagrams.workflow_pipeline_dot({"name": "x", "stages": [], "steps": []}) is None


def test_graph_id_quoted_for_hyphenated_names():
    # Codex P2: bare hyphenated graph ids (wf_place-order) break Graphviz/viz.
    assert diagrams._header("agg_a-b")[0] == 'digraph "agg_a-b" {'
    wf = {"name": "Place Order", "stages": ["A", "B"],
          "steps": [{"name": "x", "effect": "pure", "events": [], "fails": False}]}
    dot = diagrams.workflow_pipeline_dot(wf)
    assert dot.startswith('digraph "wf_place-order" {')
    rel = diagrams.workflow_relations_dot(
        [{"from": "A", "event": "E", "to": "B"}])
    assert rel.startswith('digraph "wf_relations" {')


def test_slug_collision_resistant_and_dot_safe():
    # Codex P2: Japanese headings used to both slug to "x" and collide.
    a, b = diagrams._slug("注文"), diagrams._slug("請求")
    assert a != b
    for s in (a, b):
        assert re.match(r"^[a-z0-9-]+$", s)        # DOT-safe, no non-ASCII
    # ASCII names stay readable (no hash suffix)
    assert diagrams._slug("Place Order") == "place-order"
    # two Japanese aggregates produce two distinct diagrams (no overwrite)
    jp = ("# Aggregates\n"
          "### 注文\n**操作**:\n- `place()`: x → 発行: `OrderPlaced`\n"
          "### 請求\n**操作**:\n- `bill()`: y → 発行: `Billed`\n")
    ids = {diagrams.agg_flow_id(a["name"]) for a in diagrams.parse_aggregates(jp)}
    assert len(ids) == 2  # distinct ids, not both "agg-x"


def test_autoplace_partial_marker_keeps_others():
    # Codex P2: one hand-placed marker must not suppress the other diagrams.
    md = WORKFLOWS_MD.replace(
        "## Workflow 1: PlaceOrder (Order-Taking BC)",
        "<!-- ddd:diagram:wf-placeorder -->\n## Workflow 1: PlaceOrder (Order-Taking BC)")
    out = diagrams.autoplace("workflows", md, ["wf-placeorder", "wf-relations"])
    # the explicit one is not duplicated...
    assert out.count("ddd:diagram:wf-placeorder") == 1
    # ...but the relations graph is still auto-inserted
    assert "ddd:diagram:wf-relations" in out


def test_context_map_autoplaced_in_bounded_contexts():
    # The contexts phase puts a hand-drawn "## Context Map 概要図" (ASCII) in
    # bounded-contexts.md. publish must place the generated diagram THERE too (not only
    # in context-map.md), replacing the hand-drawn fence — otherwise it renders as <pre>.
    md = (
        "# Bounded Contexts\n\n"
        "## Context Map 概要図\n\n"
        "```\n [A] --> [B]\n hand-drawn ascii\n```\n\n"
        "## Bounded Context 一覧\n\n### A (Core)\n"
    )
    out = diagrams.autoplace("bounded-contexts", md, ["context-map"])
    assert "<!-- ddd:diagram:context-map -->" in out
    assert "hand-drawn ascii" not in out  # the ASCII fence is dropped
    # idempotent
    assert diagrams.autoplace("bounded-contexts", out, ["context-map"]) == out


def test_context_map_strips_fence_even_when_marker_present():
    # Codex P2: a doc from the updated template already carries the marker; if the user
    # also adds a hand-drawn ASCII fence, the fence must STILL be stripped (not rendered
    # alongside the generated figure). Covers marker-before-fence and the dup-marker case.
    md = (
        "# Bounded Contexts\n\n"
        "## Context Map 概要図\n\n"
        "<!-- ddd:diagram:context-map -->\n"
        "```\n hand-drawn ascii\n```\n\n"
        "## Bounded Context 一覧\n"
    )
    out = diagrams.autoplace("bounded-contexts", md, ["context-map"])
    assert "hand-drawn ascii" not in out          # fence dropped
    assert out.count("ddd:diagram:context-map") == 1  # exactly one marker
    assert diagrams.autoplace("bounded-contexts", out, ["context-map"]) == out  # idempotent


def test_context_map_still_autoplaced_in_context_map_md():
    md = "# Context Map\n\n## 関係一覧\n\n| Upstream | Downstream |\n|---|---|\n"
    out = diagrams.autoplace("context-map", md, ["context-map"])
    assert "<!-- ddd:diagram:context-map -->" in out


def test_workflow_relations_and_autoplace():
    rels = diagrams.parse_workflow_relations(WORKFLOWS_MD)
    assert rels == [{"from": "PlaceOrder", "event": "OrderPlaced", "to": "ShipOrder"}]
    dot = diagrams.workflow_relations_dot(rels)
    assert '"PlaceOrder" -> "ShipOrder"' in dot and "OrderPlaced" in dot
    # autoplace inserts a marker per workflow pipeline + the relations graph
    ids = ["wf-placeorder", "wf-relations"]
    placed = diagrams.autoplace("workflows", WORKFLOWS_MD, ids)
    assert "<!-- ddd:diagram:wf-placeorder -->" in placed
    assert "<!-- ddd:diagram:wf-relations -->" in placed
    # idempotent: a doc already carrying a marker is left alone
    assert diagrams.autoplace("workflows", placed, ids) == placed


AGGREGATES_MD = """# Aggregates
### Order (Bounded Context: Order-Taking)
**操作**:
- `placeOrder(items)`: 確定 → 発行: `OrderPlaced`
- `cancelOrder(reason)`: 取消 → 発行: `OrderCancelled`
**他 Aggregate との参照**: Customer (CustomerId)
### Shipment (Bounded Context: Shipping)
**操作**:
- `dispatch()`: 出荷 → 発行: `OrderShipped`
"""

EVENTS_MD = """# Domain Events
#### OrderPlaced
- **発生元 Aggregate**: Order
- **トリガー**: placeOrder
- **Consumer**: Shipping, Billing
#### OrderShipped
- **発生元 Aggregate**: Shipment
- **Consumer**: Notification
## Event Flow (コンテキスト間)
Order-Taking --{OrderPlaced}--> Shipping
Shipping --{OrderShipped}--> Notification
"""


def test_parse_aggregates():
    aggs = diagrams.parse_aggregates(AGGREGATES_MD)
    assert [a["name"] for a in aggs] == ["Order", "Shipment"]
    assert aggs[0]["bc"] == "Order-Taking"
    cmds = {c["name"]: c["event"] for c in aggs[0]["commands"]}
    assert cmds == {"placeOrder": "OrderPlaced", "cancelOrder": "OrderCancelled"}


def test_parse_domain_events_and_flow():
    idx = diagrams.parse_domain_events(EVENTS_MD)
    assert idx["OrderPlaced"]["source"] == "Order"
    assert idx["OrderPlaced"]["consumers"] == ["Shipping", "Billing"]
    flow = diagrams.parse_event_flow(EVENTS_MD)
    assert {"from": "Order-Taking", "event": "OrderPlaced", "to": "Shipping"} in flow
    assert len(flow) == 2  # the indented prose line is not a flow edge


def test_aggregate_flow_dot():
    aggs = diagrams.parse_aggregates(AGGREGATES_MD)
    idx = diagrams.parse_domain_events(EVENTS_MD)
    dot = diagrams.aggregate_flow_dot(aggs[0], idx)
    # command (blue cds) -> aggregate (amber) -> event (note) -> consumer (sky dashed)
    assert "shape=cds" in dot and "#3b82f6" in dot
    assert '"agg_order"' in dot and "#f59e0b" in dot
    assert "shape=note" in dot and "OrderPlaced" in dot
    assert '"cons_shipping"' in dot and "dashed" in dot
    # empty aggregate yields nothing
    assert diagrams.aggregate_flow_dot({"name": "x", "commands": []}, {}) is None


def test_autoplace_aggregates_and_events():
    placed = diagrams.autoplace("aggregates", AGGREGATES_MD,
                                ["agg-order", "agg-shipment"])
    assert "<!-- ddd:diagram:agg-order -->" in placed
    assert "<!-- ddd:diagram:agg-shipment -->" in placed
    ev = diagrams.autoplace("domain-events", EVENTS_MD, ["event-flow"])
    assert "<!-- ddd:diagram:event-flow -->" in ev


def test_available_edges():
    # empty dir → nothing
    assert diagrams.available(tempfile.mkdtemp()) == {}
    # contexts only (no map) but >1 context → still a diagram
    d = tempfile.mkdtemp()
    open(os.path.join(d, "bounded-contexts.md"), "w").write(CONTEXTS_MD)
    assert "context-map" in diagrams.available(d)
    # garbage table without Upstream header → no rows
    assert diagrams.parse_context_map("| a | b |\n|---|---|\n| 1 | 2 |") == []


GLOSSARY_MD = """# 用語集
## Order-Taking
| 用語 | 英語 | 定義 |
|------|------|------|
| 注文 | Order | 購入意思の集約 |
| 注文明細 | OrderLine | 1商品の数量と価格 |
## コンテキスト横断の注意点
| 用語 | A での意味 | B での意味 |
|------|-----------|-----------|
| Order | 集約 | 参照ID |
"""


def test_parse_glossary_terms():
    rows = build_site.parse_glossary_terms(
        "| 用語 | 英語 | 定義 |\n|--|--|--|\n| 注文 | Order | 集約 |\n")
    assert rows == [{"term": "注文", "en": "Order", "def": "集約"}]
    # a cross-context table (用語 | 意味A | 意味B) is NOT a term glossary
    assert build_site.parse_glossary_terms(
        "| 用語 | A | B |\n|--|--|--|\n| Order | x | y |\n") is None


def test_glossary_body():
    body = build_site.glossary_body(GLOSSARY_MD)
    assert body is not None
    assert body.count('class="gl-card"') == 2          # only the term table
    assert "gl-toggle" in body and "gl-filter" in body  # toggle + filter present
    assert "OrderLine" in body                          # physical (English) name
    assert "<table>" in body                            # cross-context falls back
    # a doc with no term table → None (caller uses default renderer)
    assert build_site.glossary_body("# x\n## y\nplain text\n") is None


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok: %s" % t.__name__)
    print("\n%d passed" % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
