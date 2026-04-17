---
name: release-gate
description: Pre-push gate for distill-ddd — never push without explicit user approval and verified cross-platform installation
---

# Release Gate (distill-ddd)

## push は勝手に行わない

- `git push` は **ユーザーの明示的な許可があるまで実行禁止**。
- Auto モードでも例外なく事前確認を取る。
- `git push --force` / `git push origin :branch` などの破壊的 push は特に厳禁。

**Why:** 公開リポジトリに壊れた状態を push すると、インストールしたユーザー全員のスキルが壊れる。ロールバックしても履歴には残る。

**How to apply:** `git push` を実行する前に、必ず以下のチェックリストを満たすこと。

## push 前チェックリスト

push 前に以下を**全て**完了させ、ユーザーに確認を取ること。

### 1. 変更内容の提示

ユーザーに以下を**箇条書き**で示す。

- 追加 / 変更 / 削除されたファイル
- それぞれの変更の目的（なぜ変えたか）
- 互換性を壊す変更があるか（あれば赤字で強調）

### 2. Windows 動作確認

`install.ps1` が Windows でそのまま動くことを確認する。手元に Windows 環境がない場合は以下のいずれかで代替:

- GitHub Actions (`windows-latest`) で `pwsh install.ps1 -Prefix <tmp>` を流す
- Parallels / UTM / リモート Windows マシンで手動実行
- `pwsh` (PowerShell Core) が Mac にある場合は `-Prefix` を使った dry-run

確認内容:
- `install.ps1` がエラーなく完走する
- 指定した `-Prefix` 配下の `skills/ddd/SKILL.md` と `skills/ddd/references/*.md` が正しく配置される
- `-Uninstall` で削除できる

### 3. macOS ローカル動作確認

開発機の macOS で以下を実行:

- `./install.sh --prefix /tmp/distill-ddd-test` が完走する
- `/tmp/distill-ddd-test/.claude/skills/ddd/`, `.codex/skills/ddd/`, `.gemini/skills/ddd/` に SKILL.md と references が揃う
- `./install.sh --prefix /tmp/distill-ddd-test --uninstall` で消える
- 個別フラグ (`--claude` 等) が意図通り動く

### 4. ユーザー承認

上記 1〜3 の結果を提示し、**「push してよいか」を明示的に確認**。
ユーザーの "push して" / "OK" 等の明示的な承認が得られてから `git push` を実行する。

**Why:** これは OSS 配布物で、Windows ユーザーが多数使う前提。Mac だけでの確認で push すると、Windows での初回インストールが壊れるリスクがある。

**How to apply:** このチェックリストの 1〜4 を飛ばして push しない。Auto モードの「minimize interruptions」よりこのルールが優先される。
