# Phase 4: Mapping — Context Map の作成

## 目的

Bounded Context 間の関係 (チーム間関係 + 技術的統合) を Context Map として定義する。

## 関係の種類 (DDD Distilled Ch.4)

| 関係 | 説明 | 線の表記 |
|------|------|---------|
| **Partnership** | 2チームが成功/失敗を共有。密な同期 | 太線 |
| **Shared Kernel** | 小さな共通モデルを共有 | 斜線の交差 |
| **Customer-Supplier** | Upstream (U) が供給、Downstream (D) が消費 | U → D |
| **Conformist** | Downstream が Upstream に従属 | U → D (ACL なし) |
| **Anticorruption Layer** | Downstream が翻訳層で隔離 | ACL マーク |
| **Open Host Service** | Upstream が公開 API を提供 | OHS マーク |
| **Published Language** | 共有スキーマ (JSON/Protobuf 等) | PL マーク |
| **Separate Ways** | 統合しない。独自実装 | X マーク |
| **Big Ball of Mud** | 境界なし。避けるべき | オレンジ楕円 |

## 進行手順

### Step 1: 依存関係の洗い出し

各 Bounded Context ペアについて:
- 「Context A は Context B のデータを必要としますか?」
- 「どちらが "上流" (データの源泉) で、どちらが "下流" (消費者) ですか?」
- 「リアルタイムで必要ですか? 遅延しても問題ないですか?」

### Step 2: 関係タイプの決定

各依存関係について:
- 「両チームは対等ですか? → Partnership」
- 「上流チームは下流の要望に応えてくれますか? → Customer-Supplier」
- 「上流チームは協力してくれず従うしかない? → Conformist」
- 「上流の変更から自分を守りたい? → Anticorruption Layer」
- 「公開 API として提供する? → Open Host Service + Published Language」

### Step 3: 統合方式の決定

| 方式 | 堅牢性 | 結合度 | ユースケース |
|------|--------|--------|-----------|
| RPC/SOAP | 低 | 高 | レガシー統合 |
| RESTful HTTP | 中 | 中 | 公開 API |
| Messaging (非同期) | 高 | 低 | Domain Event 駆動 |

Domain Event による非同期メッセージングが最も推奨。

### Step 4: Context Map 図の作成

ASCII or Mermaid で図を描く。

## 成果物テンプレート

```markdown
# Context Map

## 図

{ASCII or Mermaid}

## 関係一覧

| Upstream | Downstream | 関係 | 統合方式 | 備考 |
|----------|-----------|------|---------|------|
| {Context A} | {Context B} | Customer-Supplier | REST + ACL | ... |
| ... | ... | ... | ... | ... |

## 統合の詳細

### {Context A} → {Context B}
- **関係**: {タイプ}
- **流れるデータ**: {Domain Event 名 or API リソース}
- **統合方式**: {REST / Messaging / Shared Kernel}
- **ACL の有無**: {あり/なし、理由}

## 未解決の問い
- ...
```
