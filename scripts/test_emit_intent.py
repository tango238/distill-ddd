#!/usr/bin/env python3
"""test_emit_intent.py — stdlib-only checks for emit_intent.py (run: python3 this).

No pytest dependency (matches the publish toolchain's "standard library only"
rule). Exits non-zero on the first failed assertion.
"""
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emit_intent  # noqa: E402


EVENTS_MD = """# Domain Events

## イベント一覧

### Observation（観測）

#### AppCrawled
- **発生元 Aggregate**: SiteStructure
- **トリガー**: `capture(crawl)`（Playwright クロール）
- **プロパティ**:
  - `pages`: RawPage[] — 収集したページ
  - `occurredOn`: Timestamp
- **Consumer**: Reconciliation

### Verification（検証）

#### VerdictReached
- **発生元 Aggregate**: Finding
- **トリガー**: `adjudicate(votes)`
- **プロパティ**:
  - `findingId`: string
  - `verdict`: Verdict — classification
- **Consumer**: Reporting

## Event Flow (コンテキスト間)
Observation --{AppCrawled}--> Reconciliation
"""

AGGREGATES_MD = """# Aggregates

## Right-Sizing の判断
| 候補 | 判断 | 理由 |
|---|---|---|
| Finding | 分離 | ライフサイクル（産出→裁定）※表は無視される |

## 集約一覧

### Order（BC: Sales）
- **Root / ID**: `Order` / `OrderId`
- **操作**:
  - `place()`: 注文確定 → 発行: `OrderPlaced`
- **状態**: Draft, Placed, Shipped
- **状態遷移**:
  - Draft → Placed : `place()` → `OrderPlaced`
  - Placed → Shipped : `ship()` → 発行 `OrderShipped`
- **他集約参照**: `CustomerId`

### SiteStructure（BC: Observation）
- **操作**:
  - `capture(crawl)`: クロール → 発行: `AppCrawled`
- **状態遷移**: なし
"""

GLOSSARY_MD = """# ユビキタス言語

## Sales

| 用語 | 英語 | 定義 |
|------|------|------|
| 注文 | Order | 顧客の購入要求 |
| 出荷 | Shipment | 発送の単位 |
"""


def test_events_basic():
    events = emit_intent.parse_events(EVENTS_MD)
    assert [e["name"] for e in events] == ["AppCrawled", "VerdictReached"], events
    app = events[0]
    assert app["aggregate"] == "SiteStructure"
    assert app["context"] == "Observation"
    assert app["trigger"] == "capture(crawl)"          # backtick, annotation stripped
    assert app["properties"] == ["pages", "occurredOn"]
    assert app["consumer"] == "Reconciliation"
    assert events[1]["context"] == "Verification"      # h3 context switch


def test_concepts_and_context():
    concepts, _ = emit_intent.parse_aggregates(AGGREGATES_MD)
    names = [c["name"] for c in concepts]
    assert names == ["Order", "SiteStructure"], names   # table rows are NOT concepts
    assert concepts[0]["kind"] == "aggregate-root"
    assert concepts[0]["context"] == "Sales"


def test_explicit_transitions():
    _, trans = emit_intent.parse_aggregates(AGGREGATES_MD)
    # only the explicit "**状態遷移**:" block (the Right-Sizing arrow is ignored)
    assert len(trans) == 2, trans
    a, b = trans
    assert (a["from"], a["to"], a["trigger"], a["event"]) == \
        ("Draft", "Placed", "place()", "OrderPlaced")
    assert (b["from"], b["to"], b["trigger"], b["event"]) == \
        ("Placed", "Shipped", "ship()", "OrderShipped")   # 発行 keyword form
    assert a["aggregate"] == "Order" and a["context"] == "Sales"


def test_no_state_aggregate_emits_no_transition():
    _, trans = emit_intent.parse_aggregates(AGGREGATES_MD)
    assert all(t["aggregate"] != "SiteStructure" for t in trans)  # "なし" → none


def test_glossary_enriches_aliases():
    concepts, _ = emit_intent.parse_aggregates(AGGREGATES_MD)
    emit_intent.enrich_concepts(concepts, emit_intent.parse_glossary(GLOSSARY_MD))
    order = next(c for c in concepts if c["name"] == "Order")
    assert "注文" in order["aliases"]                   # matched by English column
    # glossary-only term becomes its own concept (English canonical name)
    shipment = next(c for c in concepts if c["name"] == "Shipment")
    assert shipment["aliases"] == ["出荷"]


def test_build_intent_end_to_end():
    with tempfile.TemporaryDirectory() as d:
        for name, body in (("domain-events.md", EVENTS_MD),
                           ("aggregates.md", AGGREGATES_MD),
                           ("glossary.md", GLOSSARY_MD)):
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        rc = emit_intent.main(["emit_intent.py", d])
        assert rc == 0
        with open(os.path.join(d, "intent.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        assert set(data) == {"concepts", "events", "stateTransitions"}
        assert len(data["events"]) == 2
        assert len(data["stateTransitions"]) == 2
        assert any(c["aliases"] for c in data["concepts"])


def test_missing_files_are_optional():
    with tempfile.TemporaryDirectory() as d:
        intent = emit_intent.build_intent(d)            # empty dir, no crash
        assert intent == {"concepts": [], "events": [], "stateTransitions": []}


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok: %s" % t.__name__)
    print("\n%d passed" % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
