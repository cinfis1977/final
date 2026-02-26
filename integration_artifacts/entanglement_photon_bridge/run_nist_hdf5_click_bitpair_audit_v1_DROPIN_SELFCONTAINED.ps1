param(
  [Parameter(Mandatory=$true)][string]$H5Path,
  [string]$OutDir = "out",
  [string]$Prefix = "nist_h5bitpair_audit",
  [int]$TopBits = 12,
  [int]$MinRows = 200
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $scriptDir "nist_hdf5_click_bitpair_audit_v1_DROPIN.py"
if(-not (Test-Path $py)) { throw "Python script not found: $py" }
Write-Host "Running Python audit: $py"
& py -3 -X utf8 $py `
  --h5 $H5Path `
  --out_dir $OutDir `
  --prefix $Prefix `
  --top_bits $TopBits `
  --min_rows $MinRows
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }
