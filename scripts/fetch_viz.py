#!/usr/bin/env python3
"""fetch_viz.py — Vendor the Graphviz-in-WASM renderer for offline diagrams.

Phase 12 publish renders Context Map / workflow diagrams in the browser using
viz-standalone.js (Graphviz compiled to WebAssembly, single self-contained
file). We vendor it so the generated site renders SVG fully offline — no CDN,
no `dot` binary, no network at view time. This fetcher is the only step that
touches the network, and it runs once at vendor time, not at publish time.

Usage:
    python3 scripts/fetch_viz.py            # download + verify into scripts/assets/
    python3 scripts/fetch_viz.py --check    # verify the vendored copy only

Security (per .claude/rules/release.md): the download is pinned to a version
and checked against scripts/assets/viz-standalone.js.sha256. If that pin file
is absent, the first fetch establishes it (trust-on-first-use) and prints the
hash — verify it against npm's published integrity for @viz-js/viz before
committing the vendored file + pin.
"""
import hashlib
import os
import re
import sys
import urllib.request

# Resolve the latest published viz-standalone.js (Graphviz-in-WASM, UMD: sets
# window.Viz). Unversioned CDN URLs redirect to the current release; we record
# the resolved version + SHA into the pin file so the *vendored* copy is fixed
# even though the fetch tracks latest. jsdelivr is a fallback if unpkg is down.
URLS = [
    "https://unpkg.com/@viz-js/viz/lib/viz-standalone.js",
    "https://cdn.jsdelivr.net/npm/@viz-js/viz/lib/viz-standalone.js",
]

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
DEST = os.path.join(ASSETS, "viz-standalone.js")
PIN = DEST + ".sha256"


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _read_pin():
    if os.path.isfile(PIN):
        with open(PIN, encoding="utf-8") as fh:
            return fh.read().split()[0].strip()
    return None


def check():
    if not os.path.isfile(DEST):
        print("missing: %s (run without --check to fetch)" % DEST, file=sys.stderr)
        return 1
    with open(DEST, "rb") as fh:
        got = _sha256(fh.read())
    pin = _read_pin()
    if pin is None:
        print("warn: no pin file %s; vendored hash is %s" % (PIN, got), file=sys.stderr)
        return 1
    if got != pin:
        print("FAIL: %s sha256 %s != pinned %s" % (DEST, got, pin), file=sys.stderr)
        return 2
    print("ok: viz-standalone.js matches pin (%s…)" % got[:16])
    return 0


def _download():
    last = None
    for url in URLS:
        try:
            print("downloading %s" % url)
            req = urllib.request.Request(url, headers={"User-Agent": "distill-ddd-fetch"})
            with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (https)
                return resp.read(), resp.geturl()
        except Exception as e:  # try next mirror
            print("  failed: %s" % e, file=sys.stderr)
            last = e
    raise last if last else RuntimeError("no URLs configured")


def fetch():
    os.makedirs(ASSETS, exist_ok=True)
    data, final_url = _download()
    got = _sha256(data)
    pin = _read_pin()
    if pin is not None and got != pin:
        print("ABORT: downloaded sha256 %s != pinned %s" % (got, pin), file=sys.stderr)
        return 2
    with open(DEST, "wb") as fh:
        fh.write(data)
    # record the version the CDN actually served (…/@viz-js/viz@X.Y.Z/…)
    m = re.search(r"@viz-js/viz@([0-9][^/]*)", final_url)
    version = m.group(1) if m else "unknown"
    if pin is None:
        with open(PIN, "w", encoding="utf-8") as fh:
            fh.write("%s  viz-standalone.js  # @viz-js/viz@%s\n" % (got, version))
        print("TOFU: established pin %s (@viz-js/viz@%s)" % (got, version))
        print("  -> verify against npm integrity for @viz-js/viz@%s before "
              "committing %s + its .sha256" % (version, DEST))
    else:
        print("ok: matches existing pin")
    print("vendored: %s (%d bytes, @viz-js/viz@%s)" % (DEST, len(data), version))
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    return fetch()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
