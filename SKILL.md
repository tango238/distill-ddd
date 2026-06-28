---
name: ddd
description: >
  Interactive Domain-Driven Design modeling sessions based on DDD Distilled (Vaughn Vernon)
  and Domain Modeling Made Functional (Scott Wlaschin). Guides users through strategic and
  tactical design via 13 phases: discover, storming, contexts, mapping, aggregates, events,
  validate, glossary, workflows, types, simulate, publish, sync. Phase 13 (sync) reconciles
  divergences found by --analyze between the domain model and the implementation — judging whether
  the model or the code is authoritative, then planning and implementing the fix and re-aligning the
  model. Phases 9-11 take the conceptual model
  from phases 1-8 and produce workflow pipeline designs, compilable type definitions (TypeScript,
  Kotlin, Scala, Rust, C#, F#), workflow verification via type-level tests, and automatic
  UI field enumeration from the domain model. Phase 12 (publish) renders all docs/domain
  artifacts into one self-contained, cross-linked HTML site (separate files joined by a shared
  nav). Each phase is an interactive dialogue where AI acts as facilitator and domain expert
  challenger.
  Use when: "DDD", "ドメイン設計", "ドメインモデリング", "Event Storming", "Bounded Context",
  "集約設計", "ユビキタス言語", "コンテキストマップ", "ワークフロー設計", "パイプライン設計",
  "ステップ分割", "中間型", "型駆動フロー", "型駆動設計", "Domain Modeling Made Functional",
  "Railway Oriented Programming", "入力画面項目", "フォーム項目洗い出し", "UI 項目抽出",
  "HTMLにまとめる", "ドキュメントサイト化", "成果物を1つのHTMLに", "publish",
  "モデルと実装の差異", "差異解消", "実装との乖離", "モデルとコードを一致", "差異の実装計画", "sync",
  "複数フェーズを逐次実行", "フェーズをまとめて実行", "/ddd run", "サブコマンド一覧", "/ddd list",
  "/ddd", "ドメイン分析したい", "モデリングしたい", or any domain design / type modeling activity.
---

# /ddd — Interactive Domain-Driven Design

AI がドメインエキスパート兼ファシリテーターとして DDD モデリングをガイドする対話型スキル。

## Invocation

```
/ddd                          Phase selection menu
/ddd <phase>                  Jump to specific phase
/ddd <phase> --analyze        Compare model against existing codebase
/ddd <phase> --challenge      Adversarial mode: question every assumption
/ddd run <p1, p2 --flag, ...> Run several phases in sequence (each with its own flags)
/ddd run <...> --auto         Same, but auto-advance between phases (skip the checkpoint)
/ddd sync                     Reconcile model⇔implementation divergences: plan & implement
/ddd list                     List all phases, flags, and commands (aliases: help, ?)
/ddd --resume                 Resume from last session state (incl. an in-progress run queue)
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
| 10 | `types` | Translate the domain model into compilable type definitions | `code/types/*.ts` |
| 11 | `simulate` | Type-level workflow verification and UI field enumeration | `code/simulations/`, `ui-fields.md` |
| 12 | `publish` | Render all artifacts into one cross-linked HTML site (shared nav) | `docs/domain/*.html` |
| 13 | `sync` | Reconcile model⇔implementation divergences found by `--analyze`: judge authority, plan, implement, re-align the model | `sync.md` |

Phases can run in any order. Recommended flow: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12.
`publish` is typically run last (or any time) to turn the accumulated `docs/domain/*.md` into a
navigable HTML site — "one HTML, files separate but linked".
`sync` is run whenever a `--analyze` pass surfaces divergences between the model and the code: it
takes those gaps, decides whether the model or the code is authoritative, then plans and implements
the fix (and updates the model docs) — keeping the two in step.

## Sequential Runner (`/ddd run`)

Run several phases back-to-back without retyping `/ddd` each time.

```
/ddd run discover, storming --challenge, contexts, mapping --analyze
/ddd run discover, storming, contexts --auto
```

**Syntax**: a comma-separated list. Each item is a phase name followed by its own optional flags
(`--analyze` / `--challenge`). A trailing `--auto` applies to the whole run.

**Behavior**:

1. **Parse** the list into a queue. Validate each phase name against the [Phases](#phases) table
   (accept the obvious alias `discovery` → `discover`). If an item is unknown, show the closest
   match and ask before continuing — never silently skip or guess.
2. **Persist** the queue to `docs/domain/.ddd-session.json` (`queue`, `queueIndex`, `queueAuto`) so
   `/ddd --resume` can pick a halted run back up.
3. For each queued phase, in order:
   - Announce `▶ [i/N] <phase> <flags>` and read `references/phase-<phase>.md`.
   - Run that phase as a normal interactive dialogue, honoring its flags and all Interaction Rules.
   - On completion, update `completedPhases`, advance `queueIndex`, and show the phase checklist.
   - **Checkpoint** (default): show `✓ <phase> 完了 — 次は <next> です。続けますか？（続行 / skip / stop）`
     and wait for the user. With `--auto`, skip this checkpoint and proceed immediately.
4. **End of queue** → summarize what was completed and which artifacts changed.

**`--auto` only removes the *between-phase* checkpoint.** In-phase approval gates still stop and
ask — e.g. `sync`'s destructive-op / architecture-fork gates (Interaction Rules → Sync Mode), or any
moment a contradiction overturns the user's assumption. Never auto-confirm those.

**Steering**: at any checkpoint the user can say `stop` (halt, keep all progress), `skip` (drop the
current phase and go to the next), or jump to any phase. A halted run resumes with `/ddd --resume`.

**Missing prerequisites**: phases may run in any order, but if a queued phase reads artifacts that
don't exist yet (e.g. `aggregates` before `storming`), note it and ask whether to proceed or reorder
rather than producing a thin artifact.

## Command List (`/ddd list`)

`/ddd list` (aliases `/ddd help`, `/ddd ?`) prints a quick reference and runs **no** phase:

- **Phases** — the 13-row [table](#phases) (#, phase, purpose, artifact).
- **Flags** — `--analyze` (compare to code), `--challenge` (adversarial), `--auto` (run:
  auto-advance between phases).
- **Commands** — `/ddd <phase>`, `/ddd run <list>`, `/ddd sync`, `/ddd --resume`, `/ddd --status`,
  `/ddd list`.
- **Recommended flow** — discover → storming → contexts → mapping → aggregates → events → validate →
  glossary → workflows → types → simulate → publish (→ `sync` whenever `--analyze` finds divergences).

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
5. If divergences are found, point the user to the `sync` phase, which plans and implements the fix
   (or updates the model) rather than leaving the gap as a note.

### Sync Mode (`sync`)

Resolve model⇔implementation divergences surfaced by `--analyze`. Unlike the conceptual phases,
`sync` writes code, so it follows an engineering discipline (plan → approve → implement). See
[references/phase-sync.md](references/phase-sync.md) for the full loop. Key rules:

1. **Divergences are bidirectional** — for each one, decide whether the *model* or the *code* is
   authoritative (or both converge). Fix code for model-authoritative gaps; update `docs/domain` for
   code-authoritative ones.
2. **Never silently accept contradictions** — when reading the code overturns the user's assumption,
   surface it before reordering or implementing.
3. **Approval gate** — present options for architecture forks / destructive ops before implementing.
4. **TDD + honest reporting** — run the project's tests/lint/build; state failures, skips, and
   out-of-scope work plainly.
5. **Keep model and code in step** — when code change closes a gap, update the corresponding red
   sticky / open question in `docs/domain/*.md` in the same pass.
6. **Commit only when asked**; if on the default branch, branch first; split into logical commits.

### Type-Driven Mode (Phase 9, 10, 11)

Phases 9-11 follow DMMF principles in addition to the above interaction rules.

1. Phase 9 writes type-driven design drafts in Markdown. Do NOT generate code yet.
2. Phase 10 outputs only type definitions; function bodies are not written (DMMF principle: "types first, functions later").
3. After any code generation, verify it compiles with `tsc --noEmit` (or the target language's checker) before claiming completion.
4. Prioritize "make illegal states unrepresentable" — never use primitive types directly, always route through Simple (branded) types with Smart Constructors.
5. Errors are returned as `Result<Ok, Err>`; exceptions are reserved for genuinely unrecoverable system failures.
6. Dependencies are passed as function arguments. Do NOT assume a DI container.
7. When Phase 9 reveals gaps in aggregates/events/glossary, record them in the workflows.md "フィードバック" section and suggest a return trip to the affected phase rather than silently patching.

## Session State

State file: `docs/domain/.ddd-session.json`

```json
{
  "currentPhase": "storming",
  "completedPhases": ["discover"],
  "lastUpdated": "2026-04-14",
  "openQuestions": ["Is CheckIn a separate Bounded Context or part of Booking?"],
  "queue": [
    { "phase": "storming", "flags": ["--challenge"] },
    { "phase": "contexts", "flags": [] }
  ],
  "queueIndex": 0,
  "queueAuto": false,
  "divergences": [
    { "id": 1, "fromPhase": "storming", "type": "gap", "authority": "model", "decision": "...", "status": "done", "commit": "2773a1f" }
  ]
}
```

`queue` / `queueIndex` / `queueAuto` are written by `/ddd run` so a halted sequence can resume.
`queueIndex` points at the phase currently in progress; an empty/absent `queue` means no run is active.

`divergences[]` is the structured ledger maintained by the `sync` phase (see
[references/phase-sync.md](references/phase-sync.md)). `status` ∈ `pending | planned | in-progress |
done | model-updated | deferred`; `authority` ∈ `model | code | converge`.

On `--resume`: read state file, show summary of where we left off, continue. If `queue` has
remaining phases, resume the run at `queueIndex` (honoring `queueAuto`).
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
- **types**: Read [references/phase-types.md](references/phase-types.md)
- **simulate**: Read [references/phase-simulate.md](references/phase-simulate.md)
- **publish**: Read [references/phase-publish.md](references/phase-publish.md)
- **sync**: Read [references/phase-sync.md](references/phase-sync.md)

## Site Publishing (`/ddd publish`)

To bundle the investigated domain model into one cross-linked HTML site, run the bundled
generator (Python 3 stdlib only — no pip, no CDN, works offline):

```
python3 <SKILL_DIR>/scripts/build_site.py docs/domain
```

`<SKILL_DIR>` is this skill's install dir (`~/.claude/skills/ddd`, `~/.codex/skills/ddd`, or
`~/.gemini/skills/ddd`). It converts every `docs/domain/*.md` into `*.html`, wiring them with a
shared sticky nav (current page highlighted) and rewriting intra-doc `.md` links to `.html`.
See [references/phase-publish.md](references/phase-publish.md) for ASCII→SVG diagram tips and the
optional `docs/domain/_site.json` (nav order/labels). The script is idempotent — rerun after edits.

## Intent Export (`emit_intent.py`)

distill-ddd owns *intent* — "what we meant to build". Downstream tools (e.g. crawl-kit's
verification layer) need that intent as data, not prose. Export a contract-shaped `intent.json`
("emit at the source"; Python 3 stdlib only):

```
python3 <SKILL_DIR>/scripts/emit_intent.py docs/domain      # → docs/domain/intent.json
```

It reads the human artifacts and emits the two axes that diff mechanically — **events** (from
`domain-events.md`) and **state transitions** (from each aggregate's `**状態遷移**:` block in
`aggregates.md`) — plus a thin concept list (aliases enriched from `glossary.md`) for canonical-id
seeding. The shape is a superset of the legacy glossary fixture, so existing consumers keep working.

State transitions are **decided interactively during the `aggregates` phase**, not guessed from
prose — see [references/phase-aggregates.md](references/phase-aggregates.md) (Step 3.5). Keep the
canonical line shape `- {from} → {to} : \`{trigger}\` → \`{event}\`` so the exporter reads it
deterministically; mark stateless aggregates `**状態遷移**: なし`. Re-run after editing the model.

## Entry Point Behavior

When `/ddd` is invoked without arguments:

1. Check for `docs/domain/.ddd-session.json` — if exists, offer to resume.
2. Otherwise, show the phase table and ask: 「どのフェーズから始めますか？初めてなら `discover` を推奨します。」
   Mention that `/ddd run discover, storming, …` chains several phases, and `/ddd list` shows the full command reference.
3. If the project has existing domain docs (`docs/domain/*.md`), acknowledge them and ask whether to build upon or start fresh.

## Quality Checklist (shown at phase completion)

For each phase, present a self-assessment checklist. See [references/checklists.md](references/checklists.md).

## Language

Conduct sessions in the same language the user uses. Default to Japanese if the project context is Japanese.
