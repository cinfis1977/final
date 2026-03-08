Param(
  [string]$OutDir = "out/strong_c5a",
  [switch]$NoPoison,
  [double]$A = 0.0
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$Py = Join-Path $RepoRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $Py)) {
  $Py = "python"
}

$argsList = @("run_strong_c5a_paper_run.py", "--out_dir", $OutDir, "--A", "$A")
if ($NoPoison) {
  $argsList += "--no_poison"
}

& $Py @argsList
