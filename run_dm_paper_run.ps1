$ErrorActionPreference = 'Stop'

# DM paper-run wrapper (Windows-friendly)
# Runs from repo root; writes to out/dm_paper by default.

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$py = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
  $py = 'python'
}

& $py .\run_dm_paper_run.py @Args
