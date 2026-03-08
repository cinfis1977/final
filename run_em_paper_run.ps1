Param(
  [string]$OutDir = "out/em_paper",
  [ValidateSet('total','stat','sys_corr','diag_total')][string]$Cov = "total",
  [double]$A = 0.0,
  [switch]$ShapeOnly,
  [switch]$FreezeBetas,
  [switch]$BetaNonneg,
  [switch]$RequirePositive
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$Py = Join-Path $RepoRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $Py)) {
  $Py = "python"
}

$argsList = @(
  "run_em_paper_run.py",
  "--out_dir", $OutDir,
  "--cov", $Cov,
  "--A", "$A"
)

if ($ShapeOnly) { $argsList += "--shape_only" }
if ($FreezeBetas) { $argsList += "--freeze_betas" }
if ($BetaNonneg) { $argsList += "--beta_nonneg" }
if ($RequirePositive) { $argsList += "--require_positive" }

& $Py @argsList
