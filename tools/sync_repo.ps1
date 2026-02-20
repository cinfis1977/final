param(
    [string]$WorkingRoot = "C:\Dropbox\projects\new_master_equation_with_gauge_structure_test",
    [string]$RepoRoot = "",
    [string]$CommandsFile = "",
    [switch]$CopyOutTree
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
}

if ([string]::IsNullOrWhiteSpace($CommandsFile)) {
    $CommandsFile = Join-Path $RepoRoot 'tools\verdict_commands.txt'
}

$excludeDirs = @('venv', '.venv', '__pycache__', '.git', 'node_modules')

function Normalize-RelPath {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) { return $null }
    $p = $PathValue.Trim().Trim('"').Trim("'")
    if ($p.StartsWith('.\\') -or $p.StartsWith('./')) { $p = $p.Substring(2) }
    $p = $p -replace '/', '\\'
    return $p
}

function Resolve-SourceFile {
    param(
        [Parameter(Mandatory = $true)][string]$WorkingRoot,
        [Parameter(Mandatory = $true)][string]$RelPath
    )

    $direct = Join-Path $WorkingRoot $RelPath
    if (Test-Path -LiteralPath $direct -PathType Leaf) {
        return $direct
    }

    $leaf = Split-Path -Leaf $RelPath
    if ([string]::IsNullOrWhiteSpace($leaf)) {
        return $null
    }

    $candidates = @(Get-ChildItem -Path $WorkingRoot -Recurse -File -Filter $leaf -ErrorAction SilentlyContinue)
    if ($candidates.Count -eq 0) {
        return $null
    }

    $wantedParts = @((Normalize-RelPath -PathValue $RelPath).Split('\\') | Where-Object { $_ })
    $best = $null
    $bestScore = [int]::MinValue

    foreach ($c in $candidates) {
        $candidateRel = $c.FullName.Substring($WorkingRoot.Length).TrimStart('\\')
        $score = 0

        foreach ($part in $wantedParts) {
            if ($candidateRel -like "*$part*") {
                $score += 4
            }

            if ($part -match '^(?<base>.+)_ins\d+$') {
                $base = $Matches['base']
                if ($candidateRel -like "*$base*") {
                    $score += 3
                }
            }
        }

        if ($candidateRel -like 'data\\hepdata\\*') { $score += 4 }
        if ($candidateRel -like 'data\\*') { $score += 2 }
        if ($candidateRel -like 'downloads\\*') { $score -= 2 }

        $depth = ($candidateRel.Split('\\').Count)
        $score -= $depth

        if ($score -gt $bestScore) {
            $bestScore = $score
            $best = $c.FullName
        }
    }

    return $best
}
function Invoke-RoboDirCopy {
    param(
        [Parameter(Mandatory = $true)][string]$SourceDir,
        [Parameter(Mandatory = $true)][string]$DestDir
    )

    if (-not (Test-Path -LiteralPath $SourceDir)) {
        Write-Warning "Source directory not found: $SourceDir"
        return
    }

    $args = @(
        $SourceDir,
        $DestDir,
        '/E',
        '/R:1',
        '/W:1',
        '/MT:8',
        '/NFL',
        '/NDL',
        '/NJH',
        '/NJS',
        '/NP',
        '/XD'
    ) + $excludeDirs

    & robocopy @args | Out-Null
    $code = $LASTEXITCODE
    if ($code -ge 8) {
        throw "robocopy failed for $SourceDir -> $DestDir (exit code $code)"
    }
}

function Invoke-RoboFileCopy {
    param(
        [Parameter(Mandatory = $true)][string]$SourceFile,
        [Parameter(Mandatory = $true)][string]$DestFile
    )

    if (-not (Test-Path -LiteralPath $SourceFile)) {
        return $false
    }

    $srcDir = Split-Path -Parent $SourceFile
    $name = Split-Path -Leaf $SourceFile
    $dstDir = Split-Path -Parent $DestFile

    if (-not (Test-Path -LiteralPath $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }

    $args = @(
        $srcDir,
        $dstDir,
        $name,
        '/R:1',
        '/W:1',
        '/NFL',
        '/NDL',
        '/NJH',
        '/NJS',
        '/NP'
    )

    & robocopy @args | Out-Null
    $code = $LASTEXITCODE
    if ($code -ge 8) {
        throw "robocopy failed for file $SourceFile -> $DestFile (exit code $code)"
    }

    return $true
}

function Get-Commands {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Warning "Commands file not found: $Path"
        return @()
    }

    $lines = Get-Content -LiteralPath $Path
    $commands = New-Object System.Collections.Generic.List[string]
    $current = New-Object System.Collections.Generic.List[string]

    foreach ($line in $lines) {
        $trim = $line.Trim()

        if ($trim -match '^```') { continue }
        if ($trim -match '^#' -or $trim -match '^>' -or $trim -eq '---') { continue }

        if ($trim -match '^(py|python)(\s|$)') {
            if ($current.Count -gt 0) {
                $commands.Add(($current -join "`n").Trim())
                $current.Clear()
            }
            $current.Add($trim)
            if (-not $trim.EndsWith('`')) {
                $commands.Add(($current -join "`n").Trim())
                $current.Clear()
            }
            continue
        }

        if ($current.Count -gt 0) {
            if ($trim -eq '') {
                if ($current.Count -gt 0 -and -not $current[$current.Count - 1].Trim().EndsWith('`')) {
                    $commands.Add(($current -join "`n").Trim())
                    $current.Clear()
                }
                continue
            }

            $current.Add($trim)

            if (-not $trim.EndsWith('`')) {
                $commands.Add(($current -join "`n").Trim())
                $current.Clear()
            }
        }
    }

    if ($current.Count -gt 0) {
        $commands.Add(($current -join "`n").Trim())
    }

    return $commands
}

$repoTools = Join-Path $RepoRoot 'tools'
$reproDir = Join-Path $RepoRoot 'repro'
New-Item -ItemType Directory -Path $repoTools -Force | Out-Null
New-Item -ItemType Directory -Path $reproDir -Force | Out-Null

Write-Host "[sync] Copying data/ with robocopy /E"
Invoke-RoboDirCopy -SourceDir (Join-Path $WorkingRoot 'data') -DestDir (Join-Path $RepoRoot 'data')

if ($CopyOutTree.IsPresent) {
    Write-Host "[sync] Copying out/ with robocopy /E"
    Invoke-RoboDirCopy -SourceDir (Join-Path $WorkingRoot 'out') -DestDir (Join-Path $RepoRoot 'out')
}

$neededRelPaths = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
$commands = Get-Commands -Path $CommandsFile

$inputFlags = @(
    'pack',
    'data',
    'baseline_csv',
    'points_csv',
    'h1_hdf5',
    'l1_hdf5',
    'v1_hdf5',
    'model_csv',
    'sigma_data',
    'rho_data',
    'cv_csv',
    'fit_summary_json'
)

foreach ($cmd in $commands) {
    $scriptMatch = [regex]::Match($cmd, '(?i)(?:^|\s)(?:\.\\|\./)?[^\s"'']+\.py(?:\s|$)')
    if ($scriptMatch.Success) {
        $rawScript = $scriptMatch.Value.Trim()
        $rel = Normalize-RelPath -PathValue $rawScript
        if ($rel) { [void]$neededRelPaths.Add($rel) }
    }

    foreach ($flag in $inputFlags) {
        $pattern = '(?i)--' + [regex]::Escape($flag) + '\s+("[^"]+"|\S+)'
        $flagMatches = [regex]::Matches($cmd, $pattern)
        foreach ($m in $flagMatches) {
            $rawValue = $m.Groups[1].Value
            $parts = $rawValue.Split(',')
            foreach ($part in $parts) {
                $rel = Normalize-RelPath -PathValue $part
                if ($rel) {
                    [void]$neededRelPaths.Add($rel)
                }
            }
        }
    }
}

$copiedRel = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)

$dataDst = Join-Path $RepoRoot 'data'
if (Test-Path -LiteralPath $dataDst) {
    Get-ChildItem -LiteralPath $dataDst -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($RepoRoot.Length).TrimStart('\\')
        [void]$copiedRel.Add($rel)
    }
}

if ($CopyOutTree.IsPresent) {
    $outDst = Join-Path $RepoRoot 'out'
    if (Test-Path -LiteralPath $outDst) {
        Get-ChildItem -LiteralPath $outDst -Recurse -File | ForEach-Object {
            $rel = $_.FullName.Substring($RepoRoot.Length).TrimStart('\\')
            [void]$copiedRel.Add($rel)
        }
    }
}

$missingRel = New-Object System.Collections.Generic.List[string]

foreach ($rel in ($neededRelPaths | Sort-Object)) {
    if ([string]::IsNullOrWhiteSpace($rel)) { continue }

    $src = Resolve-SourceFile -WorkingRoot $WorkingRoot -RelPath $rel
    if (-not $src) {
        Write-Warning "Missing source file: $rel"
        $missingRel.Add($rel)
        continue
    }

    $dst = Join-Path $RepoRoot $rel
    $copied = Invoke-RoboFileCopy -SourceFile $src -DestFile $dst
    if ($copied) {
        if ((Normalize-RelPath -PathValue ($src.Substring($WorkingRoot.Length).TrimStart('\\'))) -ne (Normalize-RelPath -PathValue $rel)) {
            Write-Host "[sync] Fallback source used for $rel -> $src"
        }
        $cleanRel = $dst.Substring($RepoRoot.Length).TrimStart('\\')
        [void]$copiedRel.Add($cleanRel)
    }
}

$manifestPath = Join-Path $reproDir 'copied_manifest.txt'
$manifestLines = New-Object System.Collections.Generic.List[string]
$manifestLines.Add("# Copied Manifest")
$manifestLines.Add("timestamp_utc=$(Get-Date -Format o)")
$manifestLines.Add("working_root=$WorkingRoot")
$manifestLines.Add("repo_root=$RepoRoot")
$manifestLines.Add("commands_file=$CommandsFile")
$manifestLines.Add("")
$manifestLines.Add("copied_files:")

foreach ($f in ($copiedRel | Sort-Object)) {
    $manifestLines.Add($f)
}

if ($missingRel.Count -gt 0) {
    $manifestLines.Add("")
    $manifestLines.Add("missing_files:")
    foreach ($m in ($missingRel | Sort-Object)) {
        $manifestLines.Add($m)
    }
}

Set-Content -LiteralPath $manifestPath -Value $manifestLines -Encoding UTF8
Write-Host "[sync] Manifest written: $manifestPath"
Write-Host "[sync] Total files listed: $($copiedRel.Count)"
if ($missingRel.Count -gt 0) {
    Write-Warning "[sync] Missing files not found in working tree: $($missingRel.Count)"
}


