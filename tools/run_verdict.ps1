param(
    [string]$RepoRoot = "",
    [string]$CommandsFile = "",
    [string]$DataAllowlistFile = "",
    [int]$StartIndex = 1,
    [int]$EndIndex = 0,
    [int]$PerCommandTimeoutSec = 1800,
    [switch]$AppendSummary
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
}

if ([string]::IsNullOrWhiteSpace($CommandsFile)) {
    $CommandsFile = Join-Path $RepoRoot 'tools\verdict_commands.txt'
}

if ([string]::IsNullOrWhiteSpace($DataAllowlistFile)) {
    $DataAllowlistFile = Join-Path $RepoRoot 'tools\data_allowlist.txt'
}

function Normalize-RelPath {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) { return $null }
    $p = $PathValue.Trim().Trim('"').Trim("'")
    $p = $p -replace '^[\.\s\\/]+', ''
    $p = $p -replace '/', '\\'
    return $p
}

function Get-FlagValues {
    param(
        [string]$Command,
        [string]$Flag
    )

    $pattern = '(?i)--' + [regex]::Escape($Flag) + '\s+("[^"]+"|\S+)'
    $matches = [regex]::Matches($Command, $pattern)
    $vals = New-Object System.Collections.Generic.List[string]
    foreach ($m in $matches) {
        $vals.Add($m.Groups[1].Value)
    }
    return @($vals.ToArray())
}

function Parse-VerdictCommands {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Commands file not found: $Path"
    }

    $lines = Get-Content -LiteralPath $Path
    $sector = 'UNSPECIFIED'
    $rows = New-Object System.Collections.Generic.List[object]
    $current = New-Object System.Collections.Generic.List[string]

    foreach ($line in $lines) {
        $trim = $line.Trim()

        if ($trim -match '^##\s+(.+)$') {
            if ($current.Count -gt 0) {
                $rows.Add([pscustomobject]@{ sector = $sector; command = ($current -join "`n").Trim() })
                $current.Clear()
            }
            $sector = $Matches[1].Trim()
            continue
        }

        if ($trim -match '^```') { continue }
        if ($trim -match '^#' -or $trim -match '^>' -or $trim -eq '---') { continue }

        if ($trim -match '^(py|python)(\s|$)') {
            if ($current.Count -gt 0) {
                $rows.Add([pscustomobject]@{ sector = $sector; command = ($current -join "`n").Trim() })
                $current.Clear()
            }

            $current.Add($trim)
            if (-not $trim.EndsWith('`')) {
                $rows.Add([pscustomobject]@{ sector = $sector; command = ($current -join "`n").Trim() })
                $current.Clear()
            }
            continue
        }

        if ($current.Count -gt 0) {
            if ($trim -eq '') {
                if (-not $current[$current.Count - 1].Trim().EndsWith('`')) {
                    $rows.Add([pscustomobject]@{ sector = $sector; command = ($current -join "`n").Trim() })
                    $current.Clear()
                }
                continue
            }

            $current.Add($trim)
            if (-not $trim.EndsWith('`')) {
                $rows.Add([pscustomobject]@{ sector = $sector; command = ($current -join "`n").Trim() })
                $current.Clear()
            }
        }
    }

    if ($current.Count -gt 0) {
        $rows.Add([pscustomobject]@{ sector = $sector; command = ($current -join "`n").Trim() })
    }

    return @($rows.ToArray())
}

function Get-RunnerName {
    param([string]$Command)

    $m = [regex]::Match($Command, '(?i)(?:^|\s)(?:\.\\|\./)?(?<runner>[^\s"'']+\.py)(?:\s|$)')
    if ($m.Success) {
        return (Normalize-RelPath -PathValue $m.Groups['runner'].Value)
    }
    return 'unknown_runner.py'
}

function Get-DatasetPaths {
    param([string]$Command)

    $datasetFlags = @('pack', 'data', 'points_csv', 'h1_hdf5', 'l1_hdf5', 'v1_hdf5', 'sigma_data', 'rho_data', 'baseline_csv', 'model_csv', 'cv_csv', 'fit_summary_json')
    $vals = New-Object System.Collections.Generic.List[string]

    foreach ($flag in $datasetFlags) {
        $matches = Get-FlagValues -Command $Command -Flag $flag
        foreach ($v in $matches) {
            foreach ($part in $v.Split(',')) {
                $n = Normalize-RelPath -PathValue $part
                if ($n) { $vals.Add($n) }
            }
        }
    }

    if ($vals.Count -eq 0) { return @() }
    return @($vals | Select-Object -Unique)
}

function Get-DatasetSpec {
    param([string[]]$DatasetPaths)
    if (@($DatasetPaths).Count -eq 0) { return '' }
    return (@($DatasetPaths) -join ';')
}

function Get-ExpectedOutputs {
    param([string]$Command)

    $vals = New-Object System.Collections.Generic.List[string]
    $nullSinks = @('NUL', 'CON', 'PRN', 'AUX', 'COM1', 'LPT1')

    foreach ($flag in @('out', 'out_csv', 'chi2_out')) {
        $matches = Get-FlagValues -Command $Command -Flag $flag
        foreach ($v in $matches) {
            $n = Normalize-RelPath -PathValue $v
            if (-not $n) { continue }
            if ($nullSinks -contains $n.ToUpperInvariant()) { continue }
            $vals.Add($n)
        }
    }

    $prefixMatches = Get-FlagValues -Command $Command -Flag 'out_prefix'
    foreach ($p in $prefixMatches) {
        $n = Normalize-RelPath -PathValue $p
        if ($n) { $vals.Add("$n*") }
    }

    if ($vals.Count -eq 0) { return @() }
    return @($vals | Select-Object -Unique)
}

function Load-AllowlistPatterns {
    param([string]$Path)

    $patterns = New-Object System.Collections.Generic.List[string]
    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }

    foreach ($line in (Get-Content -LiteralPath $Path)) {
        $trim = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trim)) { continue }
        if ($trim.StartsWith('#')) { continue }
        $n = Normalize-RelPath -PathValue $trim
        if ($n) { $patterns.Add($n) }
    }

    return @($patterns.ToArray())
}

function Test-DataOk {
    param(
        [string[]]$DatasetPaths,
        [string[]]$AllowlistPatterns,
        [string]$RepoRoot
    )

    $paths = @($DatasetPaths)
    $allow = @($AllowlistPatterns)
    if ($paths.Count -eq 0) {
        return @{
            data_ok = 'NO_DATA'
            data_notes = 'no_dataset_flags'
        }
    }

    $reasons = New-Object System.Collections.Generic.List[string]
    foreach ($p in $paths) {
        $rel = Normalize-RelPath -PathValue $p
        if ([string]::IsNullOrWhiteSpace($rel)) { continue }

        $full = Join-Path $RepoRoot $rel
        if (-not (Test-Path -LiteralPath $full)) {
            $reasons.Add("missing:$rel")
            continue
        }

        $l = $rel.ToLowerInvariant()
        if ($l -match '(generated|simplified|approx|mock|toy|synthetic)') {
            $reasons.Add("generated_like:$rel")
        }

        if ($allow.Count -gt 0) {
            $matched = $false
            foreach ($pat in $allow) {
                if ($rel -like $pat) { $matched = $true; break }
            }
            if (-not $matched) {
                $reasons.Add("not_allowlisted:$rel")
            }
        }
    }

    if ($reasons.Count -eq 0) {
        return @{
            data_ok = 'YES'
            data_notes = ''
        }
    }

    return @{
        data_ok = 'NO'
        data_notes = ($reasons -join '|')
    }
}

function Infer-VerdictPassFromLog {
    param(
        [string]$LogPath,
        [string]$RunOk,
        [string]$DataOk
    )

    if ($RunOk -ne 'YES' -or $DataOk -ne 'YES') {
        return 'UNKNOWN'
    }

    if (-not (Test-Path -LiteralPath $LogPath)) {
        return 'UNKNOWN'
    }

    $txt = Get-Content -LiteralPath $LogPath -Raw -ErrorAction SilentlyContinue
    if ([string]::IsNullOrWhiteSpace($txt)) {
        return 'UNKNOWN'
    }

    if ($txt -match '(?im)\b(verdict[_\s:-]*pass|verdict:\s*pass|preregister(ed)?\s*pass)\b') {
        return 'YES'
    }

    if ($txt -match '(?im)\b(verdict[_\s:-]*fail|verdict:\s*fail|rejected|falsified)\b') {
        return 'NO'
    }

    return 'UNKNOWN'
}

function Run-CommandWithTimeout {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$LogPath,
        [Parameter(Mandatory = $true)][int]$TimeoutSec,
        [Parameter(Mandatory = $true)][string]$TmpScriptPath
    )

    $repoEsc = $RepoRoot.Replace("'", "''")
    $logEsc = $LogPath.Replace("'", "''")

    $runnerLines = New-Object System.Collections.Generic.List[string]
    $runnerLines.Add("Set-Location -LiteralPath '$repoEsc'")
    $runnerLines.Add("`$ErrorActionPreference = 'Continue'")
    $runnerLines.Add("`$logPath = '$logEsc'")
    $runnerLines.Add("try {")
    $runnerLines.Add("    & {")
    foreach ($cmdLine in ($Command -split "`r?`n")) {
        $runnerLines.Add("        $cmdLine")
    }
    $runnerLines.Add("    } *>> `$logPath")
    $runnerLines.Add("    exit `$LASTEXITCODE")
    $runnerLines.Add("}")
    $runnerLines.Add("catch {")
    $runnerLines.Add('    "[runner_exception] $($_.Exception.Message)" *>> $logPath')
    $runnerLines.Add("    exit 999")
    $runnerLines.Add("}")

    Set-Content -LiteralPath $TmpScriptPath -Value $runnerLines -Encoding UTF8

    $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $TmpScriptPath) -PassThru -WindowStyle Hidden

    $finished = $proc.WaitForExit($TimeoutSec * 1000)
    if (-not $finished) {
        cmd /c "taskkill /PID $($proc.Id) /T /F" | Out-Null
        Add-Content -LiteralPath $LogPath -Value "`n[runner_timeout] exceeded ${TimeoutSec}s"
        return [pscustomobject]@{ exit_code = 124; timed_out = $true }
    }

    return [pscustomobject]@{ exit_code = $proc.ExitCode; timed_out = $false }
}

$allowPatterns = @(Load-AllowlistPatterns -Path $DataAllowlistFile)

$reproDir = Join-Path $RepoRoot 'repro'
$logsDir = Join-Path $reproDir 'logs'
New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
New-Item -ItemType Directory -Path $reproDir -Force | Out-Null

Set-Location -LiteralPath $RepoRoot

$rows = Parse-VerdictCommands -Path $CommandsFile
if ($rows.Count -eq 0) {
    throw "No runnable commands found in $CommandsFile"
}

if ($EndIndex -le 0 -or $EndIndex -gt $rows.Count) {
    $EndIndex = $rows.Count
}
if ($StartIndex -lt 1) { $StartIndex = 1 }
if ($StartIndex -gt $EndIndex) {
    throw "Invalid range: StartIndex=$StartIndex EndIndex=$EndIndex"
}

$summaryPath = Join-Path $reproDir 'run_summary.csv'
$summary = New-Object System.Collections.Generic.List[object]

if ($AppendSummary.IsPresent -and (Test-Path -LiteralPath $summaryPath)) {
    $existing = Import-Csv -LiteralPath $summaryPath
    foreach ($e in $existing) {
        $summary.Add([pscustomobject]@{
            run_index = $e.run_index
            sector = $e.sector
            runner = $e.runner
            dataset = $e.dataset
            command = $e.command
            expected_outputs = $e.expected_outputs
            run_ok = $e.run_ok
            data_ok = $e.data_ok
            verdict_pass = $e.verdict_pass
            status = $e.status
            data_notes = $e.data_notes
            notes = $e.notes
            log_file = $e.log_file
        })
    }
}

for ($idx = $StartIndex; $idx -le $EndIndex; $idx++) {
    $row = $rows[$idx - 1]

    $sectorClean = ($row.sector -replace '[^A-Za-z0-9]+', '_').Trim('_')
    if ([string]::IsNullOrWhiteSpace($sectorClean)) { $sectorClean = 'UNSPECIFIED' }

    $runner = Get-RunnerName -Command $row.command
    $runnerBase = [IO.Path]::GetFileNameWithoutExtension($runner)
    if ([string]::IsNullOrWhiteSpace($runnerBase)) { $runnerBase = "run_$idx" }

    $logRel = "repro\\logs\\{0:D3}_{1}_{2}.log" -f $idx, $sectorClean, ($runnerBase -replace '[^A-Za-z0-9_\-]+', '_')
    $logPath = Join-Path $RepoRoot $logRel
    $tmpRunScript = Join-Path $reproDir ("tmp_run_{0:D3}.ps1" -f $idx)

    Write-Host "[run] ($idx/$($rows.Count)) sector=$($row.sector) runner=$runner"

    if (-not (Test-Path -LiteralPath (Split-Path -Parent $logPath))) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $logPath) -Force | Out-Null
    }
    Set-Content -LiteralPath $logPath -Value @("[run] index=$idx", "[run] sector=$($row.sector)", "[run] runner=$runner", "[run] command=$($row.command -replace "`r?`n", ' ')", '') -Encoding UTF8

    $notes = New-Object System.Collections.Generic.List[string]
    $expected = @(Get-ExpectedOutputs -Command $row.command)
    $datasetPaths = @(Get-DatasetPaths -Command $row.command)
    $datasetSpec = Get-DatasetSpec -DatasetPaths $datasetPaths
    $dataCheck = Test-DataOk -DatasetPaths $datasetPaths -AllowlistPatterns $allowPatterns -RepoRoot $RepoRoot
    $dataOk = $dataCheck.data_ok
    $dataNotes = $dataCheck.data_notes
    if (-not [string]::IsNullOrWhiteSpace($dataNotes)) {
        $notes.Add("data=$dataNotes")
    }

    $result = Run-CommandWithTimeout -Command $row.command -RepoRoot $RepoRoot -LogPath $logPath -TimeoutSec $PerCommandTimeoutSec -TmpScriptPath $tmpRunScript

    if (Test-Path -LiteralPath $tmpRunScript) {
        Remove-Item -LiteralPath $tmpRunScript -Force -ErrorAction SilentlyContinue
    }

    $runOk = 'NO'

    if ($result.timed_out) {
        $notes.Add("timeout_sec=$PerCommandTimeoutSec")
        $notes.Add('exit_code=124')
    }
    elseif ($result.exit_code -ne 0) {
        $notes.Add("exit_code=$($result.exit_code)")
    }
    else {
        $missing = New-Object System.Collections.Generic.List[string]
        if ($expected.Count -eq 0) {
            $runOk = 'YES'
            $notes.Add('no_explicit_output_flags')
        }
        else {
            foreach ($e in $expected) {
                $checkPath = Join-Path $RepoRoot $e
                if ($e.Contains('*')) {
                    $hits = @(Get-ChildItem -Path $checkPath -File -ErrorAction SilentlyContinue)
                    if ($hits.Count -eq 0) {
                        $missing.Add($e)
                    }
                }
                else {
                    if (-not (Test-Path -LiteralPath $checkPath)) {
                        $missing.Add($e)
                    }
                }
            }

            if ($missing.Count -eq 0) {
                $runOk = 'YES'
            }
            else {
                $notes.Add('missing_outputs=' + ($missing -join '|'))
            }
        }
    }

    $status = if ($runOk -eq 'YES') { 'PASS' } else { 'FAIL' }
    $verdictPass = Infer-VerdictPassFromLog -LogPath $logPath -RunOk $runOk -DataOk $dataOk

    $markerLines = @()
    if (Test-Path -LiteralPath $logPath) {
        $markerLines = @(Select-String -Path $logPath -Pattern '(?i)verdict|summary|chi2|pass|fail' -ErrorAction SilentlyContinue | Select-Object -First 2)
    }
    if ($markerLines.Count -gt 0) {
        $markers = $markerLines | ForEach-Object { $_.Line.Trim() }
        $notes.Add('markers=' + (($markers -join ' || ') -replace ',', ';'))
    }

    $summary.Add([pscustomobject]@{
        run_index = $idx
        sector = $row.sector
        runner = $runner
        dataset = $datasetSpec
        command = ($row.command -replace "`r?`n", ' ')
        expected_outputs = ($expected -join ';')
        run_ok = $runOk
        data_ok = $dataOk
        verdict_pass = $verdictPass
        status = $status
        data_notes = $dataNotes
        notes = ($notes -join ';')
        log_file = $logRel
    })

    $summary | Export-Csv -LiteralPath $summaryPath -NoTypeInformation -Encoding UTF8
}

$runOkCount = @($summary | Where-Object { $_.run_ok -eq 'YES' }).Count
$dataOkCount = @($summary | Where-Object { $_.data_ok -eq 'YES' }).Count
$verdictYesCount = @($summary | Where-Object { $_.verdict_pass -eq 'YES' }).Count
$verdictNoCount = @($summary | Where-Object { $_.verdict_pass -eq 'NO' }).Count
$verdictUnknownCount = @($summary | Where-Object { $_.verdict_pass -eq 'UNKNOWN' }).Count

Write-Host "[run] Summary written: $summaryPath"
Write-Host "[run] RUN_OK=$runOkCount/$($summary.Count) DATA_OK=$dataOkCount/$($summary.Count)"
Write-Host "[run] VERDICT_PASS YES=$verdictYesCount NO=$verdictNoCount UNKNOWN=$verdictUnknownCount"
