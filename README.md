# New Master Equation With Gauge Structure

This repository is a reproducibility workspace for a locked, cross-sector draft:
WEAK / EM / STRONG / DM / GW + mass spectrometry (real Bruker mzML addendum).

Scope note: `PASS` means not falsified under preregistered tests for the specific tested panels; it is not a universal proof.

## Data provenance (required reading)

This repo contains a mix of:

- **Real experimental / observational data** (e.g., Bruker mzML exports; LEP Bhabha tables; GWOSC strain; SPARC galaxy points)
- **Real data, cleaned/condensed for runners** (e.g., `*_clean_for_runner.csv` tables)
- **Synthetic / harness data** (used only for pipeline/mechanism tests; not for real-world claims)
- **Digitized-from-figure data** (if ever used, it must be explicitly labeled)

**Rule:** any dataset used by a runner must be traceable to (i) an origin and (ii) a raw-to-processed chain. If a dataset is digitized from a PDF figure, the paper/figure and digitizer settings must be recorded.

### Provenance matrix (reader-facing)

| Sector | What is used in this repo | Real / synthetic | Where it lives (paths) | How it was produced / notes |
|---|---|---|---|---|
| **Weak (neutrino)** | Oscillation pack JSONs (NOvA / MINOS / T2K / Daya Bay) | **Mixed** | `nova_channels.json` (and combined packs such as `t2k_nova_combined.json`) | NOvA pack is explicitly described as real public release (`ROOT -> CSV -> JSON`). Other packs may be simplified/spec-generated; the pack `source` metadata should be treated as authority. If T2K spectra are created via figure digitization, that must be labeled as digitized. |
| **EM (LEP Bhabha)** | Binned dσ/dcosθ table + pack JSON + imported baseline curve | **Real data** | `data/hepdata/em_bhabha_pack/lep_bhabha_table18_clean.csv`, `data/hepdata/em_bhabha_pack/lep_bhabha_pack.json`, baselines like `bhagen_cos09_v4_baseline_L0_Sp1.csv` | Runner logs show the pack + clean table are used as the data source, and baselines are imported from BHAGEN mapping sweeps (no figure digitization indicated). |
| **Strong (σ_tot, ρ)** | Energy-axis panels using cleaned runner tables; experiment-only splits | **Real data (table form)** | `data/hepdata/pdg_sigma_tot_clean_for_runner.csv` and derived subsets like `data/hepdata/pdg_sigma_tot_TOTEM_only.csv` | The workflow creates experiment-only CSVs from the cleaned runner table (pandas filter). No figure digitization indicated; table is treated as machine-readable `clean_for_runner` input. |
| **GW (ringdown)** | GWOSC open strain (H1/L1/V1 HDF5) + compare pipeline; also synthetic model CSV outputs | **Mixed** | `data/gw/*.hdf5` (downloaded), `out/LIGO_MIN/*_sim.csv` (sim) | When `-CompareRealData` is enabled, scripts fetch GWOSC open data via `gwosc/requests/h5py` and write `*_realcompare.json`. Without it, runs are sim-only. |
| **DM (SPARC/RAR)** | SPARC/RAR points table for likelihood / CV | **Real observational (compiled)** | `data/sparc/sparc_points.csv` | The paper and runners refer to a single consolidated points table. For strict provenance, add a short note naming upstream SPARC distribution and the conversion script (raw -> CSV). |
| **Mass spectrometry** | Bruker/CompassXport mzML full-scan runs + fit-free per-scan pipeline + prereg lock verdict artefacts | **Real data** | Local mzMLs (not usually in git); outputs under `out/particle_specific_final_goodppm3_lock/` | mzML exports are real instrument data (CompassXport in metadata). The analysis produces per-scan mass estimates + ion-load proxy `g`, then a locked multi-target test with `good_ppm=3` yields prereg PASS artefacts (JSON+MD). |

### PDF/figure digitization policy (if used)

If any dataset is created by digitizing a paper figure:

- Store it under: `data/digitized/<paper_shortname>/<figure_id>.csv`
- Include a sidecar: `data/digitized/<paper_shortname>/<figure_id>.meta.json` with:
  - bibliographic reference (title/DOI/year)
  - figure/panel identifier
  - digitizer tool + settings (axes calibration points, interpolation, export format)
  - units + any transformations
- In the paper/README, mark it clearly as: **DIGITIZED FROM FIGURE (NOT MACHINE-READABLE RELEASE)**.

## Current Paper Files (Active)

- Active locked draft (Markdown):
  - `paper/paper_final.md`
- Active locked render (HTML):
  - `paper/paper_final.html`
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
