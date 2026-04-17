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
