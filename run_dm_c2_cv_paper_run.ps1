param(
  [string]$OutDir = "out\\dm_c2_cv_paper",
  [string]$PointsCsv = "data\\sparc\\sparc_points.csv",
  [int]$MaxGalaxies = 8,
  [int]$MinPoints = 8,
  [int]$Kfold = 4,
  [int]$Seed = 2026,
  [double]$Dt = 0.001,
  [int]$NSteps = 240,
  [string]$OrderMode = "forward",
  [double]$SigmaFloor = 1e-6,
  [double]$AMin = 0.0,
  [double]$AMax = 0.2,
  [int]$NA = 21
)

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repo

$py = Join-Path $repo ".venv\\Scripts\\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

& $py run_dm_c2_cv_paper_run.py `
  --out_dir $OutDir `
  --points_csv $PointsCsv `
  --max_galaxies $MaxGalaxies `
  --min_points $MinPoints `
  --kfold $Kfold `
  --seed $Seed `
  --dt $Dt `
  --n_steps $NSteps `
  --order_mode $OrderMode `
  --sigma_floor $SigmaFloor `
  --A_min $AMin `
  --A_max $AMax `
  --nA $NA
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output ("OK out_dir=" + (Resolve-Path $OutDir).Path)
