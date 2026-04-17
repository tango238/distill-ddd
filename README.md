# distill-ddd

Interactive Domain-Driven Design modeling skill based on *DDD Distilled* (Vaughn Vernon).
Works with **Claude Code**, **Codex CLI**, and **Gemini CLI** on **macOS**, **Linux**, and **Windows**.

The skill guides you through eight phases — discover, storming, contexts, mapping, aggregates, events, validate, glossary — as an interactive dialogue where the AI plays facilitator and domain-expert challenger.

## Install

### macOS / Linux

```sh
git clone https://github.com/tango238/distill-ddd.git
cd distill-ddd
./install.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/tango238/distill-ddd.git
cd distill-ddd
.\install.ps1
```

By default the skill is installed for every supported CLI. To target just one, pass a flag:

| CLI | bash | PowerShell |
|---|---|---|
| Claude Code | `./install.sh --claude` | `.\install.ps1 -Claude` |
| Codex CLI   | `./install.sh --codex`  | `.\install.ps1 -Codex` |
| Gemini CLI  | `./install.sh --gemini` | `.\install.ps1 -Gemini` |

To uninstall:

```sh
./install.sh --uninstall        # macOS / Linux
.\install.ps1 -Uninstall        # Windows
```

### Install locations

Each CLI gets a skill body (SKILL.md + references) plus the native entry point that enables `/ddd`.

| CLI | Skill body | Entry point (`/ddd`) |
|---|---|---|
| Claude Code | `~/.claude/skills/ddd/` | same (auto-discovered) |
| Codex CLI   | `~/.codex/skills/ddd/`  | `~/.codex/prompts/ddd.md` |
| Gemini CLI  | `~/.gemini/skills/ddd/` | `~/.gemini/commands/ddd.toml` |

Windows paths are the same under `%USERPROFILE%` (e.g. `%USERPROFILE%\.codex\prompts\ddd.md`).

## Usage

Invoke with `/ddd` in any of the three CLIs:

```
/ddd                 Phase selection menu
/ddd <phase>         Jump to a phase (discover, storming, contexts, ...)
/ddd <phase> --analyze     Compare model against existing codebase
/ddd <phase> --challenge   Adversarial mode: question every assumption
/ddd --resume        Resume from last session state
/ddd --status        Show progress across all phases
```

## Phases

| # | Phase | Purpose | Artifact |
|---|-------|---------|----------|
| 1 | `discover` | Identify Core Domain, business drivers, problem space | `discovery.md` |
| 2 | `storming` | Event Storming: Events -> Commands -> Aggregates | `event-storming.md` |
| 3 | `contexts` | Define Bounded Contexts and Subdomains | `bounded-contexts.md` |
| 4 | `mapping` | Draw Context Map with inter-context relationships | `context-map.md` |
| 5 | `aggregates` | Design Aggregates using 4 rules of thumb | `aggregates.md` |
| 6 | `events` | Design Domain Events: naming, properties, causality | `domain-events.md` |
| 7 | `validate` | Validate model with use cases, scenarios, UI walkthroughs | `validation.md` |
| 8 | `glossary` | Compile and refine Ubiquitous Language | `glossary.md` |

Artifacts are written to `docs/domain/` in the project where the skill runs.

## License

[MIT](LICENSE)
