#!/usr/bin/env python3
"""test_diagrams.py — stdlib-only checks for diagrams.py (run: python3 this).

No pytest dependency (matches the publish toolchain's "standard library only"
rule). Exits non-zero on the first failed assertion.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diagrams  # noqa: E402


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


def test_available_edges():
    # empty dir → nothing
    assert diagrams.available(tempfile.mkdtemp()) == {}
    # contexts only (no map) but >1 context → still a diagram
    d = tempfile.mkdtemp()
    open(os.path.join(d, "bounded-contexts.md"), "w").write(CONTEXTS_MD)
    assert "context-map" in diagrams.available(d)
    # garbage table without Upstream header → no rows
    assert diagrams.parse_context_map("| a | b |\n|---|---|\n| 1 | 2 |") == []


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok: %s" % t.__name__)
    print("\n%d passed" % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
