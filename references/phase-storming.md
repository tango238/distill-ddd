# Phase 2: Event Storming — イベント駆動モデリング

## 目的

Alberto Brandolini の Event Storming 手法を対話で実施。
ビジネスプロセスをイベント中心に洗い出し、Commands と Aggregates を特定する。

## 進行手順 (DDD Distilled Ch.7)

### Step 1: Domain Events を洗い出す

質問:
- 「このビジネスで時系列に何が起きますか? "〜された" という過去形で教えてください」
- 「ユーザーがシステムを使い始めてから完了するまでの流れは?」
- 「例外的なケースやエラーが発生するのはどんなとき?」

ガイドライン:
- 名前は過去分詞: `BookingCreated`, `PaymentReceived`, `OrderCanceled`
- 時系列に左→右で並べる
- 並行処理は縦に配置
- 問題点やリスクは赤で注記
- 粗くてよい。数を出すことが重要

出力形式:
```
Timeline:
1. UserRegistered
2. PropertyCreated
3. RoomTypeConfigured
4. BookingCreated
5. AutoMailScheduled
   ...
```

### Step 2: Commands を特定する

質問:
- 「各イベントを引き起こすアクション (操作) は何ですか?」
- 「誰がそのアクションを実行しますか? (ロール)」

ガイドライン:
- Command は命令形: `CreateBooking`, `CancelOrder`, `ApprovePayment`
- Command/Event ペアで表示
- 時間経過やタイマーで発生するイベントは Command なし
- ロール (Actor) も記録

出力形式:
```
| Actor | Command | → Event |
|-------|---------|---------|
| Staff | CreateBooking | BookingCreated |
| System | ScheduleAutoMail | AutoMailScheduled |
| Guest | SubmitCheckIn | CheckInCompleted |
```

### Step 3: Aggregates を仮特定する

質問:
- 「このコマンドはどのデータ (もの) に対して実行されますか?」
- 「その "もの" の名前は何ですか?」

ガイドライン:
- Aggregate は名詞: `Booking`, `Property`, `AutoMailConfiguration`
- 同じ Aggregate が複数の Command/Event ペアに登場するのは正常
- Command/Event ペアの上に Aggregate 名を配置

### Step 4: 境界の発見

質問:
- 「同じ言葉が部門や文脈で別の意味を持つ箇所はありますか?」
- 「明らかに別の関心事のグループはどこですか?」
- 「ここからここまでは一つの "世界" と言えるグループ分けは?」

→ Bounded Context 候補をピンクの付箋で囲む (次フェーズへの橋渡し)

## --analyze 時の追加手順

1. プロジェクトの既存ドメインモデルからイベント・コマンド・集約を推測
2. 「コードから以下のイベント的な操作を検出しました: ...」と提示
3. 不足やズレを指摘

## 成果物テンプレート

```markdown
# Event Storming

## Domain Events (時系列)

### {Bounded Context 候補名}
1. {EventName} — {説明}
2. ...

## Command / Event マトリクス

| Actor | Command | Aggregate | Event | 備考 |
|-------|---------|-----------|-------|------|
| ... | ... | ... | ... | ... |

## 発見された問題点
- {赤付箋: 問題の説明}

## Bounded Context 候補
- {候補名}: {含まれるイベント群}

## 未解決の問い
- ...
```
