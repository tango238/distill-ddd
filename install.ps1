# install.ps1 — Install the `ddd` skill for Claude Code / Codex / Gemini on Windows.
#
# Usage:
#   .\install.ps1                # install to every supported CLI (default)
#   .\install.ps1 -Claude        # install only for Claude Code
#   .\install.ps1 -Codex         # install only for Codex CLI
#   .\install.ps1 -Gemini        # install only for Gemini CLI
#   .\install.ps1 -Uninstall     # remove the skill from every detected CLI
#   .\install.ps1 -Prefix DIR    # override USERPROFILE (for testing)

[CmdletBinding()]
param(
    [switch]$Claude,
    [switch]$Codex,
    [switch]$Gemini,
    [switch]$All,
    [switch]$Uninstall,
    [string]$Prefix = $env:USERPROFILE
)

$ErrorActionPreference = "Stop"
$SkillName = "ddd"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not ($Claude -or $Codex -or $Gemini -or $All)) {
    $Claude = $true; $Codex = $true; $Gemini = $true
}
if ($All) { $Claude = $true; $Codex = $true; $Gemini = $true }

function Copy-Body {
    param([string]$Target)
    $refDest = Join-Path $Target "references"
    New-Item -ItemType Directory -Force -Path $refDest | Out-Null
    Copy-Item -Force (Join-Path $ScriptDir "SKILL.md") (Join-Path $Target "SKILL.md")
    Get-ChildItem (Join-Path $ScriptDir "references") -Filter "*.md" | ForEach-Object {
        Copy-Item -Force $_.FullName $refDest
    }
}

function Remove-Target {
    param([string]$Path)
    if (Test-Path $Path) {
        Remove-Item -Recurse -Force $Path
        Write-Host "  removed   -> $Path"
    }
}

function Write-CodexEntry {
    param([string]$Body, [string]$Entry)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Entry) | Out-Null
    $content = @"
# /ddd — Interactive Domain-Driven Design

Follow the skill defined at ``$Body\SKILL.md``.

When invoked:
1. Read ``$Body\SKILL.md`` for phase structure and interaction rules.
2. For a specific phase, also read ``$Body\references\phase-<name>.md``.
3. Save artifacts to ``docs/domain/`` in the current project.

Arguments: `$ARGUMENTS
"@
    Set-Content -Path $Entry -Value $content -Encoding utf8
}

function Write-GeminiEntry {
    param([string]$Body, [string]$Entry)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Entry) | Out-Null
    $bodyFwd = $Body -replace '\\', '/'
    $content = @"
description = "Interactive Domain-Driven Design modeling facilitator (DDD Distilled based)"
prompt = """
Follow the skill defined at $bodyFwd/SKILL.md.

When invoked:
1. Read $bodyFwd/SKILL.md for phase structure and interaction rules.
2. For a specific phase, also read $bodyFwd/references/phase-<name>.md.
3. Save artifacts to docs/domain/ in the current project.

Arguments: {{args}}
"""
"@
    Set-Content -Path $Entry -Value $content -Encoding utf8
}

function Install-Claude {
    $body = Join-Path $Prefix ".claude\skills\$SkillName"
    Write-Host "[Claude Code]"
    Copy-Body -Target $body
    Write-Host "  installed -> $body"
}

function Install-Codex {
    $body = Join-Path $Prefix ".codex\skills\$SkillName"
    $entry = Join-Path $Prefix ".codex\prompts\$SkillName.md"
    Write-Host "[Codex CLI]"
    Copy-Body -Target $body
    Write-CodexEntry -Body $body -Entry $entry
    Write-Host "  installed -> $body"
    Write-Host "  entry     -> $entry"
}

function Install-Gemini {
    $body = Join-Path $Prefix ".gemini\skills\$SkillName"
    $entry = Join-Path $Prefix ".gemini\commands\$SkillName.toml"
    Write-Host "[Gemini CLI]"
    Copy-Body -Target $body
    Write-GeminiEntry -Body $body -Entry $entry
    Write-Host "  installed -> $body"
    Write-Host "  entry     -> $entry"
}

function Uninstall-Claude {
    Write-Host "[Claude Code]"
    Remove-Target -Path (Join-Path $Prefix ".claude\skills\$SkillName")
}
function Uninstall-Codex {
    Write-Host "[Codex CLI]"
    Remove-Target -Path (Join-Path $Prefix ".codex\skills\$SkillName")
    Remove-Target -Path (Join-Path $Prefix ".codex\prompts\$SkillName.md")
}
function Uninstall-Gemini {
    Write-Host "[Gemini CLI]"
    Remove-Target -Path (Join-Path $Prefix ".gemini\skills\$SkillName")
    Remove-Target -Path (Join-Path $Prefix ".gemini\commands\$SkillName.toml")
}

if ($Uninstall) {
    if ($Claude) { Uninstall-Claude }
    if ($Codex)  { Uninstall-Codex }
    if ($Gemini) { Uninstall-Gemini }
    Write-Host "done: uninstall complete"
} else {
    if ($Claude) { Install-Claude }
    if ($Codex)  { Install-Codex }
    if ($Gemini) { Install-Gemini }
    Write-Host "done: installed skill '$SkillName'"
    Write-Host ""
    Write-Host "Invoke with /$SkillName in your CLI."
}
