param(
    [string]$OutRoot = "out\\pass_runs",
    [int]$Kfold = 2,
    [int]$Seed = 2026
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    if (-not $PSScriptRoot) {
        throw "Unable to resolve script root (PSScriptRoot is empty)."
    }
    return (Resolve-Path (Join-Path $PSScriptRoot "..") ).Path
}

function Write-TextFileUtf8([string]$Path, [string]$Content) {
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Content | Set-Content -Path $Path -Encoding UTF8
}

function Invoke-LoggedNative(
    [string]$Name,
    [string]$FilePath,
    [string[]]$ArgList,
    [string]$RunDir,
    [string]$CommandsMd
) {
    $stdoutPath = Join-Path $RunDir ("{0}.stdout.txt" -f $Name)
    $stderrPath = Join-Path $RunDir ("{0}.stderr.txt" -f $Name)
    $summaryPath = Join-Path $RunDir ("{0}.summary.json" -f $Name)
    $logMdPath = Join-Path $RunDir ("{0}.log.md" -f $Name)

    if ($null -eq $ArgList) {
        $ArgList = @()
    }
    $ArgList = @($ArgList | Where-Object { $_ -ne $null })

    $argLine = (($ArgList | ForEach-Object { if ($_ -match "\s") { '"' + $_ + '"' } else { $_ } }) -join " ")
    if ($argLine) {
        $cmdLine = $FilePath + " " + $argLine
    } else {
        $cmdLine = $FilePath
    }

    Add-Content -Path $CommandsMd -Encoding UTF8 -Value ("- {0}`n  - cmd: {1}`n" -f $Name, $cmdLine)

    $start = Get-Date

    if ($argLine) {
        $p = Start-Process -FilePath $FilePath -ArgumentList $argLine -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    } else {
        $p = Start-Process -FilePath $FilePath -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    }

    $rc = [int]$p.ExitCode

    $end = Get-Date

    $summary = [ordered]@{
        name = $Name
        cwd = (Get-Location).Path
        cmd = $cmdLine
        exe = $FilePath
        args = $ArgList
        start_utc = $start.ToUniversalTime().ToString("o")
        end_utc = $end.ToUniversalTime().ToString("o")
        duration_sec = [math]::Round(($end - $start).TotalSeconds, 3)
        exit_code = [int]$rc
        stdout_path = $stdoutPath
        stderr_path = $stderrPath
    }

    ($summary | ConvertTo-Json -Depth 10) | Set-Content -Path $summaryPath -Encoding UTF8

    $stdoutText = ""
    if (Test-Path $stdoutPath) { $stdoutText = Get-Content -Path $stdoutPath -Raw }
    $stderrText = ""
    if (Test-Path $stderrPath) { $stderrText = Get-Content -Path $stderrPath -Raw }
    $summaryJsonText = Get-Content -Path $summaryPath -Raw

    $stdoutText = [string]$stdoutText
    $stderrText = [string]$stderrText
    $summaryJsonText = [string]$summaryJsonText

    $logMd = @(
        "# $Name",
        "",
        "## Command",
        "",
        '```',
        $cmdLine,
        '```',
        "",
        "## Stdout",
        "",
        '```',
        $stdoutText,
        '```',
        "",
        "## Stderr",
        "",
        '```',
        $stderrText,
        '```',
        "",
        "## Summary JSON",
        "",
        '```json',
        $summaryJsonText,
        '```',
        ""
    ) -join "`n"

    Write-TextFileUtf8 -Path $logMdPath -Content $logMd

    Add-Content -Path $CommandsMd -Encoding UTF8 -Value ("  - exit_code: {0}`n" -f $rc)

    if ($rc -ne 0) {
        throw "Command failed ($Name) rc=$rc. See: $logMdPath"
    }
}

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$runDir = Join-Path $repoRoot (Join-Path $OutRoot $timestamp)
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$latestPath = Join-Path $repoRoot (Join-Path $OutRoot "_LATEST_RUN.txt")
Write-TextFileUtf8 -Path $latestPath -Content $runDir

$commandsMd = Join-Path $runDir "run_commands.md"
Write-TextFileUtf8 -Path $commandsMd -Content ("# PASS run commands`n`n- timestamp_utc: {0}`n- run_dir: {1}`n`n" -f (Get-Date).ToUniversalTime().ToString("o"), $runDir)

# Environment snapshot
$pythonExe = Join-Path $repoRoot ".venv\\Scripts\\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$envJsonPath = Join-Path $runDir "env.summary.json"
$envMdPath = Join-Path $runDir "env.log.md"

$gitHead = ""
try {
    $gitHead = (git rev-parse HEAD 2>$null)
} catch {
    $gitHead = ""
}

$pyVersion = ""
$pyExecutable = ""
try {
    $pyExecutable = & $pythonExe -c "import sys; print(sys.executable)"
    $pyVersion = & $pythonExe -c "import sys; print(sys.version.replace('\\n',' '))"
} catch {
    $pyExecutable = ""
    $pyVersion = ""
}

$envSummary = [ordered]@{
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
    repo_root = $repoRoot
    run_dir = $runDir
    git_head = ($gitHead | Out-String).Trim()
    os = [System.Environment]::OSVersion.VersionString
    powershell_version = ($PSVersionTable.PSVersion.ToString())
    python_exe = ($pyExecutable | Out-String).Trim()
    python_version = ($pyVersion | Out-String).Trim()
}
($envSummary | ConvertTo-Json -Depth 6) | Set-Content -Path $envJsonPath -Encoding UTF8

$envMd = @(
    "# Environment snapshot",
    "",
    '```json',
    (Get-Content -Path $envJsonPath -Raw).TrimEnd(),
    '```',
    ""
) -join "`n"
Write-TextFileUtf8 -Path $envMdPath -Content $envMd

# Runs
Invoke-LoggedNative -Name "pytest_integration_artifacts_mastereq_tests" -FilePath $pythonExe -ArgList @("-m","pytest","-q","integration_artifacts/mastereq/tests") -RunDir $runDir -CommandsMd $commandsMd
Invoke-LoggedNative -Name "pytest_mastereq_tests" -FilePath $pythonExe -ArgList @("-m","pytest","-q","mastereq/tests") -RunDir $runDir -CommandsMd $commandsMd

Invoke-LoggedNative -Name "dm_paper_run" -FilePath $pythonExe -ArgList @("run_dm_paper_run.py","--out_dir","out\\dm_paper","--kfold",$Kfold.ToString(),"--seed",$Seed.ToString()) -RunDir $runDir -CommandsMd $commandsMd
Invoke-LoggedNative -Name "em_paper_run" -FilePath $pythonExe -ArgList @("run_em_paper_run.py","--out_dir","out\\em_paper") -RunDir $runDir -CommandsMd $commandsMd
Invoke-LoggedNative -Name "strong_c5a_paper_run" -FilePath $pythonExe -ArgList @("run_strong_c5a_paper_run.py","--out_dir","out\\strong_c5a") -RunDir $runDir -CommandsMd $commandsMd

$finalMdPath = Join-Path $runDir "PASS_RUN_REPORT.md"
$finalMd = @(
    "# PASS run report",
    "",
    "- run_dir: $runDir",
    "- latest_pointer: $latestPath",
    "",
    "## Outputs",
    "",
    "- env: env.log.md / env.summary.json",
    "- commands: run_commands.md",
    "- logs: *.log.md (each includes embedded Summary JSON)",
    "",
    "## Produced artifact dirs",
    "",
    "- out\\dm_paper",
    "- out\\em_paper",
    "- out\\strong_c5a",
    ""
) -join "`n"
Write-TextFileUtf8 -Path $finalMdPath -Content $finalMd

Write-Output ("PASS run complete. run_dir=" + $runDir)
