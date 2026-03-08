# run_prereg_entanglement_memory_from_coinc_csv_v1_DROPIN_SELFCONTAINED.ps1
# DROP-IN v1.2.1 (NO FIT, calibration fallback fix) -- Bridge-E0 + null tests + global CHSH check (PowerShell 5.1-safe)

param(
  [Parameter(Mandatory=$true)][string]$InCsv,
  [int]$NBins = 12,
  [switch]$LogGapBins,
  [double]$KSigma = 2.0,
  [string]$OutCsv = "out\entanglement_memory_prereg_v1.csv",
  [string]$OutBinsCsv = "out\entanglement_memory_bins_v1.csv",
  [string]$OutDebugTxt = "out\entanglement_memory_debug_v1.txt",
  [switch]$NullGapShuffle,
  [switch]$NullOutcomeShuffle,
  [switch]$GlobalCHSHCheck,
  [int]$NullReps = 200,
  [int]$Seed = 12345,
  [string]$PythonExe = "py"
)

$ErrorActionPreference = "Stop"
$Here = $PSScriptRoot
if([string]::IsNullOrWhiteSpace($Here)) { $Here = (Get-Location).Path }

$ScriptPath = Join-Path $Here "prereg_entanglement_memory_from_coinc_csv_v1_2_DROPIN.py"
if(-not (Test-Path $ScriptPath)) { throw "Python runner not found: $ScriptPath" }

$od1 = Split-Path -Parent $OutCsv
$od2 = Split-Path -Parent $OutBinsCsv
$od3 = Split-Path -Parent $OutDebugTxt
if(-not [string]::IsNullOrWhiteSpace($od1)) { New-Item -ItemType Directory -Force -Path $od1 | Out-Null }
if(-not [string]::IsNullOrWhiteSpace($od2)) { New-Item -ItemType Directory -Force -Path $od2 | Out-Null }
if(-not [string]::IsNullOrWhiteSpace($od3)) { New-Item -ItemType Directory -Force -Path $od3 | Out-Null }

$ArgsList = @(
  "-3","-X","utf8",
  $ScriptPath,
  "--in_csv", $InCsv,
  "--nbins", ("" + $NBins),
  "--k_sigma", ("" + $KSigma),
  "--out_csv", $OutCsv,
  "--out_bins_csv", $OutBinsCsv,
  "--out_debug_txt", $OutDebugTxt,
  "--null_reps", ("" + $NullReps),
  "--seed", ("" + $Seed)
)
if($LogGapBins.IsPresent) { $ArgsList += "--log_gap_bins" }
if($NullGapShuffle.IsPresent) { $ArgsList += "--null_gap_shuffle" }
if($NullOutcomeShuffle.IsPresent) { $ArgsList += "--null_outcome_shuffle" }
if($GlobalCHSHCheck.IsPresent) { $ArgsList += "--global_chsh_check" }

Write-Host ("Running Python runner: {0}" -f $ScriptPath)
& $PythonExe @ArgsList
