param(
  [string]$OutDir = "out\\dm_c1_paper",
  [int]$Seed = 2026,
  [double]$Dt = 0.2,
  [int]$NSteps = 240
)

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo

$py = Join-Path $repo ".venv\\Scripts\\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

& $py run_dm_c1_paper_run.py --out_dir $OutDir --seed $Seed --dt $Dt --n_steps $NSteps
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output ("OK out_dir=" + (Resolve-Path $OutDir).Path)
