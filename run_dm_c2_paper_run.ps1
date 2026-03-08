param(
  [string]$OutDir = "out\\dm_c2_paper",
  [string]$PointsCsv = "data\\sparc\\sparc_points.csv",
  [int]$MaxGalaxies = 5,
  [int]$MinPoints = 8,
  [int]$Seed = 2026,
  [double]$Dt = 0.001,
  [int]$NSteps = 300
)

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo

$py = Join-Path $repo ".venv\\Scripts\\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

& $py run_dm_c2_paper_run.py `
  --out_dir $OutDir `
  --points_csv $PointsCsv `
  --max_galaxies $MaxGalaxies `
  --min_points $MinPoints `
  --seed $Seed `
  --dt $Dt `
  --n_steps $NSteps
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output ("OK out_dir=" + (Resolve-Path $OutDir).Path)
