# Phase 11: Simulate — 型レベル検証と UI 項目抽出

## 目的

Phase 10 で生成された型を使って、次の 2 つの成果物を得る。

1. **ワークフローの型レベル検証**: Phase 7 validate のシナリオを、生成された型で組み立てて通るか確認する
2. **入力画面項目の自動抽出**: `Unvalidated*` 型の構造から UI フォーム項目を機械的に列挙する

DMMF Ch.9 (Implementation: Composing a Pipeline) の発想を借りて、「設計した型が実際のシナリオを表現可能か」「型から画面が導出できるか」を型レベルで検証する。ユーザー要望の「ドメインモデルだけでワークフロー検証と入力画面洗い出し」はこのフェーズで完結する。

## 進行手順

### Step 1: 既存アーティファクトの読み込み

- `docs/domain/code/types/*.ts` (Phase 10 の成果物、必須)
- `validation.md` (Phase 7 の成果物、シナリオ検証に必須)
- `workflows.md` (Phase 9 の成果物、対応づけに使用)
- `glossary.md` (フォーム項目のラベル引当に使用)

Phase 10 の code/ が無ければ、「まず Phase 10 を完了してください」で終了する。

### Step 2: 範囲の確認

- 「シナリオ検証と UI 項目抽出、両方やりますか? 片方だけですか?」
- 「シナリオが多いので優先度の高いものから絞り込みますか?」
- 「UI 項目抽出の対象画面はどれですか?」

## 5-1. ワークフロー検証

### 目的

Phase 7 の各シナリオを型レベルテストに変換する。「型で表現不可能なシナリオ」が見つかれば、それは **設計の穴** である。

### 進行手順

#### Step A1: シナリオ選定

- validation.md のシナリオ一覧を提示
- 優先度の高いもの (Core Domain、Core フロー、複数集約横断) から対話で選ぶ

#### Step A2: シナリオを型で組み立てる

シナリオごとに:

- Given 節 → 入力 `UnvalidatedOrder` 等をリテラルで構築
- When 節 → ワークフロー関数呼び出し (スタブ実装 OK)
- Then 節 → 戻り値の OR 型 (`Result<OrderPlaced, PlaceOrderError>`) を検証

質問:
- 「このシナリオを型で表現すると、`OrderId` が `string` で入ってきます。検証エラーはどう扱いますか?」
- 「このシナリオは 3 集約に触ります。結果整合性で大丈夫ですか?」
- 「Given 節の入力データに足りない情報はありませんか?」

シナリオを型で組み立てる過程で **Phase 5〜9 で抜けた情報が露出する**。これが本フェーズの価値。

#### Step A3: テスト雛形の生成

`docs/domain/code/simulations/<workflow-name>.spec.ts` として書き出す。

```typescript
// docs/domain/code/simulations/place_order.spec.ts
//
// 対応シナリオ: validation.md「正常: 注文受付成功」
// 自動生成: YYYY-MM-DD

import { describe, it, expect } from "vitest";
import type { UnvalidatedOrder } from "../types/stages";
import type { PlaceOrder } from "../types/workflows";

// スタブ実装 (常に成功を返す)
const placeOrderStub: PlaceOrder = (deps) => async (input) => ({
  kind: "Ok",
  value: [{ kind: "OrderPlaced", orderId: input.orderId, at: new Date() }],
});

describe("シナリオ: 注文受付成功", () => {
  it("Given 有効な注文、When placeOrder、Then OrderPlaced + BillableOrderPlaced", async () => {
    const input: UnvalidatedOrder = {
      kind: "Unvalidated",
      orderId: "ORD-001",
      customerEmail: "alice@example.com",
      lines: [{ productCode: "W1234", quantity: 2 }],
    };
    const deps = { /* スタブ依存 */ } as any;
    const result = await placeOrderStub(deps)(input);
    expect(result.kind).toBe("Ok");
  });
});
```

**重要**: スタブ実装は「常に成功を返す」等の単純なもので OK。本番実装はこのフェーズの目的外。目的は **設計の型レベル確認** と **シナリオが型で組み立てられること** の確認。

#### Step A4: 未表現シナリオの指摘

型で組み立てられなかったシナリオを列挙し、元フェーズへの差し戻し提案を添える。

## 5-2. 入力画面項目の洗い出し

### 目的

Command 入力型 (`Unvalidated*`) を起点に型構造を再帰的に展開し、UI フォーム項目を機械的に列挙する。
glossary.md から表示ラベルとヘルプテキストを引当、`ui-fields.md` に書き出す。

### アルゴリズム

1. Phase 10 で生成した Command 入力型 (例: `UnvalidatedOrder`) を列挙
2. 対象画面を対話で選ばせる
3. 型を再帰的に展開:
   - **Simple 型 (Brand)** → 1 フィールド。ラベル・検証規則を Smart Constructor から抽出
   - **AND 型** → サブセクション、子フィールドを再帰展開
   - **OR 型** → ラジオ/セレクト、選択肢ごとに異なる子フィールド
   - **`Option<T>`** → 任意項目フラグ付き
   - **配列 / `NonEmptyList`** → 動的追加/削除リスト (minimum 数を記録)
4. glossary.md から表示ラベルとヘルプテキストを引当
5. 見つからないラベルは対話で補完
6. 検証エラー ↔ UI フィールドのマッピング表を生成 (Phase 9 のエラーカタログから)
7. `docs/domain/ui-fields.md` に書き出し

### 対話の要点

- 表示ラベル: glossary から自動、無ければ対話で補完
- `Option<T>` の UI 扱い: 常時表示 / 展開リンク / チェックボックス切替 の 3 パターンから選ばせる
- `NonEmptyList` の初期状態: 空 1 件を出すかどうか
- 状態依存フィールド (例: productCode の W/G 接頭辞で quantity の検証規則が変わる): UI 切替方式を対話で決定

### 成果物テンプレート (`ui-fields.md`)

```markdown
# UI Fields — 入力画面項目仕様

Phase 11 で Unvalidated* 型から自動抽出。UI 実装者向け。
生成日: YYYY-MM-DD

## 画面: 注文入力 (UnvalidatedOrder)

対応コマンド: `PlaceOrder`
対応ワークフロー: `placeOrder: UnvalidatedOrder -> Result<PlaceOrderEvents, PlaceOrderError>`

### セクション 1: 注文基本情報

| フィールド | 型 | 必須 | 検証 | UI | glossary |
|-----------|---|----|-----|----|---------|
| orderId | string → OrderId | ✓ | `ORD-\d{3,}` | テキスト | 注文ID |
| customerEmail | string → EmailAddress | ✓ | `@` 含む | メール | 顧客メール |

### セクション 2: 配送先住所 (Address)

| フィールド | 型 | 必須 | 検証 | UI |
|-----------|---|----|-----|----|
| addressLine1 | string | ✓ | 空不可 | テキスト |
| addressLine2 | Option<string> | - | - | 展開テキスト |
| city | string | ✓ | 空不可 | テキスト |
| zipCode | string | ✓ | `\d{3}-\d{4}` | テキスト |

### セクション 3: 注文明細 (OrderLine[], NonEmptyList)

**動的リスト**: 最低 1 件、最大なし

| フィールド | 型 | 必須 | 検証 | UI |
|-----------|---|----|-----|----|
| productCode | WidgetCode \| GizmoCode | ✓ | `^[WG]\d{3,4}$` | テキスト or サジェスト |
| quantity | Unit \| Kilos | ✓ | W: 1〜1000 整数 / G: 0.05〜100 | 数値 (種別で切替) |

**依存関係**: productCode の接頭辞 (W/G) が quantity の型と検証範囲を決定。UI では productCode 確定後に quantity の入力方法を切り替える必要あり。

## 検証エラーと UI 反応のマッピング

| エラー | 表示フィールド | メッセージ |
|-------|-------------|----------|
| `ValidationError.InvalidProductCode` | 該当行の productCode | 「商品コードが無効です」 |
| `ValidationError.lines[N].quantity` | 該当明細 quantity | 「数量は 1〜1000 で入力してください」 |

## 未解決項目

- addressLine2 の表示方式 (常時表示 / クリック展開)
- productCode サジェスト用マスタ API
```

## サンプル対話 (UI 項目抽出)

```
User: /ddd simulate --ui-only

AI:   code/types/commands.ts を読みました。Unvalidated* 型が 3 つ:
      1. UnvalidatedOrder (PlaceOrder 用)
      2. UnvalidatedShipment (ShipOrder 用)
      3. UnvalidatedCancellation (CancelOrder 用)

      どれから始めますか?

User: 1

AI:   UnvalidatedOrder を展開しました。最上位 4 フィールド、
      うち 1 つ動的リスト (lines)、1 つ複合オブジェクト (shippingAddress)。

      [抽出フィールド構造を提示]

      glossary.md に orderId の表示ラベルが定義されていません。
      フォーム上の表示は?

User: 「注文番号」。customerEmail は「お客様メールアドレス」。

AI:   addressLine2 は Option<string>。フォーム上の扱いは?
      (a) 常に表示 (空欄許容)
      (b) 「建物名を追加」リンクで展開
      (c) チェックボックス切替

User: b

AI:   lines は NonEmptyList。初期に空 1 件を出しますか?

User: 出す。

AI:   productCode と quantity に状態依存があります。
      W → UnitQuantity (1〜1000 整数)、G → KilogramQuantity (0.05〜100)
      UI 実装は?
      (a) productCode 確定後に quantity を切替 (推奨)
      (b) 最初から両方表示し、種別で片方無効化

User: a

AI:   [ui-fields.md 全文を提示]
      承認すれば docs/domain/ui-fields.md に書き出します。

      抽出中の発見 (フィードバック):
      - Address の zipCode に形式制約があるはず、glossary に定義なし
      - productCode マスタ取得は商品カタログ BC から。Context Map に関係が明示されていない可能性

      対応方針は?
```

## `--challenge` モード

- 「このフォーム項目は本当に必要? デフォルト値で省けない?」
- 「必須にするとユーザビリティが落ちる。型を `Option<T>` にすべきでは?」
- 「画面が 1 ユースケースに対して複雑すぎる。ウィザード分割すべきでは?」
- 「このシナリオは設計で表現不可能。集約境界の見直しが必要では?」
- 「`NonEmptyList` の UX はどう設計する? 空の状態を見せるならそもそも型が違うのでは?」

## `--analyze` モード

1. 既存フロントエンド (React / Vue / Angular) から既存フォームを抽出
2. 生成した `ui-fields.md` と突き合わせ:
   - **Missing**: モデルにあるが UI にない
   - **Extra**: UI にあるがモデルにない (モデル化漏れの兆候)
   - **Drift**: 検証規則の不一致
3. 画面単位でリファクタリング優先度を提案

## Phase 11 固有のフラグ

| フラグ | 動作 |
|-------|-----|
| `--ui-only` | UI 項目抽出だけを実行 (シナリオ検証はスキップ) |
| `--scenario <N>` | validation.md のシナリオ N だけを型レベル検証 |
| `--analyze` | 既存フロントエンドとの差分 |
| `--challenge` | UX / 型表現の前提を疑うモード |

使用例:

```
/ddd simulate                    シナリオ検証 + UI 抽出の両方
/ddd simulate --ui-only          UI 抽出のみ
/ddd simulate --scenario 3       シナリオ 3 番だけ検証
/ddd simulate --analyze          既存フロントエンドとの差分
```

## 他フェーズへのフィードバック

Phase 11 の対話中に発見された問題は、元フェーズへの差し戻し提案として記録する。

| 発見パターン | 差し戻し先 |
|-----------|----------|
| 表示ラベルが glossary に無い | Phase 8 (glossary) |
| シナリオが型で表現不可能 | Phase 9 (workflows) / Phase 5 (aggregates) |
| 必要な検証エラーがエラーカタログに無い | Phase 9 (workflows) |
| UI 切替に必要な情報が型から取れない | Phase 10 (types) または Phase 9 (workflows) |
| Context Map に無い BC 連携が UI から必要 | Phase 4 (mapping) |
