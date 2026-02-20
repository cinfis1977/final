# New Master Equation With Gauge Structure

This repository is the reproducibility workspace for the model documented in `paper/master_equation.md`.

## Source Of Truth

- Main model and physics narrative: `paper/master_equation.md`
- Current draft tag in that file: `2026-02-12 (v4_30)`
- Scope policy in that file: falsification-first prereg workflow

## Model Snapshot

The project implements one geometric modulation framework across:

- `WEAK` (NOvA, MINOS, T2K-linked)
- `STRONG` (sigma_tot, rho, dispersion bridge checks)
- `EM` (LEP Bhabha and mumu channels)
- `GW/LIGO` (pattern/basis generation in this repo snapshot)
- `DM` (SPARC holdout CV)

Core substrate summary from `paper/master_equation.md`:

- Lattice: cubic cells with a central bubble node and threaded links
- Fixed prereg geometry: `N_in=8`, `N_face=16`
- Dual thread rule:
  - `CT`: intra-cube, constant tension links
  - `RT`: inter-cube, distance-dependent links
- Junction plane stack roles:
  - `LP` ordering/lock
  - `RL` route/localization addressing
  - `TT2` phase gate `g(phi)`
  - `EM/QED` stiffness conditioning
- Weak-sector one-line evolution:
  - `d rho / dL = -i K(E)[H_vac + H_mat + H_geo, rho] + sum_j Gamma_j D[L_j] rho`
- Cross-sector postulate:
  - one shared kernel
  - sector-specific bridge operators to observables

## Locked Prereg Discipline

- Run scan-free fixed points for verdict runs.
- Use `A=0` as the NULL control when defined.
- Interpret PASS as "not falsified under the prereg test definition", not proof of truth.

One-for-all locked base from `paper/master_equation.md`:

- `A_phys=-0.003`
- `alpha_phys=0.001`
- Fixed sector map:
  - `STRONG`: `A=-0.003`
  - `WEAK`: `A=-0.002`, `alpha=0.7`
  - `DM`: `A=0.1778279410038923`, `alpha=0.001`
  - `EM`: `A=+100000`, `alpha=7.5e-05` (with sign-flip control where applicable)

## Quickstart (Windows PowerShell)

1. Optional environment setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install required packages for your chosen scripts.
`requirements.txt` is currently a placeholder.

3. Run prereg command batch:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1
```

4. Build reports:

```powershell
python .\tools\make_repro_report.py
python .\tools\verdict_group_eval.py
python .\tools\make_fig_strong_deltachi2.py
```

5. Check outputs:

- `repro/run_summary.csv`
- `repro/REPORT.md`
- `repro/verdict_groups.csv`
- `repro/REPORT_VERDICT.md`
- `repro/figs/strong_delta_chi2.png`

## Useful Options

Run a subset:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1 -StartIndex 1 -EndIndex 5
```

Longer timeout:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1 -PerCommandTimeoutSec 3600
```

Append to existing summary:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1 -AppendSummary
```

## Data Sync Helper

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\sync_repo.ps1 -WorkingRoot "<source-root>"
```

This writes `repro/copied_manifest.txt` after syncing.

## Key Files

- `tools/verdict_commands.txt`: command list executed by `run_verdict.ps1`
- `tools/data_allowlist.txt`: allowlist used by data checks
- `protocol/tolerances.json`: tolerance settings
- `paper/master_equation.md`: full model document

## Repo Layout

```text
data/           datasets
figs/           figures
out/            produced outputs
paper/          model and paper notes
protocol/       run/test protocol docs
repro/          generated logs and reports
runners/        runner wrappers
scripts/        utility scripts
tools/          orchestration and report tools
```
