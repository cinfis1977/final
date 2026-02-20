# New Master Equation With Gauge Structure (Repro)

This repository is a reproducibility bundle for multi-sector prereg-style runs across:

- `EM` (LEP Bhabha/mumu)
- `WEAK` (NOvA/MINOS/T2K-linked runs)
- `STRONG` (sigma_tot, rho, and rho-from-dispersion checks)
- `DM` (SPARC holdout CV runs)
- `LIGO` (pattern-generation runs)

It is organized to run command batches, capture logs, and generate summary/verdict reports under `repro/`.

## Quickstart (Windows PowerShell)

1. Create and activate a virtual environment (optional, but recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies you need for your environment.
`requirements.txt` is currently a placeholder, so install the packages required by your selected scripts.

3. Run the full verdict command set:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1
```

4. Generate reports and strong-sector figure:

```powershell
python .\tools\make_repro_report.py
python .\tools\verdict_group_eval.py
python .\tools\make_fig_strong_deltachi2.py
```

5. Review outputs:

- `repro/run_summary.csv`
- `repro/REPORT.md`
- `repro/verdict_groups.csv`
- `repro/REPORT_VERDICT.md`
- `repro/figs/strong_delta_chi2.png`

## Useful Run Options

Run only a subset of commands (by index from `tools/verdict_commands.txt`):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1 -StartIndex 1 -EndIndex 5
```

Adjust per-command timeout (default is 1800s):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1 -PerCommandTimeoutSec 3600
```

Append to existing `repro/run_summary.csv` instead of overwriting:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1 -AppendSummary
```

## Data Sync Helper

If you maintain a separate working tree and want to copy inputs/scripts into this repro repo, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_repo.ps1 -WorkingRoot "<source-root>"
```

This updates copied files and writes `repro/copied_manifest.txt`.

## Repository Layout

```text
data/           Input datasets (HEPData, GW, SPARC, etc.)
figs/           Project figures
out/            Run outputs grouped by sector
paper/          Paper-facing notes
protocol/       Tolerance and protocol docs
repro/          Generated run summaries, logs, reports, and repro figures
runners/        Runner wrappers
scripts/        Utility and figure scripts
tools/          Main orchestration/report scripts (run_verdict, sync, eval)
```

## Main Control Files

- `tools/verdict_commands.txt`: batch commands executed by `run_verdict.ps1`
- `tools/data_allowlist.txt`: allowlisted data paths used in data checks
- `protocol/tolerances.json`: protocol tolerance configuration

## Notes

- This repo intentionally contains both inputs and generated outputs for reproducibility.
- `.gitignore` is configured to ignore local caches/temp artifacts and helper clone folders.
