param(
  [Parameter(Mandatory=$true)][string]$PairB2Dir,
  [Parameter(Mandatory=$true)][string]$PairB3Dir,
  [Parameter(Mandatory=$true)][string]$ThirdArmDir,
  [Parameter(Mandatory=$true)][string]$TargetsCsv,
  [Parameter(Mandatory=$true)][string]$OutDir,

  [double]$GoodPpm = 3,
  [double]$WindowPpm = 30,
  [double]$Tail3Ppm = -300000,
  [int]$MinN = 8,
  [int]$MaxBins = 8,

  [string]$ModeAPoints = "",
  [string]$ModeB2Points = "",
  [string]$ModeB3Points = "",
  [string]$ModeA2Points = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-PyExe {
  $cmd = Get-Command py -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  throw "[FATAL] Could not find 'py' or 'python' on PATH."
}

$pyExe = Get-PyExe
$script = Join-Path $PSScriptRoot "finalize_particle_specific_goodppm_lock_from_runs_v1_0.py"

$args = @(
  $script,
  "--root", ".",
  "--pair_b2_dir", $PairB2Dir,
  "--pair_b3_dir", $PairB3Dir,
  "--third_arm_dir", $ThirdArmDir,
  "--targets_csv", $TargetsCsv,
  "--out_dir", $OutDir,
  "--good_ppm", $GoodPpm,
  "--window_ppm", $WindowPpm,
  "--tail3_ppm", $Tail3Ppm,
  "--min_n", $MinN,
  "--max_bins", $MaxBins
)

if ($ModeAPoints)  { $args += @("--mode_a_points",  $ModeAPoints) }
if ($ModeB2Points) { $args += @("--mode_b2_points", $ModeB2Points) }
if ($ModeB3Points) { $args += @("--mode_b3_points", $ModeB3Points) }
if ($ModeA2Points) { $args += @("--mode_a2_points", $ModeA2Points) }

& $pyExe -3 -X utf8 @args
