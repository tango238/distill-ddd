# Phase 12: Publish — 成果物を1つのリンク HTML サイトに束ねる

## 目的

これまでのフェーズ（discover〜simulate）で `docs/domain/` に蓄積したドメインモデルの
成果物（`*.md`）を、**共通ナビゲーションで相互リンクした self-contained な HTML サイト**に変換する。

「1つの HTML（ファイルは別だがリンクとしてまとめられている）」= 各 `*.md` → `*.html`、
全ページ上部に**同じタブ**を置き、現在ページをハイライト。外部依存なし（CDN 不要・オフライン可）。

## 進行手順

### Step 1: モデル調査の完了を確認

`docs/domain/` に少なくとも以下があること（足りなければ該当フェーズに戻る）:
- `bounded-contexts.md`（contexts）/ `event-storming.md`（storming）
- `aggregates.md`（aggregates）/ `domain-events.md`（events）/ `glossary.md`（glossary）
- 任意: `discovery.md`, `context-map.md`, `validation.md`, `workflows.md`, `model-inventory.md`, `index.md`

`--analyze` 系で既存コードからモデルを起こしている場合は、その成果物も同じ `docs/domain/` に置く。

### Step 2: ASCII 図を SVG 化（任意・推奨）

`*.md` 内のフロー/関係図（コードフェンスの ASCII アート）は、`docs/domain/diagrams/*.svg` として
**インライン SVG** に起こし、`![alt](./diagrams/foo.svg)` 参照に差し替えると見栄えが揃う。
- ダークテーマ（背景 `#0f172a`）に合わせ、コンテキスト色は Spotly=緑 / PMS=青 / Cleaning=橙 等で統一
- ディレクトリツリーやコード列挙は **図ではない**ので `<pre>` のまま残す
- 繰り返し構造（ライフロサイクル等）はデータ駆動でまとめて生成すると手早い

### Step 3: サイト生成スクリプトを実行

```sh
python3 <SKILL_DIR>/scripts/build_site.py docs/domain
```

`<SKILL_DIR>` はこのスキルの設置先（例: `~/.claude/skills/ddd`、`~/.codex/skills/ddd`、`~/.gemini/skills/ddd`）。
引数省略時は `docs/domain` を対象にする。各 `*.md` の隣に `*.html` を生成する。

スクリプトは **Python 3 標準ライブラリのみ**で動作（pip 不要）。サポートする Markdown:
ATX 見出し / GFM パイプ表 / フェンスコード / 入れ子リスト / 引用 / 水平線 / 画像(SVG含む) /
リンク / `**強調**` / `` `インラインコード` ``。`*.md` への相互リンクは自動で `*.html` に書き換える。

### Step 4: ナビ順序・ラベルの調整（任意）

既定のナビ順は「`index`/`README` 先頭→アルファベット順」、ラベルは各ドキュメントの最初の `# 見出し`を
短縮（`—` `(` `：` `/` の手前で切る）。明示したい場合は `docs/domain/_site.json` を置く:

```json
{
  "title": "Roomport ドメインモデル",
  "order": ["index", "bounded-contexts", "event-storming", "model-inventory",
            "aggregates", "domain-events", "glossary", "migration-guide"],
  "labels": { "bounded-contexts": "コンテキストマップ", "domain-events": "ドメインイベント" }
}
```

### Step 5: 検証

- 生成 HTML を 1〜2 ページ開き、**全タブが表示・現在ページがハイライト**されること
- 表・コード・画像（SVG）・相互リンク（`.html` 化）が壊れていないこと
- `python3 -c "import xml.dom.minidom" ...` 等で SVG の整形式性を確認してもよい

## 成果物

- `docs/domain/*.html` — 共通ナビで相互リンクされたドメインモデル・サイト一式
- 任意: `docs/domain/diagrams/*.svg`、`docs/domain/_site.json`

## メモ

- スクリプトは**冪等**。`*.md` を更新したら再実行すれば `*.html` が作り直される。
- 図を差し替えた後も `*.md` が正本。HTML は常に再生成物（バージョン管理は `*.md` + `*.svg` を主とする）。
- 既存のリッチな HTML（独自に作った対話的ページ等）がある場合、`build_site.py` は同名 `*.html` を
  上書きするので、上書きしたくないページは `*.md` を置かない or 退避すること。
