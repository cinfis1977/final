param(
  [string]$RunId = "",
  [switch]$StopOnFailure
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  if (-not $PSScriptRoot) {
    throw "Unable to resolve script root (PSScriptRoot is empty)."
  }
  return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-GitHead([string]$RepoRoot) {
  try {
    Push-Location $RepoRoot
    $h = (git rev-parse HEAD 2>$null | Out-String).Trim()
    Pop-Location
    return $h
  } catch {
    try { Pop-Location } catch {}
    return ""
  }
}

function Pick-PythonExe([string]$RepoRoot) {
  $py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
  if (Test-Path $py) { return $py }
  return "python"
}

function New-RunIdIfEmpty([string]$RepoRoot, [string]$RunIdIn) {
  if ($RunIdIn -and $RunIdIn.Trim().Length -gt 0) { return $RunIdIn }

  $date = (Get-Date).ToString("yyyy-MM-dd")
  $n = 1

  $sectors = @("weak", "strong", "em", "dm")

  while ($true) {
    $candidate = "{0}_run{1:D2}" -f $date, $n
    $exists = $false
    foreach ($s in $sectors) {
      $p = Join-Path $RepoRoot (Join-Path "logs" (Join-Path $s $candidate))
      if (Test-Path $p) {
        $exists = $true
        break
      }
    }
    if (-not $exists) {
      return $candidate
    }
    $n += 1
    if ($n -gt 99) { throw "Unable to allocate a run id for date=$date (exhausted run01..run99)." }
  }
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Write-TextUtf8([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if ($dir) { Ensure-Dir $dir }
  $Content | Set-Content -Path $Path -Encoding UTF8
}

function Format-CmdLine([string]$Exe, [string[]]$CmdArgs) {
  $parts = @()
  $parts += $Exe
  foreach ($a in $CmdArgs) {
    if ($null -eq $a) { continue }
    if ($a -match "\s") {
      $parts += ('"' + $a.Replace('"','\\"') + '"')
    } else {
      $parts += $a
    }
  }
  return ($parts -join " ")
}

function Copy-ProducedArtifacts([string]$FromPath, [string]$ToDir) {
  Ensure-Dir $ToDir

  if (-not (Test-Path $FromPath)) {
    return
  }

  $item = Get-Item -LiteralPath $FromPath

  if ($item.PSIsContainer) {
    Get-ChildItem -LiteralPath $FromPath -Recurse -File | Where-Object {
      $_.Extension -in @(".csv", ".json")
    } | ForEach-Object {
      Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $ToDir $_.Name) -Force
    }
  } else {
    $ext = [System.IO.Path]::GetExtension($FromPath)
    if ($ext -in @(".csv", ".json")) {
      Copy-Item -LiteralPath $FromPath -Destination (Join-Path $ToDir ([System.IO.Path]::GetFileName($FromPath))) -Force
    }
  }
}

function Invoke-CapturedRun(
  [string]$Sector,
  [string]$RunId,
  [string]$Name,
  [string]$Exe,
  [Alias('Args')]
  [string[]]$RunArgs,
  [string]$ArtifactsFrom,
  [string]$RepoRoot,
  [string]$GitHead
) {
  $base = Join-Path $RepoRoot (Join-Path "logs" (Join-Path $Sector (Join-Path $RunId $Name)))
  Ensure-Dir $base

  $cmdLine = Format-CmdLine $Exe $RunArgs
  Write-TextUtf8 -Path (Join-Path $base "command.txt") -Content ($cmdLine + "`n")

  $startUtc = (Get-Date).ToUniversalTime().ToString("o")

  $output = ""
  $rc = 999
  $status = "unknown"
  try {
    Push-Location $RepoRoot
    $output = (& $Exe @RunArgs 2>&1 | Out-String)
    $rc = [int]$LASTEXITCODE
    Pop-Location
    $status = if ($rc -eq 0) { "ok" } else { "fail" }
  } catch {
    try { Pop-Location } catch {}
    $output = ($output + "`n" + ($_ | Out-String))
    $rc = 999
    $status = "exception"
  }

  $endUtc = (Get-Date).ToUniversalTime().ToString("o")

  $term = @(
    "# terminal output",
    "",
    $output.TrimEnd(),
    "",
    ("EXIT_CODE: {0}" -f $rc),
    ""
  ) -join "`n"

  Write-TextUtf8 -Path (Join-Path $base "terminal_output_and_exit_code.txt") -Content $term

  $meta = [ordered]@{
    sector = $Sector
    run_id = $RunId
    name = $Name
    status = $status
    start_utc = $startUtc
    end_utc = $endUtc
    git_head = $GitHead
    repo_root = $RepoRoot
    exe = $Exe
    args = $RunArgs
    cmd = $cmdLine
    artifacts_from = $ArtifactsFrom
  }
  ($meta | ConvertTo-Json -Depth 6) | Set-Content -Path (Join-Path $base "meta.json") -Encoding UTF8

  $artDir = Join-Path $base "artifacts"
  Copy-ProducedArtifacts -FromPath $ArtifactsFrom -ToDir $artDir

  if ($rc -ne 0 -and $StopOnFailure) {
    throw "Run failed: sector=$Sector name=$Name rc=$rc (see $base)"
  }

  return [ordered]@{ sector=$Sector; name=$Name; rc=$rc; status=$status; dir=$base }
}

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

$gitHead = Get-GitHead $repoRoot
$py = Pick-PythonExe $repoRoot

$runIdFinal = New-RunIdIfEmpty $repoRoot $RunId

# Output scratch (so artifact copies are not contaminated by previous runs)
$outBase = Join-Path $repoRoot (Join-Path "out" (Join-Path "log_capture" $runIdFinal))
Ensure-Dir $outBase

$results = @()

# --- WEAK ---
$weakOutDir = Join-Path $outBase "weak"
Ensure-Dir $weakOutDir

# 1) Legacy phase-map runner (proxy-ish; kept as reference)
$weakPhaseCsv = Join-Path $weakOutDir "t2k_phase_map.csv"
$results += Invoke-CapturedRun -Sector "weak" -RunId $runIdFinal -Name "t2k_phase_map_fixedbyclaude" -Exe $py -Args @(
  "nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py",
  "--pack", "t2k_channels_real_approx.json",
  "--kernel", "rt", "--k_rt", "180",
  "--A", "-0.002", "--alpha", "0.7", "--n", "0", "--E0", "1",
  "--omega0_geom", "fixed", "--L0_km", "295",
  "--phi", "1.57079632679", "--zeta", "0.05",
  "--rho", "2.6", "--kappa_gate", "0", "--T0", "1", "--mu", "0", "--eta", "0",
  "--bin_shift_app", "0", "--bin_shift_dis", "0",
  "--breath_B", "0.3", "--breath_w0", "0.00387850944887629", "--breath_gamma", "0.2",
  "--thread_C", "1.0", "--thread_w0", "0.00387850944887629", "--thread_gamma", "0.2",
  "--thread_weight_app", "0", "--thread_weight_dis", "1",
  "--out", $weakPhaseCsv
) -ArtifactsFrom $weakPhaseCsv -RepoRoot $repoRoot -GitHead $gitHead

# 2) Explicit GKSL dynamics runner (state evolution)
$weakGkslCsv = Join-Path $weakOutDir "t2k_gksl_dynamics.csv"
$results += Invoke-CapturedRun -Sector "weak" -RunId $runIdFinal -Name "t2k_gksl_dynamics" -Exe $py -Args @(
  "nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py",
  "--pack", "t2k_channels_real_approx.json",
  "--kernel", "rt", "--k_rt", "180",
  "--A", "-0.002", "--alpha", "0.7", "--n", "0", "--E0", "1",
  "--omega0_geom", "fixed", "--L0_km", "295",
  "--phi", "1.57079632679", "--zeta", "0.05",
  "--rho", "2.6", "--kappa_gate", "0", "--T0", "1", "--mu", "0", "--eta", "0",
  "--bin_shift_app", "0", "--bin_shift_dis", "0",
  "--breath_B", "0.3", "--breath_w0", "0.00387850944887629", "--breath_gamma", "0.2",
  "--thread_C", "1.0", "--thread_w0", "0.00387850944887629", "--thread_gamma", "0.2",
  "--thread_weight_app", "0", "--thread_weight_dis", "1",
  "--flavors", "3",
  "--steps", "700",
  "--out", $weakGkslCsv
) -ArtifactsFrom $weakGkslCsv -RepoRoot $repoRoot -GitHead $gitHead

# --- STRONG ---
$strongOutDir = Join-Path $outBase "strong_c5a"
$results += Invoke-CapturedRun -Sector "strong" -RunId $runIdFinal -Name "strong_c5a_paper_run" -Exe $py -Args @(
  "run_strong_c5a_paper_run.py",
  "--out_dir", $strongOutDir
) -ArtifactsFrom $strongOutDir -RepoRoot $repoRoot -GitHead $gitHead

# --- EM ---
$emOutDir = Join-Path $outBase "em_paper"
$results += Invoke-CapturedRun -Sector "em" -RunId $runIdFinal -Name "em_paper_run" -Exe $py -Args @(
  "run_em_paper_run.py",
  "--out_dir", $emOutDir,
  "--shape_only",
  "--freeze_betas"
) -ArtifactsFrom $emOutDir -RepoRoot $repoRoot -GitHead $gitHead

# --- DM ---
$dmOutDir = Join-Path $outBase "dm_paper"
$results += Invoke-CapturedRun -Sector "dm" -RunId $runIdFinal -Name "dm_proxy_paper_run" -Exe $py -Args @(
  "run_dm_paper_run.py",
  "--out_dir", $dmOutDir,
  "--kfold", "2",
  "--seed", "2026"
) -ArtifactsFrom $dmOutDir -RepoRoot $repoRoot -GitHead $gitHead

$dmC1OutDir = Join-Path $outBase "dm_c1_paper"
$results += Invoke-CapturedRun -Sector "dm" -RunId $runIdFinal -Name "dm_c1_dynamics_paper_run" -Exe $py -Args @(
  "run_dm_c1_paper_run.py",
  "--out_dir", $dmC1OutDir,
  "--seed", "2026",
  "--dt", "0.2",
  "--n_steps", "240"
) -ArtifactsFrom $dmC1OutDir -RepoRoot $repoRoot -GitHead $gitHead

$dmC2OutDir = Join-Path $outBase "dm_c2_paper"
$results += Invoke-CapturedRun -Sector "dm" -RunId $runIdFinal -Name "dm_c2_realpack_dynamics_paper_run" -Exe $py -Args @(
  "run_dm_c2_paper_run.py",
  "--out_dir", $dmC2OutDir,
  "--max_galaxies", "5",
  "--min_points", "8",
  "--seed", "2026",
  "--dt", "0.001",
  "--n_steps", "300"
) -ArtifactsFrom $dmC2OutDir -RepoRoot $repoRoot -GitHead $gitHead

$dmC2CvOutDir = Join-Path $outBase "dm_c2_cv_paper"
$results += Invoke-CapturedRun -Sector "dm" -RunId $runIdFinal -Name "dm_c2_holdout_cv_paper_run" -Exe $py -Args @(
  "run_dm_c2_cv_paper_run.py",
  "--out_dir", $dmC2CvOutDir,
  "--max_galaxies", "8",
  "--min_points", "8",
  "--kfold", "4",
  "--seed", "2026",
  "--dt", "0.001",
  "--n_steps", "240",
  "--order_mode", "forward",
  "--A_min", "0.0",
  "--A_max", "0.2",
  "--nA", "21"
) -ArtifactsFrom $dmC2CvOutDir -RepoRoot $repoRoot -GitHead $gitHead

# Write a minimal index under logs/
$indexPath = Join-Path $repoRoot (Join-Path "logs" ("RUN_INDEX_{0}.md" -f $runIdFinal))
$lines = @()
$lines += "# Run index: $runIdFinal"
$lines += ""
$lines += "- repo: $repoRoot"
$lines += "- git_head: $gitHead"
$lines += "- generated_utc: " + (Get-Date).ToUniversalTime().ToString("o")
$lines += ""
$lines += "## Captured runs"
$lines += ""
foreach ($r in $results) {
  $lines += "- sector=$($r.sector) name=$($r.name) status=$($r.status) rc=$($r.rc)"
  $lines += "  - dir: $($r.dir)"
}
$lines += ""
Write-TextUtf8 -Path $indexPath -Content (($lines -join "`n") + "`n")

Write-Output ("OK run_id=" + $runIdFinal)
Write-Output ("index=" + $indexPath)
