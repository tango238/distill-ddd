# Phase 10: Types — 実装言語の型定義コード生成

## 目的

Phase 9 の `workflows.md` と既存 8 フェーズの成果物を、**コンパイル可能な型定義** に翻訳する。
DMMF (Scott Wlaschin『Domain Modeling Made Functional』Ch.4, Ch.5, Ch.6) の 3 種の型 (Simple / AND / OR) と Result / Option に固定し、情報が落ちない一対一対応を作る。

**重要な原則**: このフェーズでは **型シグネチャだけ** を出力する。関数本体は書かない。「型を先に、実装は後で」を徹底する (Phase 11 でスタブ実装を最小限作る場面を除く)。

## 翻訳規則の全体像

各マークダウンからコードへの一対一対応。

| 元アーティファクト | 元の要素 | 生成される型 |
|-----------------|---------|-----------|
| glossary.md | 制約付き値 (ProductCode = W+4 桁 等) | Simple 型 (ブランド + Smart Constructor) |
| aggregates.md | Value Object | Simple 型 or 小 AND 型 |
| aggregates.md | Root Entity + VO 集合 | AND 型 (readonly レコード) |
| aggregates.md | 状態遷移のある Entity | OR 型 (判別可能ユニオン) + 遷移関数 |
| aggregates.md | 不変条件 | Smart Constructor 内の検証 |
| **workflows.md** | **ステージ** | **中間型 (AND 型) の系列** |
| **workflows.md** | **ステップ** | **関数型シグネチャ** |
| **workflows.md** | **エラーカタログ** | **OR 型** |
| **workflows.md** | **依存** | **関数型シグネチャ (ポート)** |
| event-storming.md | Command | Command 型 |
| domain-events.md | Event | Domain Event OR 型の各要素 |
| context-map.md | BC 間契約 | DTO 型 + 変換関数シグネチャ |

## 生成ディレクトリ構成

`docs/domain/code/` 配下に次の構造で出す。

```
docs/domain/code/
├── README.md                   # マークダウン ↔ コードの対応表
├── tsconfig.json               # strict 設定
├── types/
│   ├── value-objects.ts        # Simple 型
│   ├── aggregates.ts           # AND 型 (集約)
│   ├── stages.ts               # ワークフロー中間型
│   ├── states.ts               # 状態機械の OR 型
│   ├── commands.ts             # Command
│   ├── events.ts               # Domain Event
│   ├── errors.ts               # ドメインエラー
│   ├── dtos.ts                 # BC 間連携 DTO
│   ├── ports.ts                # 依存の関数型シグネチャ
│   └── workflows.ts            # ワークフロー全体の関数型
└── util/
    ├── result.ts
    └── branded.ts
```

言語を切り替える場合 (例: kotlin) は `code/` ではなく `code-kotlin/` 等のサフィックス付きディレクトリに生成する (既存 TS 成果物と共存可能に)。

## 進行手順

### Step 1: 既存アーティファクトの読み込み

以下を順に読む。1 つでも欠けていれば、ユーザーに確認し補完のための対話を先に行う。

- `discovery.md` (背景把握)
- `event-storming.md` (Command / Event)
- `aggregates.md` (集約)
- `domain-events.md` (Event の詳細)
- `glossary.md` (制約付き値の仕様)
- `workflows.md` (Phase 9 の成果物。無ければ Phase 10 の出力は最小スケルトンになる)
- `context-map.md` (BC 間 DTO)

### Step 2: 補完質問

翻訳に必要だが文書にない情報を対話で引き出す。

質問例:
- 「ProductCode の検証ルールは `^[WG]\d{3,4}$` で合っていますか?」 (正規表現の確定)
- 「`Order` 集約は状態遷移 (Unshipped / Shipped / Cancelled) を持ちますか?」
- 「`Address` は Value Object ですか、それとも Entity として独立管理しますか?」
- 「`Money` は (amount, currency) の AND 型で作って OK ですか?」

### Step 3: 翻訳案の提示と承認

**1 ファイルずつ** 翻訳案を提示し、ユーザー承認を取る。全部まとめて提示すると見落としが出る。

推奨順:
1. `util/result.ts`, `util/branded.ts` (依存なしの基盤)
2. `types/value-objects.ts` (Simple 型、Smart Constructor)
3. `types/aggregates.ts` (AND 型)
4. `types/states.ts` (状態機械の OR 型)
5. `types/stages.ts` (ワークフロー中間型)
6. `types/commands.ts`, `events.ts` (Command / Event)
7. `types/errors.ts` (エラー OR 型)
8. `types/ports.ts` (依存の関数型)
9. `types/workflows.ts` (ワークフロー関数型)
10. `types/dtos.ts` (BC 間 DTO)

### Step 4: code/README.md の対応表を確定

各型がどのマークダウンの何セクションから来たかを表で固定する。マークダウンが更新された際に何を再生成すべきか分かるようにする。

### Step 5: 型チェック確認

生成完了後、対応言語のコンパイラ/型チェッカーで warning なしに通ることを確認する。

| 言語 | コマンド |
|------|---------|
| typescript | `tsc --noEmit` |
| kotlin | `kotlinc -script` または gradle build |
| scala | `scala compile` |
| rust | `cargo check` |
| csharp | `dotnet build --no-restore` |
| fsharp | `dotnet fsi --noninteractive` |

### Step 6: 未翻訳セクションの列挙

翻訳できなかった (情報不足、型で表現困難など) 要素を `code/README.md` の「未翻訳」セクションに列挙し、元フェーズへの差し戻し提案を添える。

## `--challenge` モード

- 「この `string` 型は本当に制約なしか? Simple 型にすべきでは?」
- 「この `bool` フラグは OR 型に分解できないか? (`Active | Inactive` のような)」
- 「この `Option<Foo>` は状態ごとに別型にすべきでは? (UnsubmittedDraft / SubmittedDraft)」
- 「例外を投げる操作はないか? Result で表現すべきでは?」
- 「全域関数として書けるか? 部分関数になっていないか?」
- 「この AND 型は本当に 1 つの概念か? 分解したほうが表現力が高まらないか?」

## `--analyze` モード

1. `src/**/domain/**` および `src/**/models/**` から既存型定義を探索
2. 生成予定の型との差分を分類:
   - **Missing**: モデルにあるが実装にない
   - **Extra**: 実装にあるがモデルにない (モデル化漏れの兆候)
   - **Drift**: 制約・名前の食い違い
3. リファクタリング提案を優先度付きで提示

## 対応言語

初期サポート (段階展開)。

| 言語 | 型表現 | Result 実装 | ブランド型 |
|------|-------|-----------|-----------|
| typescript (既定) | object literal + discriminated union | neverthrow | `{ readonly __brand: unique symbol }` |
| kotlin | sealed class + data class + inline class | Arrow Either | inline class |
| scala | Scala 3 enum + opaque type | Cats Validated | opaque type |
| rust | enum + struct + newtype | 標準 Result | newtype pattern |
| csharp | record + OneOf | LanguageExt Either | wrapper record |
| fsharp | discriminated union + record | 標準 Result | single-case DU |

TS を最初に完全実装。他言語は最小テンプレートから始め、要望ベースで補充。

## 成果物テンプレート

### `code/README.md`

```markdown
# Code ↔ Domain Model Mapping

このディレクトリのコードは `docs/domain/*.md` から自動翻訳されています。
マークダウン更新後は `/ddd types --regenerate` で再生成してください。

## 対応表

| コード | 由来 | セクション |
|------|-----|----------|
| `types/value-objects.ts` の `ProductCode` | glossary.md | 「ProductCode」 |
| `types/aggregates.ts` の `Order` | aggregates.md | 「Order 集約」 |
| `types/stages.ts` の `ValidatedOrder` | workflows.md | Workflow 1 Step 1 |
| `types/workflows.ts` の `PlaceOrder` | workflows.md | Workflow 1 |
| `types/ports.ts` の `CheckProductCodeExists` | workflows.md | Workflow 1 依存 |

## 未翻訳の要素

- `ShippingZone` (glossary に記載なし、Phase 8 差し戻し)
- `CancellationPolicy` (aggregates に記載なし、Phase 5 差し戻し)
```

### 翻訳サンプル (TypeScript)

```typescript
// types/value-objects.ts
import { Result, ok, err } from "../util/result";

// Brand 型による Simple 型
export type ProductCode = string & { readonly __brand: "ProductCode" };

export const ProductCode = {
  create: (input: string): Result<ProductCode, "InvalidProductCode"> => {
    if (!/^[WG]\d{3,4}$/.test(input)) return err("InvalidProductCode");
    return ok(input as ProductCode);
  },
};

// types/stages.ts
import type { ProductCode } from "./value-objects";

export type UnvalidatedOrder = {
  readonly kind: "Unvalidated";
  readonly orderId: string;
  readonly customerEmail: string;
  readonly lines: ReadonlyArray<{ productCode: string; quantity: number }>;
};

export type ValidatedOrder = {
  readonly kind: "Validated";
  readonly orderId: string;
  readonly customerEmail: EmailAddress;
  readonly lines: ReadonlyArray<{ productCode: ProductCode; quantity: number }>;
};

// types/errors.ts
export type PlaceOrderError =
  | { kind: "Validation"; detail: ValidationError }
  | { kind: "Pricing"; detail: PricingError };

export type ValidationError =
  | { kind: "InvalidProductCode"; code: string }
  | { kind: "AddressNotFound"; address: string }
  | { kind: "InvalidEmail" };

// types/ports.ts
export type CheckProductCodeExists = (code: ProductCode) => Promise<boolean>;
export type GetProductPrice = (code: ProductCode) => Promise<Price>;

// types/workflows.ts
import type { UnvalidatedOrder } from "./stages";
import type { PlaceOrderEvents } from "./events";
import type { PlaceOrderError } from "./errors";
import type { CheckProductCodeExists, GetProductPrice } from "./ports";

export type PlaceOrderDeps = {
  checkProductCodeExists: CheckProductCodeExists;
  getProductPrice: GetProductPrice;
};

export type PlaceOrder =
  (deps: PlaceOrderDeps) =>
  (input: UnvalidatedOrder) =>
  Promise<Result<PlaceOrderEvents, PlaceOrderError>>;
```

## Phase 10 固有のフラグ

| フラグ | 動作 |
|-------|-----|
| `--lang <lang>` | 対象言語を指定 (typescript / kotlin / scala / rust / csharp / fsharp)。既定は typescript |
| `--regenerate` | 既存 `code/` を対応表に従って再生成 (ユーザー承認後) |
| `--analyze` | 既存コードとの差分を分類 (Missing / Extra / Drift) |
| `--challenge` | プリミティブ偏重などの批判モード |

使用例:

```
/ddd types                   TypeScript で新規生成
/ddd types --lang kotlin     Kotlin で新規生成 (code-kotlin/ へ)
/ddd types --regenerate      マークダウン更新を反映して再生成
/ddd types --analyze         既存コードとの差分
```
