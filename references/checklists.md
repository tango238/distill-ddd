# Phase Completion Checklists

各フェーズ完了時にユーザーに提示する自己評価チェックリスト。

## Phase 1: Discover

- [ ] Core Domain を1つ特定し、なぜ Core かを説明できる
- [ ] Supporting / Generic Subdomain を少なくとも1つずつ特定した
- [ ] ビジネスの競争優位が Core Domain に反映されている
- [ ] 未解決の問いをリストアップした

## Phase 2: Event Storming

- [ ] 主要なビジネスプロセスのイベントを時系列で洗い出した
- [ ] 各イベントに対応する Command を特定した
- [ ] 各 Command/Event ペアに Aggregate を紐づけた
- [ ] 問題点 (赤付箋) を記録した
- [ ] Bounded Context の境界候補を仮特定した

## Phase 3: Bounded Contexts

- [ ] 各 Bounded Context に名前と責務を定義した
- [ ] 同じ用語が異なる意味を持つ箇所を特定し、分離した
- [ ] 各コンテキストを Core / Supporting / Generic に分類した
- [ ] 1 BC = 1 Subdomain の原則を意識した (例外は理由を記録)
- [ ] 各コンテキストのユビキタス言語の範囲を明確にした

## Phase 4: Context Mapping

- [ ] 全 Bounded Context 間の依存関係を特定した
- [ ] 各関係の種類 (Partnership, Customer-Supplier 等) を決定した
- [ ] 統合方式 (REST, Messaging 等) を決定した
- [ ] ACL が必要な箇所を特定した
- [ ] Context Map を図として描いた

## Phase 5: Aggregates

- [ ] 各 Aggregate の Root Entity を特定した
- [ ] Rule 1: ビジネス不変条件を Aggregate 内で保護している
- [ ] Rule 2: Aggregate が小さく保たれている (巨大な Aggregate がない)
- [ ] Rule 3: 他の Aggregate は ID のみで参照している
- [ ] Rule 4: 他の Aggregate は結果整合性で更新している (or 理由付きで例外)
- [ ] Anemic Domain Model になっていない (振る舞いが Aggregate 内にある)

## Phase 6: Domain Events

- [ ] 全ての Domain Event が過去形で命名されている
- [ ] 各イベントのプロパティが定義されている
- [ ] occurredOn (発生日時) が含まれている
- [ ] Enrichment vs Query-Back の判断をイベントごとに行った
- [ ] コンテキスト間の Event Flow を描いた
- [ ] Event Sourcing の採用/不採用を検討した

## Phase 7: Validate

- [ ] Core Domain の主要ユースケースを少なくとも3つ検証した
- [ ] 各シナリオが Command → Aggregate → Event にマッピングできた
- [ ] 複数 Aggregate を横断するシナリオで整合性の問題がないか確認した
- [ ] 異常系・エッジケースを少なくとも各シナリオ1つ検証した
- [ ] UI ウォークスルーで必要なデータが取得可能か確認した (画面がある場合)
- [ ] 発見された問題を対応するフェーズにフィードバックした
- [ ] Given/When/Then 形式で少なくとも1つ実行可能な仕様を書いた (任意)

## Phase 8: Glossary

- [ ] 全 Bounded Context の用語を収集した
- [ ] 各用語に明確な定義がある
- [ ] 同じ用語が異なる意味を持つケースを記録した
- [ ] コード上の命名と一致している (or 不一致を記録)

## Phase 9: Workflows

- [ ] 実装対象ワークフローを優先度付きで絞り込んだ
- [ ] 各ワークフローのステージ(中間型系列)を命名・定義した
- [ ] 各ステップの入力型・出力型・エラー・依存・副作用を表にした
- [ ] 依存(ポート)を型シグネチャ付きで一覧化した
- [ ] エラー型を OR 型として整理した
- [ ] イベント発行タイミングを各ステップで特定した
- [ ] 副作用が境界(最初と最後)に寄っているか確認した
- [ ] ワークフロー間の関係(Event 駆動 / orchestration) を整理した
- [ ] 発見された問題を元フェーズ (aggregates / events / glossary 等) にフィードバックとして記録した

## Phase 10: Types

- [ ] Aggregate Root が AND 型として出力されている
- [ ] Value Object が Simple 型 (ブランド型) として出力されている
- [ ] 状態遷移を持つ Entity が OR 型で表現されている
- [ ] 各 Simple 型に Smart Constructor がある
- [ ] ステージ型 (UnvalidatedX / ValidatedX 等) が workflows.md と一致している
- [ ] すべての Command に対応する Workflow 関数型がある
- [ ] すべての Event が Domain Event の OR 型に含まれる
- [ ] エラー型が OR 型として階層化されている
- [ ] ポート (依存) が関数型で定義されている
- [ ] `code/README.md` の対応表が完成している
- [ ] `tsc --noEmit` (または対応言語のチェッカー) が警告なしで通る
- [ ] 未翻訳セクションが `code/README.md` に列挙されている

## Phase 11: Simulate

- [ ] validation.md の全シナリオに対応する型レベルテストがある (ワークフロー検証時)
- [ ] 全 `Unvalidated*` 型から UI 項目が抽出されている
- [ ] `ui-fields.md` の各項目が glossary と対応づいている
- [ ] 検証エラーと UI フィールドのマッピングがある
- [ ] 状態依存フィールド (productCode → quantity 等) が明示されている
- [ ] `Option<T>` と `NonEmptyList` の UI 扱いが決定されている
- [ ] シナリオ検証で発見された問題が他フェーズにフィードバックされている
