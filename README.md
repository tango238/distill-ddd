# distill-ddd

『**DDD Distilled**』(Vaughn Vernon) をベースにした、対話型ドメイン駆動設計モデリングスキル。
**Claude Code** / **Codex CLI** / **Gemini CLI** の3環境、**macOS** / **Linux** / **Windows** で動作します。

AI がファシリテーター兼ドメインエキスパート（時に批判者）として振る舞い、以下8フェーズの対話を通じてモデリングをガイドします — discover, storming, contexts, mapping, aggregates, events, validate, glossary。

## インストール

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

デフォルトでは対応する3つの CLI 全てにインストールされます。特定の CLI だけを対象にしたい場合はフラグを指定:

| CLI | bash | PowerShell |
|---|---|---|
| Claude Code | `./install.sh --claude` | `.\install.ps1 -Claude` |
| Codex CLI   | `./install.sh --codex`  | `.\install.ps1 -Codex` |
| Gemini CLI  | `./install.sh --gemini` | `.\install.ps1 -Gemini` |

アンインストール:

```sh
./install.sh --uninstall        # macOS / Linux
.\install.ps1 -Uninstall        # Windows
```

### 配置場所

各 CLI に、スキル本体 (SKILL.md + references) と `/ddd` を有効化するネイティブなエントリポイントの両方を配置します。

| CLI | スキル本体 | エントリポイント (`/ddd`) |
|---|---|---|
| Claude Code | `~/.claude/skills/ddd/` | 同上（自動認識） |
| Codex CLI   | `~/.codex/skills/ddd/`  | `~/.codex/prompts/ddd.md` |
| Gemini CLI  | `~/.gemini/skills/ddd/` | `~/.gemini/commands/ddd.toml` |

Windows では `%USERPROFILE%` 配下に同構造で配置されます（例: `%USERPROFILE%\.codex\prompts\ddd.md`）。

## 使い方

3つの CLI いずれからも `/ddd` で起動できます:

```
/ddd                          フェーズ選択メニュー
/ddd <phase>                  指定フェーズに直接ジャンプ (discover, storming, contexts, ...)
/ddd <phase> --analyze        既存コードベースとモデルを突き合わせる
/ddd <phase> --challenge      批判モード: 前提を徹底的に疑う
/ddd --resume                 前回のセッション状態から再開
/ddd --status                 全フェーズの進捗を表示
```

## フェーズ

| # | Phase | 目的 | 成果物 |
|---|-------|------|--------|
| 1 | `discover` | Core Domain・ビジネスドライバー・問題空間を特定 | `discovery.md` |
| 2 | `storming` | Event Storming: イベント → コマンド → 集約 | `event-storming.md` |
| 3 | `contexts` | Bounded Context と Subdomain を定義 | `bounded-contexts.md` |
| 4 | `mapping` | コンテキスト間関係を描いた Context Map を作成 | `context-map.md` |
| 5 | `aggregates` | 4つのルールに基づく集約設計 | `aggregates.md` |
| 6 | `events` | ドメインイベントの命名・属性・因果関係を設計 | `domain-events.md` |
| 7 | `validate` | ユースケース・シナリオ・UI ウォークスルーでモデルを検証 | `validation.md` |
| 8 | `glossary` | ユビキタス言語を集約・洗練 | `glossary.md` |

成果物は、スキルを動かすプロジェクトの `docs/domain/` に書き出されます。

## ライセンス

[MIT](LICENSE)
