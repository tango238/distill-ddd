#!/usr/bin/env python3
"""build_site.py — Render DDD artifacts (docs/domain/*.md) into one linked HTML site.

Self-contained: Python 3 standard library only (no pip install, no CDN).
Produces a dark-themed, self-contained HTML file per markdown doc, all wired
together by a common sticky top navigation ("files separate but linked").

Usage:
    python3 build_site.py [DIR]
        DIR defaults to docs/domain. Converts every *.md in DIR to <name>.html.

Optional config: DIR/_site.json
    {
      "title": "Domain Model",            # nav brand text
      "order": ["index", "bounded-contexts", ...],   # nav order (basenames, no ext)
      "labels": {"bounded-contexts": "Context Map"}  # short nav labels
    }
If absent: order = alphabetical (index/README first); labels derived from each
doc's first H1 (shortened at the first of — ( ： : /).

Markdown supported (the subset the DDD skill emits): ATX headings, GFM pipe
tables, fenced code blocks, ordered/unordered (nestable) lists, blockquotes,
horizontal rules, images (incl. .svg), links, **bold**, `inline code`.
Intra-site links ending in .md are rewritten to .html.
"""
import sys, os, re, json, html, shutil

try:
    import diagrams  # same scripts/ dir; optional
except Exception:
    diagrams = None


# ---------- inline ----------
def inline(text):
    codes = []

    def grab(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", grab, text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                  lambda m: '<img src="%s" alt="%s">' % (rewrite_link(m.group(2)), m.group(1)), text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  lambda m: '<a href="%s">%s</a>' % (rewrite_link(m.group(2)), m.group(1)), text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)

    def restore(m):
        c = codes[int(m.group(1))]
        c = c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return "<code>%s</code>" % c

    return re.sub(r"\x00(\d+)\x00", restore, text)


def rewrite_link(url):
    # keep anchors/external untouched; rewrite local *.md -> *.html
    m = re.match(r"^([^#?]+)\.md(#.*)?$", url)
    if m and "://" not in url:
        return m.group(1) + ".html" + (m.group(2) or "")
    return url


# ---------- block ----------
def render_table(rows):
    def cells(line):
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [c.strip() for c in line.split("|")]

    header = cells(rows[0])
    aligns = []
    for c in cells(rows[1]):
        l, r = c.startswith(":"), c.endswith(":")
        aligns.append("center" if l and r else "right" if r else "left" if l else "")
    out = ["<table>", "<thead><tr>"]
    for i, h in enumerate(header):
        a = aligns[i] if i < len(aligns) else ""
        out.append('<th%s>%s</th>' % (' style="text-align:%s"' % a if a else "", inline(h)))
    out.append("</tr></thead><tbody>")
    for r in rows[2:]:
        out.append("<tr>")
        cs = cells(r)
        for i, c in enumerate(cs):
            a = aligns[i] if i < len(aligns) else ""
            out.append('<td%s>%s</td>' % (' style="text-align:%s"' % a if a else "", inline(c)))
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def render_list(lines):
    out = []
    stack = []  # (indent, tag)
    for ln in lines:
        m = re.match(r"(\s*)([-*+]|\d+\.)\s+(.*)", ln)
        indent = len(m.group(1))
        tag = "ol" if m.group(2).endswith(".") else "ul"
        content = inline(m.group(3))
        while stack and indent < stack[-1][0]:
            out.append("</li></%s>" % stack.pop()[1])
        if not stack or indent > stack[-1][0]:
            stack.append((indent, tag))
            out.append("<%s>" % tag)
            out.append("<li>" + content)
        else:
            out.append("</li>")
            out.append("<li>" + content)
    while stack:
        out.append("</li></%s>" % stack.pop()[1])
    return "".join(out)


LIST_RE = re.compile(r"\s*([-*+]|\d+\.)\s+")


DIRECTIVE_RE = re.compile(r"^<!--\s*ddd:diagram:([a-z0-9-]+)\s*-->$")


def md_to_html(md, diagrams_dot=None):
    lines = md.split("\n")
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        # diagram directive: <!-- ddd:diagram:context-map -->
        dm = DIRECTIVE_RE.match(s)
        if dm:
            kind = dm.group(1)
            if diagrams_dot and diagrams_dot.get(kind):
                out.append(figure_html(kind, diagrams_dot[kind]))
            i += 1
            continue
        # fenced code
        if s.startswith("```"):
            j = i + 1
            buf = []
            while j < n and not lines[j].strip().startswith("```"):
                buf.append(lines[j])
                j += 1
            code = html.escape("\n".join(buf))
            out.append("<pre><code>%s</code></pre>" % code)
            i = j + 1
            continue
        # heading
        m = re.match(r"(#{1,6})\s+(.*)", line)
        if m:
            lv = len(m.group(1))
            text = inline(m.group(2).strip())
            anchor = re.sub(r"[^a-z0-9]+", "-", m.group(2).strip().lower()).strip("-")
            out.append('<h%d id="%s">%s</h%d>' % (lv, anchor, text, lv))
            i += 1
            continue
        # hr
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            out.append("<hr>")
            i += 1
            continue
        # table (header + separator row of ---)
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", lines[i + 1]) and "-" in lines[i + 1]:
            j = i
            rows = []
            while j < n and "|" in lines[j] and lines[j].strip():
                rows.append(lines[j])
                j += 1
            out.append(render_table(rows))
            i = j
            continue
        # blockquote
        if s.startswith(">"):
            j = i
            buf = []
            while j < n and lines[j].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[j]))
                j += 1
            out.append("<blockquote>%s</blockquote>" % "<br>".join(inline(b) for b in buf if b.strip()))
            i = j
            continue
        # list
        if LIST_RE.match(line):
            j = i
            buf = []
            while j < n and (LIST_RE.match(lines[j]) or (lines[j].strip() == "" and j + 1 < n and LIST_RE.match(lines[j + 1]))):
                if lines[j].strip():
                    buf.append(lines[j])
                j += 1
            out.append(render_list(buf))
            i = j
            continue
        # paragraph
        j = i
        buf = []
        while j < n and lines[j].strip() and not lines[j].strip().startswith("```") \
                and not re.match(r"#{1,6}\s", lines[j]) and not LIST_RE.match(lines[j]) \
                and not lines[j].strip().startswith(">") \
                and not re.match(r"^(-{3,}|\*{3,}|_{3,})$", lines[j].strip()):
            buf.append(lines[j].strip())
            j += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
        i = j
    return "\n".join(out)


# ---------- diagrams ----------
def figure_html(kind, dot):
    """Embed DOT as a renderable figure.

    The DOT lives in a <script type="text/vnd.graphviz"> block (raw text, no
    attribute escaping). viz-standalone.js (if present) renders it to inline
    SVG on load; without it, the <pre> fallback shows the DOT source plus the
    ⧉ copy button, so the page degrades gracefully.
    """
    safe = dot.replace("</script", "<\\/script").replace("<!--", "<\\!--")
    pre = html.escape(dot)
    return (
        '<figure class="jig-graph" data-kind="%s">\n'
        '  <div class="jig-toolbar">'
        '<button type="button" data-act="dir" title="Switch direction">⇄</button>'
        '<button type="button" data-act="svg" title="Download SVG">⬇ SVG</button>'
        '<button type="button" data-act="src" title="Copy DOT source">⧉ DOT</button>'
        '</div>\n'
        '  <script type="text/vnd.graphviz">%s</script>\n'
        '  <div class="jig-canvas"><pre class="jig-fallback">%s</pre></div>\n'
        '</figure>' % (html.escape(kind), safe, pre))


GRAPH_CSS = """
figure.jig-graph{margin:18px 0;background:#0b1220;border:1px solid var(--line);border-radius:12px;overflow:hidden}
figure.jig-graph .jig-toolbar{display:flex;gap:6px;justify-content:flex-end;padding:8px 10px;border-bottom:1px solid var(--line);background:#0d1526}
figure.jig-graph .jig-toolbar button{background:#172033;color:var(--muted);border:1px solid var(--line);border-radius:6px;font-size:12px;padding:3px 9px;cursor:pointer}
figure.jig-graph .jig-toolbar button:hover{background:#1e293b;color:var(--txt)}
figure.jig-graph .jig-canvas{padding:16px;overflow:auto;text-align:center}
figure.jig-graph .jig-canvas svg{max-width:100%;height:auto}
figure.jig-graph .jig-fallback{background:none;border:none;text-align:left;color:var(--muted);margin:0}
"""

INIT_JS = """
(function(){
  var graphs=document.querySelectorAll('figure.jig-graph');
  if(!graphs.length) return;
  // Copy-DOT works without the renderer, so bind it unconditionally (the
  // documented graceful-degradation path when viz-standalone.js is absent).
  graphs.forEach(function(g){
    var node=g.querySelector('script[type=\"text/vnd.graphviz\"]');
    if(!node) return;
    var src=node.textContent, b=g.querySelector('[data-act=src]');
    if(b) b.onclick=function(){ if(navigator.clipboard) navigator.clipboard.writeText(src); };
  });
  if(!(window.Viz&&window.Viz.instance)) return;  // no renderer: keep DOT fallback
  window.Viz.instance().then(function(viz){
    graphs.forEach(function(g){
      var node=g.querySelector('script[type=\"text/vnd.graphviz\"]');
      if(!node) return;
      var src=node.textContent, dir='LR', canvas=g.querySelector('.jig-canvas');
      function render(){
        var dot=src.replace(/rankdir\\s*=\\s*\"?(LR|TB)\"?/,'rankdir=\"'+dir+'\"');
        try{var svg=viz.renderSVGElement(dot);canvas.innerHTML='';canvas.appendChild(svg);}
        catch(e){/* keep fallback */}
      }
      render();
      var b;
      if((b=g.querySelector('[data-act=dir]'))) b.onclick=function(){dir=(dir==='LR'?'TB':'LR');render();};
      if((b=g.querySelector('[data-act=svg]'))) b.onclick=function(){
        var s=canvas.querySelector('svg'); if(!s) return;
        var blob=new Blob([s.outerHTML],{type:'image/svg+xml'});
        var a=document.createElement('a');a.href=URL.createObjectURL(blob);
        a.download=(g.dataset.kind||'diagram')+'.svg';document.body.appendChild(a);a.click();a.remove();
      };
    });
  });
})();
"""


# ---------- glossary (Phase 7) ----------
def _row_cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_glossary_terms(body):
    """Find a `用語 | 英語 | 定義` table in a section → [{term, en, def}]."""
    lines = body.split("\n")
    for i, l in enumerate(lines):
        if "|" not in l:
            continue
        header = [c.lower() for c in _row_cells(l)]
        if not any("用語" in h or "term" in h for h in header):
            continue
        if i + 1 >= len(lines) or "-" not in lines[i + 1]:
            continue

        def col(*names):
            for idx, h in enumerate(header):
                if any(n in h for n in names):
                    return idx
            return None

        ci = {"term": col("用語", "term"), "en": col("英語", "english", "en"),
              "def": col("定義", "definition", "def")}
        # require an 英語/定義 column so cross-context tables (用語|意味A|意味B)
        # aren't mistaken for a term glossary
        if ci["en"] is None and ci["def"] is None:
            continue
        rows, j = [], i + 2
        while j < len(lines) and "|" in lines[j] and lines[j].strip():
            cs = _row_cells(lines[j])

            def g(key):
                k = ci[key]
                return cs[k].strip() if k is not None and k < len(cs) else ""

            if g("term") and g("term") != "---":
                rows.append({"term": g("term"), "en": g("en"), "def": g("def")})
            j += 1
        return rows or None
    return None


def glossary_body(md, dots=None):
    """Render glossary.md as filterable term cards with a logical⇔physical toggle.

    Per-BC sections (## headings) whose table is a 用語/英語/定義 grid become card
    grids; other sections fall back to normal markdown so nothing is lost. Returns
    None when no term table is found (caller then uses the default renderer).
    """
    heads = list(re.finditer(r"^##\s+(.+?)\s*$", md, re.M))
    if not heads:
        return None
    pre = md[:heads[0].start()]
    sections = []
    any_terms = False
    for k, h in enumerate(heads):
        body = md[h.end():(heads[k + 1].start() if k + 1 < len(heads) else len(md))]
        terms = parse_glossary_terms(body)
        any_terms = any_terms or bool(terms)
        sections.append((h.group(1).strip(), terms, body))
    if not any_terms:
        return None

    out = [md_to_html(pre, dots)]
    out.append('<div class="gl-toolbar">'
               '<input class="gl-filter" type="search" placeholder="用語を絞り込み…" '
               'aria-label="filter terms">'
               '<button type="button" class="gl-toggle" data-act="toggle">'
               'T 英語表示</button></div>')
    idx = []
    for n, (title, terms, _) in enumerate(sections):
        if terms:
            idx.append('<a href="#gl-sec-%d">%s</a>' % (n, html.escape(title)))
    if idx:
        out.append('<div class="gl-index">%s</div>' % "".join(idx))

    for n, (title, terms, body) in enumerate(sections):
        out.append('<h2 id="gl-sec-%d">%s</h2>' % (n, inline(title)))
        if not terms:
            out.append(md_to_html(body, dots))
            continue
        out.append('<div class="gl-grid">')
        for t in terms:
            search = html.escape(" ".join((t["term"], t["en"], t["def"])).lower())
            phys = '<span class="gl-physical">%s</span>' % inline(t["en"]) if t["en"] else ""
            out.append('<div class="gl-card" data-search="%s">'
                       '<div class="gl-name"><span class="gl-logical">%s</span>%s</div>'
                       '<div class="gl-def">%s</div></div>'
                       % (search, inline(t["term"]), phys, inline(t["def"])))
        out.append('</div>')
    return "\n".join(out)


GLOSSARY_CSS = """
.gl-toolbar{display:flex;gap:10px;margin:18px 0 6px;flex-wrap:wrap}
.gl-filter{flex:1;min-width:200px;background:#0b1220;border:1px solid var(--line);border-radius:8px;color:var(--txt);padding:8px 12px;font-size:14px}
.gl-toggle{background:#172033;color:var(--muted);border:1px solid var(--line);border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer;white-space:nowrap}
.gl-toggle:hover{background:#1e293b;color:var(--txt)}
.gl-index{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 18px}
.gl-index a{font-size:12px;color:var(--muted);text-decoration:none;padding:3px 10px;border:1px solid var(--line);border-radius:999px}
.gl-index a:hover{background:#172033;color:var(--txt)}
.gl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin:14px 0}
.gl-card{background:#0b1220;border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.gl-card .gl-name{display:flex;flex-direction:column;gap:1px;margin-bottom:6px}
.gl-logical{font-weight:700;color:#f1f5f9;font-size:15px}
.gl-physical{color:var(--muted);font-size:12px;font-family:ui-monospace,Menlo,monospace}
body.gl-physical-mode .gl-name .gl-logical{order:2;font-weight:400;color:var(--muted);font-size:12px;font-family:ui-monospace,Menlo,monospace}
body.gl-physical-mode .gl-name .gl-physical{order:1;font-weight:700;color:#f1f5f9;font-size:15px;font-family:inherit}
.gl-def{font-size:13px;color:var(--txt);line-height:1.6}
.gl-card.gl-hidden{display:none}
"""

GLOSSARY_JS = """
(function(){
  var f=document.querySelector('.gl-filter');
  if(f){f.addEventListener('input',function(){
    var q=f.value.trim().toLowerCase();
    document.querySelectorAll('.gl-card').forEach(function(c){
      c.classList.toggle('gl-hidden', q && (c.dataset.search||'').indexOf(q)<0);
    });
  });}
  var t=document.querySelector('.gl-toggle');
  if(t){t.addEventListener('click',function(){
    var phys=document.body.classList.toggle('gl-physical-mode');
    t.textContent = phys ? 'T 用語表示' : 'T 英語表示';
  });}
})();
"""


# ---------- site ----------
CSS = """:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--txt:#e2e8f0;--muted:#94a3b8;--accent:#7dd3fc}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:-apple-system,'Hiragino Kaku Gothic ProN','Segoe UI',sans-serif;line-height:1.75}
nav.top{position:sticky;top:0;z-index:10;background:#0b1220;border-bottom:1px solid var(--line);padding:10px 24px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
nav.top .brand{font-weight:700;font-size:14px;margin-right:12px;color:#fff}
nav.top a{color:var(--muted);text-decoration:none;font-size:13px;padding:5px 11px;border-radius:7px;white-space:nowrap}
nav.top a:hover{background:#172033;color:var(--txt)}
nav.top a.active{background:#334155;color:#fff;font-weight:600}
main{max-width:1000px;margin:0 auto;padding:32px 28px 96px}
main img{max-width:100%;height:auto;border-radius:12px;border:1px solid var(--line);display:block;margin:18px auto}
h1{font-size:26px;border-bottom:2px solid var(--line);padding-bottom:12px;margin-top:8px}
h2{font-size:20px;border-bottom:1px solid var(--line);padding-bottom:7px;margin-top:38px}
h3{font-size:16px;margin-top:28px;color:#cbd5e1}h4{font-size:14px;margin-top:20px;color:#cbd5e1}
a{color:var(--accent)}p,li{font-size:14.5px}
code{background:#0b1220;padding:2px 7px;border-radius:5px;font-size:13px;font-family:ui-monospace,Menlo,monospace}
pre{background:#0b1220;border:1px solid var(--line);border-radius:10px;padding:16px;overflow:auto;font-size:12.5px;line-height:1.55}
pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:13px}
th,td{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}
th{background:var(--card);font-weight:600}tr:nth-child(even) td{background:#172033}
blockquote{border-left:4px solid #475569;margin:16px 0;padding:4px 18px;color:var(--muted);background:#131c2e;border-radius:0 8px 8px 0}
hr{border:none;border-top:1px solid var(--line);margin:32px 0}
ul,ol{padding-left:24px}li{margin:4px 0}strong{color:#f1f5f9}
footer{max-width:1000px;margin:0 auto;padding:20px 28px 60px;color:var(--muted);font-size:12px;border-top:1px solid var(--line)}
"""

PAGE = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title><style>{css}</style></head><body>
<nav class="top"><span class="brand">{brand}</span>{nav}</nav>
<main>
{body}
</main>
<footer>{brand} &nbsp;|&nbsp; source: <code>{src}</code> &nbsp;|&nbsp; generated by /ddd publish</footer>
{foot_extra}
</body></html>
"""


def first_h1(md):
    m = re.search(r"^#\s+(.+)$", md, re.M)
    return m.group(1).strip() if m else None


def short_label(title, slug):
    if not title:
        return slug
    for sep in ("—", "(", "（", "：", ":", " / ", "/"):
        if sep in title:
            title = title.split(sep)[0]
    return title.strip() or slug


def main(argv):
    d = argv[1] if len(argv) > 1 else "docs/domain"
    if not os.path.isdir(d):
        print("error: not a directory: %s" % d, file=sys.stderr)
        return 2
    mds = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    if not mds:
        print("error: no .md files in %s" % d, file=sys.stderr)
        return 2
    slugs = [os.path.splitext(f)[0] for f in mds]

    cfg = {}
    cfgp = os.path.join(d, "_site.json")
    if os.path.isfile(cfgp):
        with open(cfgp, encoding="utf-8") as fh:
            cfg = json.load(fh)

    # Auto-generated diagrams (DOT) from the structured model artifacts.
    dots = {}
    if diagrams is not None:
        try:
            dots = diagrams.available(d, cfg.get("colors"))
        except Exception as e:
            print("warn: diagram generation skipped: %s" % e, file=sys.stderr)

    titles, bodies, has_graph, has_glossary = {}, {}, {}, {}
    for slug in slugs:
        with open(os.path.join(d, slug + ".md"), encoding="utf-8") as fh:
            md = fh.read()
        # Auto-place diagram markers (diagrams.py owns the per-kind anchors).
        if dots and diagrams is not None:
            md = diagrams.autoplace(slug, md, dots)
        titles[slug] = first_h1(md) or slug
        gl = None
        if slug == "glossary":
            try:
                gl = glossary_body(md, dots)
            except Exception as e:
                print("warn: glossary render fell back: %s" % e, file=sys.stderr)
        if gl is not None:
            bodies[slug] = gl
            has_glossary[slug] = True
        else:
            bodies[slug] = md_to_html(md, dots)
            has_glossary[slug] = False
        has_graph[slug] = "jig-graph" in bodies[slug]

    order = cfg.get("order")
    if order:
        order = [s for s in order if s in slugs] + [s for s in slugs if s not in order]
    else:
        pri = {"index": 0, "readme": 0, "README": 0}
        order = sorted(slugs, key=lambda s: (pri.get(s.lower(), 1), s))

    labels = cfg.get("labels", {})
    brand = cfg.get("title", "Domain Model")

    def nav_html(current):
        items = []
        for s in order:
            lbl = html.escape(labels.get(s) or short_label(titles[s], s))
            cls = ' class="active"' if s == current else ""
            items.append('<a href="%s.html"%s>%s</a>' % (s, cls, lbl))
        return "".join(items)

    # Copy the vendored Graphviz-in-WASM renderer next to the pages, if shipped.
    viz_present = False
    if any(has_graph.values()):
        src_viz = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "assets", "viz-standalone.js")
        if os.path.isfile(src_viz):
            assets = os.path.join(d, "_assets")
            os.makedirs(assets, exist_ok=True)
            shutil.copy2(src_viz, os.path.join(assets, "viz-standalone.js"))
            viz_present = True
        else:
            print("note: scripts/assets/viz-standalone.js not vendored — "
                  "diagrams show DOT source fallback "
                  "(run scripts/fetch_viz.py to enable in-browser SVG)",
                  file=sys.stderr)

    css = CSS + (GRAPH_CSS if any(has_graph.values()) else "") \
        + (GLOSSARY_CSS if any(has_glossary.values()) else "")
    for slug in slugs:
        foot = ""
        if has_graph[slug]:
            if viz_present:
                foot += '<script src="./_assets/viz-standalone.js"></script>\n'
            foot += "<script>%s</script>" % INIT_JS
        if has_glossary[slug]:
            foot += "<script>%s</script>" % GLOSSARY_JS
        page = PAGE.format(title=html.escape(titles[slug]), css=css, brand=html.escape(brand),
                           nav=nav_html(slug), body=bodies[slug],
                           src=html.escape(d + "/" + slug + ".md"), foot_extra=foot)
        with open(os.path.join(d, slug + ".html"), "w", encoding="utf-8") as fh:
            fh.write(page)
        print("generated: %s.html" % slug)
    print("done: %d pages linked under '%s'" % (len(slugs), brand))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
