# Phase 6: Events — ドメインイベントの設計

## 目的

Domain Event の命名、プロパティ、因果関係を設計する。
Event Sourcing の適用可否も検討する。

## 設計ガイドライン (DDD Distilled Ch.6)

### 命名規則

- 過去形の動詞: `ProductCreated`, `BookingCanceled`, `CheckInFinished`
- ユビキタス言語を反映
- 「何が起きたか」が名前だけで明確

### プロパティの決定

1. そのイベントを引き起こした Command のプロパティを特定
2. Command の全プロパティを Event にも含める
3. イベントの `occurredOn` (発生日時) を必ず含める

質問:
- 「このイベントを受信した他のコンテキストは、何を知る必要がありますか?」
- 「足りない情報は Query-Back で取得できますか?」

### Enrichment vs Query-Back トレードオフ

| アプローチ | メリット | デメリット |
|----------|--------|---------|
| **Enrichment** (イベントにデータを詰める) | Consumer の自律性が高い | イベントが肥大化、セキュリティリスク |
| **Query-Back** (ID だけ渡して問い合わせ) | イベントが軽量 | Consumer と Publisher が結合 |

### 因果整合性 (Causal Consistency)

- Domain Event の因果順序が重要
- Sequence ID やタイムスタンプで因果関係を表現
- Consumer は因果の前提イベントを待ってから処理

## 進行手順

### Step 1: Command → Event マッピングの精査

Event Storming の結果を精査:
- 各 Command に対応する Event が漏れなくあるか
- タイマーやスケジュール起因のイベントはあるか

### Step 2: Event プロパティの設計

各 Event について:
- Command のプロパティをベースに
- Aggregate の ID は必須
- `occurredOn` は必須
- Enrichment の範囲を決定

### Step 3: Event Sourcing の検討

質問:
- 「この Aggregate の変更履歴を完全に追跡する必要がありますか?」
- 「コンプライアンスや監査の要件はありますか?」

Event Sourcing 採用時:
- Aggregate の状態 = Event Stream の再生
- append-only の Event Store
- CQRS との組み合わせがほぼ必須

## 成果物テンプレート

```markdown
# Domain Events

## イベント一覧

### {BoundedContext名}

#### {EventName}
- **発生元 Aggregate**: {Aggregate名}
- **トリガー**: {Command名} or {時間イベント}
- **プロパティ**:
  - `{propName}`: {型} — {説明}
  - `occurredOn`: Timestamp
- **Consumer**: {受信する Bounded Context / Aggregate}
- **Enrichment/Query-Back**: {どちらを採用、理由}

## Event Flow (コンテキスト間)

{Context A} --{EventName}--> {Context B}
  → {Context B での処理}

## Event Sourcing 対象
- {Aggregate名}: {採用/不採用} — {理由}

## 未解決の問い
- ...
```
