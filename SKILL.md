---
name: ddd
description: >
  Interactive Domain-Driven Design modeling sessions based on DDD Distilled (Vaughn Vernon)
  and Domain Modeling Made Functional (Scott Wlaschin). Guides users through strategic and
  tactical design via 9 phases: discover, storming, contexts, mapping, aggregates, events,
  validate, glossary, workflows. Each phase is an interactive dialogue where AI acts as
  facilitator and domain expert challenger. Use when: "DDD", "ドメイン設計", "ドメインモデリング",
  "Event Storming", "Bounded Context", "集約設計", "ユビキタス言語", "コンテキストマップ",
  "ワークフロー設計", "パイプライン設計", "ステップ分割", "中間型", "型駆動フロー",
  "/ddd", "ドメイン分析したい", "モデリングしたい", or any domain design activity.
---

# /ddd — Interactive Domain-Driven Design

AI がドメインエキスパート兼ファシリテーターとして DDD モデリングをガイドする対話型スキル。

## Invocation

```
/ddd                          Phase selection menu
/ddd <phase>                  Jump to specific phase
/ddd <phase> --analyze        Compare model against existing codebase
/ddd <phase> --challenge      Adversarial mode: question every assumption
/ddd --resume                 Resume from last session state
/ddd --status                 Show progress across all phases
```

## Phases

| # | Phase | Purpose | Artifact |
|---|-------|---------|----------|
| 1 | `discover` | Identify Core Domain, business drivers, problem space | `discovery.md` |
| 2 | `storming` | Event Storming: Events → Commands → Aggregates | `event-storming.md` |
| 3 | `contexts` | Define Bounded Contexts and Subdomains | `bounded-contexts.md` |
| 4 | `mapping` | Draw Context Map with inter-context relationships | `context-map.md` |
| 5 | `aggregates` | Design Aggregates using 4 rules of thumb | `aggregates.md` |
| 6 | `events` | Design Domain Events: naming, properties, causality | `domain-events.md` |
| 7 | `validate` | Validate model with use cases, scenarios, and UI walkthroughs | `validation.md` |
| 8 | `glossary` | Compile and refine Ubiquitous Language | `glossary.md` |
| 9 | `workflows` | Design workflow pipelines: stages, steps, dependencies, errors, side-effects | `workflows.md` |

Phases can run in any order. Recommended flow: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9.

## Interaction Rules

### Facilitator Mode (default)

1. Ask 1-2 focused questions per turn. Never dump a wall of questions.
2. After each answer, synthesize into a model fragment and present it.
3. Ask "Does this capture your intent? What's missing or wrong?"
4. When the user confirms, append to the phase artifact.
5. Periodically summarize progress and suggest what to explore next.

### Challenge Mode (`--challenge`)

Same as Facilitator, but after each model fragment:
1. Present 2-3 counter-arguments or alternative interpretations.
2. Ask "Is X really part of this context, or does it belong elsewhere?"
3. Test assumptions: "What if the same term means something different in department Y?"
4. Push until the user defends or revises the design.

### Analyze Mode (`--analyze`)

1. Read the project's domain model code (find `**/domain/**/*.kt`, `**/domain/**/*.java`, `**/domain/**/*.ts` etc.).
2. Compare discovered model against the current phase's design.
3. Highlight: matches, gaps, violations of DDD principles, naming mismatches.
4. Suggest concrete refactoring opportunities.

## Session State

State file: `docs/domain/.ddd-session.json`

```json
{
  "currentPhase": "storming",
  "completedPhases": ["discover"],
  "lastUpdated": "2026-04-14",
  "openQuestions": ["Is CheckIn a separate Bounded Context or part of Booking?"]
}
```

On `--resume`: read state file, show summary of where we left off, continue.
On phase completion: update state, show checklist score.

## Artifact Location

All artifacts saved to `docs/domain/` in the project root. Create the directory if it doesn't exist.
If artifacts already exist, read them first and build upon them — never overwrite without confirmation.

## Phase Details

Each phase has a detailed reference file. Read the appropriate file when entering a phase:

- **discover**: Read [references/phase-discover.md](references/phase-discover.md)
- **storming**: Read [references/phase-storming.md](references/phase-storming.md)
- **contexts**: Read [references/phase-contexts.md](references/phase-contexts.md)
- **mapping**: Read [references/phase-mapping.md](references/phase-mapping.md)
- **aggregates**: Read [references/phase-aggregates.md](references/phase-aggregates.md)
- **events**: Read [references/phase-events.md](references/phase-events.md)
- **validate**: Read [references/phase-validate.md](references/phase-validate.md)
- **glossary**: Read [references/phase-glossary.md](references/phase-glossary.md)
- **workflows**: Read [references/phase-workflows.md](references/phase-workflows.md)

## Entry Point Behavior

When `/ddd` is invoked without arguments:

1. Check for `docs/domain/.ddd-session.json` — if exists, offer to resume.
2. Otherwise, show the phase table and ask: 「どのフェーズから始めますか？初めてなら `discover` を推奨します。」
3. If the project has existing domain docs (`docs/domain/*.md`), acknowledge them and ask whether to build upon or start fresh.

## Quality Checklist (shown at phase completion)

For each phase, present a self-assessment checklist. See [references/checklists.md](references/checklists.md).

## Language

Conduct sessions in the same language the user uses. Default to Japanese if the project context is Japanese.
