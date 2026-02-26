# run_nist_hdf5_export_coinc_bridgeE0_v1_2_1_DROPIN_SELFCONTAINED.ps1
# Exports coincidence-level CSV for Bridge-E0 entanglement prereg from NIST processed HDF5
# No fit. Real data helper.

[CmdletBinding()]
param(
  [string]$Hdf5Path = ".\data\nist\03_43_run4_afterfixingModeLocking.build.hdf5",
  [ValidateSet('','01_11','02_54','03_43')]
  [string]$DownloadRun = '03_43',
  [switch]$ForceRedownload,
  [switch]$InspectOnly,
  [switch]$CoincOnly,
  [ValidateSet('half','parity')]
  [string]$OutcomeMode = 'half',
  [string]$OutCsv = "out\nist_run4_coincidences.csv",
  [string]$SchemaTxt = "out\nist_hdf5_schema_v1.txt",
  [string]$DebugTxt = "out\nist_hdf5_export_debug_v1.txt",
  [string]$SettingsPath = "",
  [string]$ClicksPath = "",
  [string]$ASettingsPath = "",
  [string]$BSettingsPath = "",
  [string]$AClicksPath = "",
  [string]$BClicksPath = "",
  [string]$IndexPath = ""
)

$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'nist_hdf5_inspect_and_export_coinc_bridgeE0_v1_2_1_DROPIN.py'
if(-not (Test-Path $scriptPath)) {
  throw "Python helper not found: $scriptPath"
}

$dlArg = @()
if($DownloadRun -ne '') { $dlArg = @('--download_run', $DownloadRun) }

# NOTE: Python script expects booleans as switches, so we only append the switch when set.
$pyArgs = @(
  $scriptPath,
  '--hdf5_path', $Hdf5Path,
  '--out_csv', $OutCsv,
  '--schema_txt', $SchemaTxt,
  '--debug_txt', $DebugTxt,
  '--outcome_mode', $OutcomeMode
) + $dlArg

if($ForceRedownload.IsPresent){ $pyArgs += '--force_redownload' }
if($InspectOnly.IsPresent){ $pyArgs += '--inspect_only' }
if($CoincOnly.IsPresent){ $pyArgs += '--coinc_only' }
if($SettingsPath -ne '') { $pyArgs += @('--settings_path', $SettingsPath) }
if($ClicksPath -ne '')   { $pyArgs += @('--clicks_path',   $ClicksPath) }
if($ASettingsPath -ne '') { $pyArgs += @('--a_settings_path', $ASettingsPath) }
if($BSettingsPath -ne '') { $pyArgs += @('--b_settings_path', $BSettingsPath) }
if($AClicksPath -ne '')   { $pyArgs += @('--a_clicks_path',   $AClicksPath) }
if($BClicksPath -ne '')   { $pyArgs += @('--b_clicks_path',   $BClicksPath) }
if($IndexPath -ne '')     { $pyArgs += @('--index_path',      $IndexPath) }

Write-Host "Running Python helper: $scriptPath"
& py -3 -X utf8 @pyArgs
if($LASTEXITCODE -ne 0) {
  throw "Python helper failed with exit code $LASTEXITCODE"
}
