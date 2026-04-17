# Phase 3: Contexts — Bounded Context とサブドメインの定義

## 目的

Event Storming で発見した境界を正式な Bounded Context として定義する。
各コンテキストのユビキタス言語のスコープを明確にし、サブドメインに分類する。

## 進行手順 (DDD Distilled Ch.2-3)

### Step 1: 言語の境界テスト

Event Storming の結果を見ながら:
- 「この用語 (例: "Policy") は全ての文脈で同じ意味ですか?」
- 「別の部門やチームで同じ言葉が違う意味で使われていませんか?」
- 「同じ概念に対して異なる名前が使われていませんか?」

判定基準: 同じ用語が異なる意味を持つ → 別の Bounded Context

### Step 2: "What is core?" チャレンジ

Ch.2 の Challenge and Unify プロセス:
- 各概念について「これは Core Domain のユビキタス言語に属するか?」を問う
- 属さないものを外に出す
- 例: `Tenant`, `User`, `Permission` は Scrum の言語ではない → Identity Context へ

### Step 3: Bounded Context の命名と定義

各コンテキストについて:
- **名前**: ビジネスドメインを反映した名前 (技術名ではない)
- **責務**: 1-2 文で何を扱うか
- **ユビキタス言語**: このコンテキスト内でのみ通用する用語リスト
- **チーム**: このコンテキストを所有するチーム (1 BC = 1 team が理想)

### Step 4: サブドメイン分類

| 種別 | 基準 |
|------|------|
| Core Domain | 競争優位。最大の投資。Ubiquitous Language を精緻に |
| Supporting | Core を支えるが差別化ではない。カスタム開発 |
| Generic | 汎用。購入 or 最小限の開発 |

理想: 1 Bounded Context = 1 Subdomain (1:1 対応)

## --challenge 時の追加質問

- 「この2つのコンテキストは本当に別ですか? 統合した方がシンプルでは?」
- 「このコンテキストは大きすぎませんか? 内部に別の言語が混在していませんか?」
- 「この Generic Subdomain は本当に Generic ですか? 実は差別化要因では?」

## 成果物テンプレート

```markdown
# Bounded Contexts

## Context Map 概要図

{ASCII or Mermaid 図}

## Bounded Context 一覧

### {Context 名} ({Core/Supporting/Generic})
- **責務**: {1-2文}
- **主要概念**: {Aggregate, Entity, Value Object の名前}
- **ユビキタス言語**: {このコンテキスト固有の用語}
- **所有チーム**: {チーム名 or TBD}

### ...

## 言語の境界で発見した事実
- 「{用語}」は {Context A} では {意味A}、{Context B} では {意味B}

## 未解決の問い
- ...
```
