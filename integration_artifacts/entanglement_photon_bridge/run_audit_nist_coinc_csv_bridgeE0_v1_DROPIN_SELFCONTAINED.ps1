[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$InCsv,
  [int]$GapBins = 24,
  [switch]$LogGapBins,
  [string]$OutDir = "out",
  [string]$Prefix = "coinc_audit"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "audit_nist_coinc_csv_bridgeE0_v1_DROPIN.py"
if(-not (Test-Path $scriptPath)) {
  throw "Python script not found: $scriptPath"
}

$argsList = @(
  $scriptPath,
  "--in_csv", $InCsv,
  "--gap_bins", "$GapBins",
  "--out_dir", $OutDir,
  "--prefix", $Prefix
)

if($LogGapBins.IsPresent) {
  $argsList += "--log_gap_bins"
}

Write-Host ("Running Python audit: " + $scriptPath)
& py -3 -X utf8 @argsList
if($LASTEXITCODE -ne 0) {
  throw "Python audit failed with exit code $LASTEXITCODE"
}
