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
