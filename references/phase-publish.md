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

### Step 2: モデルから図を自動生成（jig 風・dddjava/jig 参考）

手書き SVG ではなく、**構造化された成果物（テーブル）から図を自動生成**する。
`scripts/diagrams.py` が `*.md` の構造化部分を読んで Graphviz DOT を出力し、`build_site.py` が
それを各ページに埋め込む。ブラウザ側で **viz-standalone.js（Graphviz の WASM 版）** が DOT を
インライン SVG に描画する（完全オフライン・`dot` バイナリ不要・CDN 不要）。

**対応する図:**

| 図 | 入力（正本 md の構造化部分） | 表現 |
|----|------------------------------|------|
| Context Map | `context-map.md` の関係テーブル + `bounded-contexts.md` の `### 名前 (Core/Supporting/Generic)` | コンテキスト=ノード（色分け／Core=太枠・Generic=破線）、関係=ラベル付きエッジ（C/S・ACL=ダイヤ矢印・OHS/PL）。**Partnership/Shared Kernel は双方向**、**Separate Ways/Big Ball of Mud/🔴 付箋は赤エッジ**で問題を可視化 |
| Workflow パイプライン（1ワークフロー1図） | `workflows.md` の `### ステージ` 系列 + `#### Step` の副作用・発行 Event・エラー | ステージ型=ノード（左→右で信頼水準が上がる）、ステップ=エッジ（副作用で色分け: read=青/write=橙/message=紫/pure=灰）、**発行イベント=金色のノート**、**失敗しうるステップは赤破線で `⚠ Error` sink にフォーク**（Result 型＝DMMF の2トラック鉄道） |
| Workflow 間の関係図 | `workflows.md` の `## ワークフロー間の関係図`（`A --[Event]--> B`） | ワークフロー=ノード、ドメインイベント=紫のラベル付きエッジ（イベント駆動の連鎖） |

**図の配置:** 既定では構造化部分の直近に自動挿入する（`context-map.md` → `#` 直下、
`workflows.md` → 各ワークフローの `### ステージ` 直後 + 関係図フェンス直後）。位置を明示したい場合は
md 本文に `<!-- ddd:diagram:context-map -->` / `<!-- ddd:diagram:wf-<workflow名> -->` /
`<!-- ddd:diagram:wf-relations -->` を置くと、そこに描画される。

**各図の操作ボタン**（jig 由来・vanilla JS）: `⇄` 方向切替（LR⇄TB）/ `⬇ SVG` ダウンロード / `⧉ DOT` ソースコピー。

**viz の vendoring（1回だけ・ネットワーク使用）:**

```sh
python3 <SKILL_DIR>/scripts/fetch_viz.py          # scripts/assets/ に取得 + SHA 記録
python3 <SKILL_DIR>/scripts/fetch_viz.py --check  # vendoring 済みコピーの検証
```

`scripts/assets/viz-standalone.js` が無い場合でも図は壊れない。**DOT ソースを `<pre>` で表示し
`⧉ DOT` でコピー→外部レンダラ（例: edotor.net / graphviz online）で描画**できる（graceful degradation）。

- 色は `_site.json` の `"colors": {"Spotly":"#22c55e", ...}` で固定可（無ければ自動パレット）
- ディレクトリツリーやコード列挙は **図ではない**ので `<pre>` のまま残す
- 旧来の手書き SVG（`![alt](./diagrams/foo.svg)`）も引き続き使える（画像として埋め込まれる）

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
- `docs/domain/_assets/viz-standalone.js` — 図描画ランタイム（vendoring 済みのとき自動コピー）
- 任意: `docs/domain/diagrams/*.svg`（手書き SVG）、`docs/domain/_site.json`

## メモ

- スクリプトは**冪等**。`*.md` を更新したら再実行すれば `*.html` が作り直される。
- 図を差し替えた後も `*.md` が正本。HTML は常に再生成物（バージョン管理は `*.md` + `*.svg` を主とする）。
- 既存のリッチな HTML（独自に作った対話的ページ等）がある場合、`build_site.py` は同名 `*.html` を
  上書きするので、上書きしたくないページは `*.md` を置かない or 退避すること。
