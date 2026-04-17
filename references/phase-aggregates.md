# Phase 5: Aggregates — 集約の設計

## 目的

Aggregate の4つのルールに基づき、トランザクション整合性境界を設計する。

## 4つのルール (DDD Distilled Ch.5)

### Rule 1: ビジネス不変条件を Aggregate 境界内で保護する

- トランザクション終了時に、Aggregate 内の全構成要素がビジネスルールに従って整合していること
- 質問: 「このデータが更新されたとき、同時に整合している必要があるデータは何ですか?」

### Rule 2: 小さな Aggregate を設計する

- Aggregate Root + 最小限の Entity/Value Object
- 巨大な Aggregate はトランザクション競合・メモリ問題の原因
- 質問: 「この Aggregate から分離できる概念はありますか? それは本当に同時に整合が必要ですか?」

### Rule 3: 他の Aggregate は ID のみで参照する

- 直接のオブジェクト参照ではなく ID (Value Object) で参照
- 質問: 「この Aggregate は他の Aggregate のインスタンスを直接保持していますか? ID 参照に置き換えられませんか?」

### Rule 4: 他の Aggregate は結果整合性で更新する

- 1トランザクションで1つの Aggregate のみ変更
- 他の Aggregate は Domain Event 経由で結果整合的に更新
- 質問: 「この2つの Aggregate を同時に更新する必要がありますか? 数秒の遅延は許容できますか?」

## 進行手順

### Step 1: Aggregate 候補のリストアップ

Event Storming の結果から Aggregate 候補を列挙。

### Step 2: Right-Sizing (Ch.5 の5ステップ)

1. 単一 Entity の小さな Aggregate から始める
2. Rule 1 に基づき、ビジネス不変条件とその時間枠をリストアップ
3. ドメインエキスパートに反応時間を確認: (a) 即時、(b) N秒/分/時間以内
4. 即時の場合 → 同一 Aggregate に合成
5. 遅延可の場合 → Domain Event + 結果整合性

### Step 3: 各 Aggregate の設計

各 Aggregate について:
- **Root Entity**: 名前、ID (Value Object)
- **内包する Entity**: 名前と役割
- **Value Object**: 属性を表す不変オブジェクト
- **ビジネス不変条件**: Aggregate 内で保護するルール
- **公開操作** (Command メソッド): ドメイン言語に基づく振る舞い
- **発行する Domain Event**: 操作の結果

### Step 4: Anemic Domain Model チェック

- Aggregate が getter/setter のみ → ビジネスロジックが Application Service に漏洩
- 「この Aggregate はどんなビジネス判断を行いますか?」
- 「この振る舞いは Aggregate 自身の責務ですか?」

## --analyze 時の追加手順

1. 既存の Entity/data class を読む
2. 4つのルールに照らして診断
3. 違反箇所を具体的に指摘

## 成果物テンプレート

```markdown
# Aggregates

## 集約一覧

### {Aggregate 名} (Bounded Context: {BC名})

**Root Entity**: {名前}
**ID**: {ID の Value Object}

**構成要素**:
- {Entity/VO名}: {役割}
- ...

**ビジネス不変条件**:
- {ルールの記述}
- ...

**操作**:
- `{commandName}({params})`: {説明} → 発行: `{EventName}`
- ...

**他 Aggregate との参照**: {ID のみで参照する Aggregate と ID 名}

**整合性**:
- {即時}: {同一 Aggregate 内の Entity}
- {結果整合}: {Domain Event 経由で更新される Aggregate}

## 未解決の問い
- ...
```
