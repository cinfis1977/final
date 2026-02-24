# New Master Equation With Gauge Structure

This repository is a reproducibility workspace for a locked, cross-sector draft:
WEAK / EM / STRONG / DM / GW + mass spectrometry (real Bruker mzML addendum).

Scope note: `PASS` means not falsified under preregistered tests for the specific tested panels; it is not a universal proof.

## Current Paper Files (Active)

- **Canonical / stable names** (recommended for sharing):
  - `paper/paper_final.md` (should be the current locked draft)
  - `paper/paper_final.html` (render of the same)
- **Versioned locked snapshots** (historical, audit-friendly):
  - `paper/paper_LOCKED_mathfixed_v452_CHATRUNS_ONEFORALL_LIGOpatternonly__massspec_REALDATA_particlespecific.md`
  - `paper/paper_LOCKED_mathfixed_v452_massspec_REALDATA_particlespecific.html`
- Cube structure animation (HTML):
  - `paper/dual_cube_gauge_planes_animation.html`

## Legacy / Reference

- Legacy draft (historical wording):
  - `paper/paper_LOCKED_mathfixed_v442_CHATRUNS_ONEFORALL_LIGOpatternonly__QEDplaneTheta_massspec_REALDATA_particlespecific.md`
- Legacy reference text:
  - `paper/master_equation.md`

## Requirements

- Windows PowerShell 5.1+ or PowerShell 7+
- Python 3.10+ recommended
- `requirements.txt` currently has no pinned packages; dependencies are managed script-by-script

Optional environment setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Quickstart (Windows PowerShell)

Run locked verdict batch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1
```

Build summary artefacts:

```powershell
python .\tools\make_repro_report.py
python .\tools\verdict_group_eval.py
python .\tools\make_fig_strong_deltachi2.py
```

## Baselines and evaluation metrics (what “SM baseline” means here)

The phrase **“SM baseline”** is used in a _sector-specific_ sense. Not every panel is a literal “Standard Model fit” in the same way.

- **Weak (neutrino):** the baseline is the standard 3-flavor oscillation description evaluated with the sector’s chosen metric (typically Δχ² with a fixed convention). Some checks are “scan-free” (no parameter sweeps) and are compared to the corresponding baseline under the _same metric_.
- **EM (LEP Bhabha):** the baseline is the standard QED/Bhabha prediction for the same binned table (often via an imported baseline curve such as BHAGEN-derived tables). Evaluation is done on the same binned observable (e.g., χ² / residual structure).
- **Strong (σ_tot, ρ):** the baseline is the standard reference curve/table used in that runner (PDG/experiment tables and their standard parametrizations). The runner’s metric (Δχ² or residual score) is the authority.
- **GW (ringdown):** some runs are **sim-only** (internal consistency), while “real-compare” runs use GWOSC strain and compare against the chosen GR/null reference within that script’s metric.
- **DM (SPARC/RAR):** the baseline is the standard reference relation used in that runner (RAR/MOND-style or the declared baseline in the script). Again, the script’s metric is the authority.
- **Mass spectrometry (Bruker mzML):** this is **not an SM-vs-model fit**. The baseline is a frozen **do-nothing / no-correction reference** (legacy labels may say “SM” but it means baseline). The prereg verdict is based on locked, fit-free statistics (e.g., target-dependent p_success/MAD stability across holdout/third-arm).

**Takeaway:** Many panels are compared against a sector baseline under the same metric, but some panels are **internal consistency / null** tests. Use `repro/REPORT_VERDICT.md` and the runner logs as the authoritative definitions for each panel.

## Quick way to reproduce the PASS/TENSION/FAIL table

1. Run the verdict batch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1
```

2. Build reports:

```powershell
python .\tools\make_repro_report.py
python .\tools\verdict_group_eval.py
```

3. Read the final summary:

- `repro/REPORT_VERDICT.md` (human-readable verdict table)
- `repro/run_summary.csv` (per-command run log)

If you want to rerun only a subset, use `-StartIndex` / `-EndIndex` with the same command list `tools/verdict_commands.txt`.

## Mass spectrometry: where the mzML files go

mzML files are typically **not committed** to git due to size and licensing/data policies. To reproduce the mass-spec runs, you must:

- Place your Bruker/CompassXport mzML exports in a local folder (commonly under `data/`), **or**
- Set the mzML paths explicitly in the mass-spec runner commands you execute.

The paper section and runner examples use a “cyto_full” style folder convention (e.g., `data/cyto_full/*.mzML`), but the exact location is not required as long as the runner paths point to the files.

## Repro Entry Points

- Main verdict batch runner:
  - `tools/run_verdict.ps1`
- Command list consumed by verdict runner:
  - `tools/verdict_commands.txt`
- Curated manual command sets:
  - `verdict_reproducer_commands_v1.md`
  - `CODEX_FINAL_RUN_COMMANDS.md`
  - `CODEX_FINAL_RUN_COMMANDS_v2.txt`
- Data allowlist used by runner checks:
  - `tools/data_allowlist.txt`

## Useful Verdict Runner Options

Run only part of the command file:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1 -StartIndex 1 -EndIndex 5
```

Increase per-command timeout:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1 -PerCommandTimeoutSec 3600
```

Append to existing `repro/run_summary.csv`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1 -AppendSummary
```

## Mass-Spec Finalizer (good_ppm=3 prereg lock)

What it does: produces locked final verdict artefacts (JSON+MD) from already-generated run outputs.
It does not rerun mzML conversion or the multi-target analysis.

Runner path:

- `runners/particle_specific_finalize_from_runs_v1_0_DROPIN/RUN_finalize_particle_specific_goodppm3_lock_from_runs_v1_0.ps1`

Example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\runners\particle_specific_finalize_from_runs_v1_0_DROPIN\RUN_finalize_particle_specific_goodppm3_lock_from_runs_v1_0.ps1 `
  -PairB2Dir ".\out\particle_specific_sweep_goodppm_3_A1_B2" `
  -PairB3Dir ".\out\particle_specific_sweep_goodppm_3_A1_B3_holdout" `
  -ThirdArmDir ".\out\particle_specific_cytofull_A2_B3_good3" `
  -TargetsCsv ".\out\particle_specific_cytofull_A1_B2_direct\targets_used.csv" `
  -OutDir ".\out\particle_specific_final_goodppm3_lock"
```

Expected final artefacts:

- `out/particle_specific_final_goodppm3_lock/prereg_lock_and_final_verdict_goodppm3.json`
- `out/particle_specific_final_goodppm3_lock/FINAL_VERDICT_REPORT_goodppm3.md`

## Main Output Locations

- Sector outputs:
  - `out/WEAK/`
  - `out/EM/`
  - `out/STRONG/`
- Cross-sector/root outputs:
  - `out/`
  - root-level `out_*.csv` and `out_*.json`
- Audit outputs:
  - `out/md_audit/`
- Repro summaries:
  - `repro/run_summary.csv`
  - `repro/REPORT.md`
  - `repro/verdict_groups.csv`
  - `repro/REPORT_VERDICT.md`

## Data And Packaging Notes

Some datasets are intentionally duplicated across:

- repo root
- `data/hepdata/`
- sector-specific subfolders (for example `data/hepdata/em_bhabha_pack/`)

Use the paths referenced by `tools/verdict_commands.txt` as canonical for runs.

Large data files may not be tracked in git depending on your clone/source; verify local data availability before running full verdict batches.

## Repo Layout

```text
data/           datasets
figs/           figures
out/            produced outputs
paper/          paper drafts and notes
protocol/       run/test protocol docs
repro/          generated logs and reports
runners/        runner wrappers and drop-in utilities
scripts/        utility scripts
tools/          orchestration and report tools
```
