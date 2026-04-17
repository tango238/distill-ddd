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
    $Claude = $true
    $Codex = $true
    $Gemini = $true
}
if ($All) {
    $Claude = $true
    $Codex = $true
    $Gemini = $true
}

function Copy-Skill {
    param([string]$Target)
    $refDest = Join-Path $Target "references"
    New-Item -ItemType Directory -Force -Path $refDest | Out-Null
    Copy-Item -Force (Join-Path $ScriptDir "SKILL.md") (Join-Path $Target "SKILL.md")
    Get-ChildItem (Join-Path $ScriptDir "references") -Filter "*.md" | ForEach-Object {
        Copy-Item -Force $_.FullName $refDest
    }
    Write-Host "  installed -> $Target"
}

function Remove-Skill {
    param([string]$Target)
    if (Test-Path $Target) {
        Remove-Item -Recurse -Force $Target
        Write-Host "  removed   -> $Target"
    }
}

function Process-CLI {
    param([string]$Label, [string]$Base)
    $target = Join-Path $Base "skills\$SkillName"
    Write-Host "[$Label]"
    if ($Uninstall) {
        Remove-Skill -Target $target
    } else {
        Copy-Skill -Target $target
    }
}

if ($Claude) { Process-CLI -Label "Claude Code" -Base (Join-Path $Prefix ".claude") }
if ($Codex)  { Process-CLI -Label "Codex CLI"   -Base (Join-Path $Prefix ".codex") }
if ($Gemini) { Process-CLI -Label "Gemini CLI"  -Base (Join-Path $Prefix ".gemini") }

if ($Uninstall) {
    Write-Host "done: uninstall complete"
} else {
    Write-Host "done: installed skill '$SkillName'"
    Write-Host ""
    Write-Host "Activate with:"
    Write-Host "  Claude Code: /$SkillName"
    Write-Host "  Codex CLI:   /$SkillName   (add to AGENTS.md if needed)"
    Write-Host "  Gemini CLI:  /$SkillName   (or via activate_skill)"
}
