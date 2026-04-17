# Phase 9: Workflows — ワークフローのパイプライン構造を対話で詰める

## 目的

Event Storming で特定した Command 群の中から実装対象を絞り込み、各ワークフローのステージ(中間型)・ステップ(関数)・依存・エラー・副作用・発行イベントを対話で設計する。
『Domain Modeling Made Functional』(Scott Wlaschin) Ch.5 (Domain Modeling with Types) および Ch.7 (Modeling Workflows as Pipelines) に準拠。

成果物は `docs/domain/workflows.md` というマークダウン 1 本。ここで決めた設計が、のちの型定義生成やシナリオ検証の土台になる。

## 背景: ワークフロー = パイプライン

DMMF のコア発想は「ビジネスワークフローを関数合成のパイプラインとして設計する」こと。

- 入力 (`UnvalidatedOrder`) に対して、段階的に変換(validate → price → acknowledge)を通すたびに、データの信頼水準が上がっていく
- **ステージ間の型を分ける** ことで「どの段階で何が保証されているか」がコンパイラで強制される
- 副作用 (I/O) はパイプラインの境界に寄せ、中間の変換は純粋関数として保つ
- エラーは例外ではなく **Result / OR 型** で表現し、ビジネスエラーと技術的例外を仕分ける

この章は対話で上記の構造を詰める場。コードは書かない。マークダウンで「型駆動の設計ドラフト」を完成させる。

## 入力

既存アーティファクトを読み込んで材料にする。

| 参照元 | 使うもの |
|-------|--------|
| event-storming.md | Command / Event の一覧 |
| aggregates.md | 集約の操作、不変条件 |
| domain-events.md | Event の属性、因果関係 |
| glossary.md | 用語の正式名 |
| validation.md (任意) | 先行シナリオからの逆算材料 |

## 進行手順

### Step 1: 実装対象ワークフローの絞り込み

Event Storming で洗い出した Command は通常 5〜20 個ある。全部を同時に設計するのは重すぎる。MVP に含めるものと後回しにするものを対話で決める。

質問:
- 「Event Storming で N 個の Command が出ました。まず実装したいのはどれですか?」
- 「業務上のクリティカルパス(これが止まるとビジネスが止まる)はどれですか?」
- 「MVP に含めるワークフローは?」

優先度の判断基準:
1. Core Domain に属するものを最優先
2. 他ワークフローへの依存が少ないもの(または依存元から順に)
3. 顧客の主要動線に直結するもの

成果: 実装対象ワークフローの優先順位付きリスト。未実装決定のものも理由と共に記録する。

### Step 2: 各ワークフローの輪郭

1 ワークフローずつ、対話で以下を決める。

質問:
- 「このワークフローの発動契機は何ですか?(HTTP リクエスト / スケジュール / 他ワークフローの Event / ユーザー操作)」
- 「最終的に何が起きれば成功ですか?(返り値 / 発行されるイベント / 保存される状態)」
- 「どういうカテゴリの失敗がありえますか?(検証エラー / 外部サービスエラー / ドメインルール違反)」
- 「このワークフローは同期ですか? 非同期ですか? 長時間実行ですか?」

成果: ワークフロー 1 つあたり 1 段落の概要。

### Step 3: ステージ(中間型の系列)の設計

**ここが DMMF の肝**。同じビジネスオブジェクトが処理過程で異なる信頼水準を獲得していくことを、型で表現する。

質問:
- 「入力は何と呼びますか?(例: `UnvalidatedOrder`)」
- 「最初の変換が終わった時点で、確実に言えることは何ですか?」→ 次のステージ名の由来
- 「さらに次の変換が終わると何が確定しますか?」
- 「最終的な状態は?」

典型例:
```
UnvalidatedOrder → ValidatedOrder → PricedOrder → AcknowledgedOrder
```

各ステージについて、**「この型の値を受け取ったコードは何を信じていいか」** を明文化する:

```
ValidatedOrder:
  - ProductCode が実在することが保証されている
  - Address が実在することが保証されている
  - 顧客 Email が形式的に valid
  - まだ価格は計算されていない
```

成果: ステージ名とその保証内容の表。

### Step 4: 各ステップの詳細

ステージ間の遷移 = ステップ(関数)。各ステップについて次を詰める。

| 項目 | 内容 |
|-----|-----|
| 名前 | 動詞形 (validateOrder, priceOrder) |
| 入力型 | 前ステージ |
| 出力型 | 次ステージ、または `Result<次ステージ, エラー>` |
| エラー | 発生しうるエラーの列挙 |
| 依存 | 外部情報源(DB、他 BC、設定値) |
| 副作用 | read-only / write / send-message / none |
| 発行 Event | あれば(通常は最終ステップ) |

質問:
- 「この変換の責務を 1 文で言うと?」(1 文で言えなければ分割候補)
- 「この変換に必要な情報は、全部入力型に含まれていますか? 外部から取ってくる情報は何ですか?」
- 「ここで起こる失敗の種類を全部挙げてください」
- 「副作用はありますか? あるなら本当にこのステップでしか解決できませんか?(末端に寄せられないか)」

### Step 5: 依存(ポート)の整理

全ステップの依存を集約して 1 つの表にする。

| 依存名 | 型シグネチャ | 実装元 | 同期/非同期 | 使うステップ |
|-------|-----------|-------|-----------|-----------|
| CheckProductCodeExists | `ProductCode → bool` | 商品カタログ DB | async | validateOrder |
| GetProductPrice | `ProductCode → Money` | 価格マスタ | async | priceOrder |
| SendAcknowledgment | `Order → Unit` | Email ゲートウェイ | async (fire-and-forget) | acknowledgeOrder |

質問:
- 「この依存は純粋関数として扱えますか? 失敗はどう型に現れますか?」
- 「複数のワークフローで同じ依存を使いますか?(共通化候補)」
- 「この依存は他の BC から来るものですか?(ACL 配置の判断材料)」

### Step 6: エラーカタログ

ワークフロー全体のエラー型を OR 型として整理する。

```
type PlaceOrderError =
    | ValidationError of ValidationError
    | PricingError of PricingError
    | RemoteServiceError of RemoteServiceError

and ValidationError =
    | InvalidProductCode of code: string
    | AddressNotFound of address: string
    | InvalidEmail

and PricingError =
    | UnknownProduct of ProductCode
    | PriceListUnavailable
```

質問:
- 「このエラーはユーザーに見せますか? 内部ログだけですか?」(ドメインエラー vs システム例外の仕分け)
- 「このエラーに対して UI はどう応答しますか?」(UI 仕様への入力)
- 「エラーを共通化できますか? 別々にする方が表現力が上がりますか?」

成果: エラー型の階層図と、各エラーの発生元ステップの対応表。

### Step 7: イベント発行タイミング

ワークフローの各段階で発行される Event を整理。

| ステップ | 発行イベント | 条件 | 購読側 BC |
|--------|----------------|-----|---------|
| priceOrder 成功 | BillableOrderPlaced | 常に | Billing BC |
| acknowledgeOrder 成功 | AcknowledgmentSent | 送信成功時のみ | Notification BC |
| (ワークフロー完了) | OrderPlaced | 全ステップ成功時 | Shipping BC, Analytics BC |

質問:
- 「この Event はこのステップのどの時点で発行すべきですか?(ステップ内での順序)」
- 「domain-events.md にこの Event の定義がありますか?(なければ Phase 6 に戻る)」
- 「イベント発行失敗は別扱い(アウトボックスパターン等)にしますか?」

### Step 8: 副作用の境界(I/O at the edges)

DMMF の原則「I/O は境界に」を具体化する。

視覚化:
```
[ 外界 ]  →  [ 入力ゲート ]  →  [ 純粋なドメインロジック ]  →  [ 出力ゲート ]  →  [ 外界 ]
 DTO           検証                  中間型の変換連鎖            イベント発行    Event Bus
                                                                DTO 生成       DB 保存
```

質問:
- 「検証ステップ以外で DB や外部 API を叩く箇所はありますか? 最初と最後に寄せられませんか?」
- 「この依存を入力の一部として前処理できませんか?(pull の purify)」
- 「副作用のあるステップと無いステップを表にすると?」

### Step 9: ワークフロー間の関係

複数ワークフローがある場合、依存関係を整理する。

```
PlaceOrder --[OrderPlaced]--> ShipOrder
PlaceOrder --[BillableOrderPlaced]--> IssueInvoice
ShipOrder --[OrderShipped]--> NotifyCustomer
```

質問:
- 「これらは Event で繋ぎますか? 直接呼び出しますか?」(Event-driven vs orchestration)
- 「長時間・複数ステップにまたがるフローはありますか?(Saga 候補)」
- 「補償トランザクションが必要な箇所は?」

## `--challenge` モード

設計の「当たり前」を壊して検証するための追加質問。

- 「このステップ分割は本当にドメインを反映しているか? 実装都合の分割では?」
- 「中間型 N 個は多すぎないか? 本当に区別が必要か?」
- 「この依存は本当にこのステップで必要か? もっと上流に寄せられないか?」
- 「このエラーは本当にドメインエラーか? 技術的例外にすべきでは?」
- 「このワークフローは同期でいいのか? ユーザーを 2 秒待たせて大丈夫か?」
- 「副作用のあるステップが中間にある。ここを pure にできないか?」
- 「Event で繋ぐべき箇所を直接呼び出しにしていないか?(隠れた結合)」

## `--analyze` モード

既存コードベースに対する差分指摘モード。

1. プロジェクトの `src/**/application/**`、`src/**/usecases/**`、`src/**/workflows/**` などを探索
2. 既存のユースケース実装と設計したワークフローを突き合わせる
3. 以下のパターンを指摘:
   - **ステージ分けされていないモノリシック実装** → 中間型の導入提案
   - **例外ベースのエラーハンドリング** → Result 型への変換提案
   - **I/O がステップ中間に散在** → 境界への集約提案
   - **依存がクラスのフィールドとして注入されている** → 関数引数への変換提案

## 他フェーズとの連携

### 入力元

```
storming.md  ──┐
aggregates.md ─┼─→ Phase 9 (workflows) ──→ workflows.md
events.md   ───┤
glossary.md ───┘
```

### フィードバック先

Phase 9 の対話中に発見された問題を、元フェーズに差し戻す提案として記録する。

| 発見パターン | 差し戻し先 |
|-----------|----------|
| 集約に無い操作が必要 | Phase 5 (aggregates) |
| 未定義の Event が必要 | Phase 6 (events) |
| 用語集に無い中間型名が登場 | Phase 8 (glossary) |
| シナリオと矛盾する設計 | Phase 7 (validate) |
| BC 境界を跨ぐ問題 | Phase 3 (contexts) |

workflows.md の末尾「フィードバック」セクションにまとめる。

### Phase 7 (validate) との順序関係

**順序はどちらでもよい**ように設計する。

- Phase 7 を先にやっていれば、validation.md のシナリオを「このワークフローのどのステップに対応するか」で突き合わせられる
- Phase 9 を先にやっていれば、Phase 7 は各ワークフローについて Given/When/Then を書く材料として workflows.md を使える

## 成果物テンプレート (workflows.md)

```markdown
# Workflows — ワークフロー設計

生成日: YYYY-MM-DD
前提フェーズ: storming ✓ / aggregates ✓ / events ✓ / glossary ✓

## 実装対象ワークフロー一覧(優先度順)

| # | 名前 | Bounded Context | 優先度 | 理由 |
|---|-----|---------------|-------|-----|
| 1 | PlaceOrder | Order-Taking | 高 | Core Domain、主要動線 |
| 2 | ShipOrder | Shipping | 高 | PlaceOrder の下流 |
| 3 | CancelOrder | Order-Taking | 中 | 異常系対応 |
| 4 | IssueInvoice | Billing | 中 | Generic Subdomain |

(未実装決定: ProcessRefund、ChangeShippingAddress — 理由: MVP 外)

---

## Workflow 1: PlaceOrder (Order-Taking BC)

### 概要

- 発動契機: HTTP POST /orders
- 最終出力: `Result<PlaceOrderEvents, PlaceOrderError>`
- 性質: 同期、短時間(< 2s 目標)

### ステージ(中間型の系列)

```
UnvalidatedOrder → ValidatedOrder → PricedOrder → AcknowledgedOrder
```

| ステージ | この型が保証すること |
|--------|------------------|
| UnvalidatedOrder | (外部入力、何も保証されない) |
| ValidatedOrder | ProductCode/Address/Email が形式的に valid、ProductCode/Address が実在 |
| PricedOrder | 各行の価格が確定、合計金額が計算済み |
| AcknowledgedOrder | 顧客への受付メールが送信済み |

### ステップ

#### Step 1: validateOrder

- 入力: `UnvalidatedOrder`
- 出力: `Result<ValidatedOrder, ValidationError>`
- 責務: 入力ゲート。形式検証と実在性確認
- 依存: `CheckProductCodeExists`, `CheckAddressExists`
- 副作用: read-only(マスタ照会のみ)
- エラー: `InvalidProductCode`, `AddressNotFound`, `InvalidEmail`
- 発行 Event: なし

#### Step 2: priceOrder

- 入力: `ValidatedOrder`
- 出力: `Result<PricedOrder, PricingError>`
- 責務: 各行の価格を引当、合計を計算
- 依存: `GetProductPrice`
- 副作用: read-only
- エラー: `UnknownProduct`, `PriceListUnavailable`
- 発行 Event: `BillableOrderPlaced`(成功時)

#### Step 3: acknowledgeOrder

- 入力: `PricedOrder`
- 出力: `AcknowledgedOrder`(エラーにしない。送信失敗は後続でリトライ)
- 責務: 顧客確認メール送信
- 依存: `SendAcknowledgment`
- 副作用: write(メッセージング)
- エラー: なし(失敗は Event で別管理)
- 発行 Event: `AcknowledgmentSent`(成功時のみ)

#### Step 4: createEvents

- 入力: `AcknowledgedOrder`
- 出力: `PlaceOrderEvents[]`
- 責務: 下流 BC に流す Event の組み立て
- 依存: なし
- 副作用: なし(純粋)
- 発行 Event: `OrderPlaced`(常に)

### 依存(ポート一覧)

| 名前 | 型 | 実装元 | 同期性 | 使用ステップ |
|-----|---|-------|-------|-----------|
| CheckProductCodeExists | `ProductCode → Task<bool>` | 商品カタログ BC (ACL 経由) | async | validateOrder |
| CheckAddressExists | `Address → Task<Result<Address, AddressError>>` | 住所検証サービス | async | validateOrder |
| GetProductPrice | `ProductCode → Task<Price>` | 価格マスタ DB | async | priceOrder |
| SendAcknowledgment | `Order → Task<unit>` | Email ゲートウェイ | async | acknowledgeOrder |

### エラーカタログ

```
type PlaceOrderError =
    | Validation of ValidationError
    | Pricing of PricingError

type ValidationError =
    | InvalidProductCode of string
    | AddressNotFound of Address
    | InvalidEmail of string

type PricingError =
    | UnknownProduct of ProductCode
    | PriceListUnavailable
```

UI 表示マッピング(後続フェーズで活用):

| エラー | UI 反応 |
|-------|--------|
| InvalidProductCode | 該当行の productCode を赤くし、「商品コードが無効です」 |
| AddressNotFound | 配送先全体にエラー表示 |
| PriceListUnavailable | 画面全体に「現在価格を取得できません。時間を置いて再試行してください」|

### 発行イベント

| Event | タイミング | Consumer |
|-------|---------|---------|
| BillableOrderPlaced | priceOrder 成功時 | Billing BC |
| AcknowledgmentSent | acknowledgeOrder 成功時 | Notification BC |
| OrderPlaced | 全成功時 | Shipping BC, Analytics BC |

### 副作用の配置

```
validateOrder    [read-only I/O]
     ↓
priceOrder       [read-only I/O]
     ↓
acknowledgeOrder [write I/O - messaging]
     ↓
createEvents     [pure]
```

### 関係するワークフロー

- 下流: `ShipOrder`(OrderPlaced を契機に起動)、`IssueInvoice`(BillableOrderPlaced 契機)
- 上流: なし

### 未解決の問い

- `AcknowledgmentSent` が送信失敗した場合のリトライ戦略(アウトボックス? Saga?)
- 価格マスタ側の変更中にリクエストが来たときの競合処理

---

## Workflow 2: ... (同構造で繰り返し)

---

## ワークフロー間の関係図

```
PlaceOrder --[OrderPlaced]--> ShipOrder
PlaceOrder --[BillableOrderPlaced]--> IssueInvoice
ShipOrder --[OrderShipped]--> NotifyCustomer
CancelOrder --[OrderCancelled]--> RefundPayment
```

## 共通パターンの識別

- すべてのワークフローで検証ステップが存在(共通の ValidationError 型を切り出せる)
- I/O 副作用は最初(検証)と最後(イベント/メッセージ送信)に集中(オニオン構造が適用可)

## フィードバック

- aggregates.md への追加提案: Order 集約に `acknowledge()` 操作を追加
- domain-events.md への追加提案: `AcknowledgmentSent` イベントが未定義
- glossary.md への追加提案: 「PricedOrder」「AcknowledgedOrder」を用語集に追加
```

## Phase 9 固有のフラグ

| フラグ | 動作 |
|-------|-----|
| `--pick <N,N,...>` | Step 1 の絞り込みをスキップし、指定した Command 番号のみを対象にする |
| `--from-validation` | validation.md を先に読み込み、そこのシナリオから逆算してステージ・ステップを組み立てる |
| `--analyze` | 既存ユースケース実装と設計を突き合わせ、差分を指摘する(上記 `--analyze` モード参照) |
| `--challenge` | 設計の前提を疑う追加質問を投げる(上記 `--challenge` モード参照) |

使用例:

```
/ddd workflows --pick 1,2,4        Command 1, 2, 4 のみを対象に設計
/ddd workflows --from-validation   validation.md のシナリオから逆算
/ddd workflows --challenge         中間型・ステップ分割を敵対的に検証
```
