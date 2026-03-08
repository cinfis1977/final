# New Master Equation With Gauge Structure

> Current status: WEAK / STRONG / DM / FT-ICR MS / LIGO = performance pass; EM = pass; Entanglement (CHSH) and Photon (birefringence/decay) = not scored here (audit / bridge lines only; first-principles dynamic closure still open).

This repository is a reproducibility workspace for a locked, cross-sector draft spanning:

- **WEAK** (T2K / NOvA / MINOS)
- **EM** (LEP Bhabha / MuMu)
- **STRONG**
- **DM / SPARC**
- **GW / LIGO ringdown**
- **FT-ICR target-specific mass spectrometry**
- **Entanglement / Bell audit**
- **Photon / birefringence bridge**

## Status semantics (important)

This repository now uses the following status labels:

- **performance pass**  
  Use this **only** when a sector has a locked performance-style result under the project’s current prereg / evaluation convention.

- **pass**  
  Use this when a sector is accepted as **non-failing / parity-preserving** in the current repo sense, but **not** promoted to a performance-pass sector.  
  Current intended use: **EM**, where the tested branch is treated as compatible / acceptable under the declared baseline reading, but does **not** claim a positive performance superiority result.

- **not established**  
  Use this when a tested branch does **not** currently establish either a usable pass reading or a positive performance result.

- **audit-positive**  
  Use this for sectors where the repo has a functioning audit / diagnostic / data-side result, but **not** a first-principles dynamic performance closure.

- **not scored here**  
  Use this when a sector is intentionally outside the current performance scoreboard.

These labels are **not** universal proof claims. They are repository-local status labels tied to the current locked evaluation structure.

## Current project snapshot

### Performance-pass sectors
The current performance-pass line is:

- **WEAK**
- **STRONG**
- **DM**
- **GW / LIGO**
- **FT-ICR target-specific mass spectrometry**

### Pass (non-performance-pass) sector
- **EM**

### Audit / bridge sectors (not performance-scored yet)
- **Entanglement** — audit-positive, **not scored here**
- **Photon / birefringence** — bridge/audit functioning, **not scored here**

## What is established right now

### WEAK
Weak-sector locked runs currently support a positive performance result under the project’s current evaluation convention.

### STRONG
Strong-sector locked runs currently support a net-positive performance result, with mixed internal branch quality that should still be described honestly in-paper.

### DM
Current DM reruns support a positive locked criterion.

### GW / LIGO
The canonical exact GW branch is locally re-confirmed as a passing performance result on the current exact run path.

### FT-ICR mass spectrometry
This remains a **target-specific / cross-domain robustness** result, not a fundamental-particle claim. The locked prereg branch is treated as a performance-pass sector under the repo’s current scoreboard.

### EM
EM is currently treated as **pass** in the repo-local status sense: the tested branch is accepted as a non-failing / parity-preserving line relative to the declared baseline reading, but it is **not** promoted to a **performance pass** because no positive performance-superiority result is being claimed.

### Entanglement
The repo now has three distinct executable layers:

1. **CHSH/NIST audit wrapper**  
   Current executable wrapper reports observed \(|S| = 2.455041357825164\) against a **decorrelation surrogate null** centered near 0.  
   This is a functioning audit, **not** a Bell-bound significance proof.

2. **Preregistered “memory-statistic” diagnostic**  
   Current rerun reports:
   - `z_p95 = 1.9363439433203153`
   - `z_worst = 1.9914293684831685`  
   This is a diagnostic / empirical-template holdout test, **not** a first-principles Bell derivation.

3. **Data-side CH/Eberhard audit**  
   The **fully re-verified paper-facing branch** is currently the `slots 4–8` branch, where:
   - `01_11 -> J = 550`
   - `02_54 -> J = 176`
   - `03_43 -> J = 151`

   This is the strongest current data-side Bell-inequality result in the repo.  
   It is **audit-positive**, but it is **not yet** a first-principles dynamic performance closure.

### Photon / birefringence
Photon currently has a working bridge / falsification layer based on the accumulation observable:

\[
\alpha(z) = \beta I(z)
\]

with locked accumulation-law and sky-fold style tests producing **null-compatible** outputs.  
This establishes a functioning bridge observable and audit layer, **not** a first-principles propagation closure.

## What is *not* yet established

### Entanglement
The repo does **not** yet have a locked first-principles Bell forward model that:

- defines \(H_s\) and \(\mathcal{D}_s\),
- generates model-side \(J_{\mathrm{model}}\) or \(E^{\mathrm{model}}_{ab}\),
- runs no-fit multi-run / multi-window scorecards,
- and closes the Bell sector as a dynamic performance-pass result.

### Photon
The repo does **not** yet have a substrate-generated first-principles photon propagation model that replaces bridge-only \(\alpha(z)=\beta I(z)\) usage with a locked forward theory prediction.

---

## Current Paper Files (Active)

- **Canonical / stable names** (recommended for sharing):
  - `paper/paper_final.md`
  - `paper/paper_final.html`

- **Versioned locked snapshots** (historical / audit-friendly):
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

## Performance-pass reproducibility (current scoreboard)

Canonical performance runbook:

- [paper/PERFORMANCE_RUNBOOK_20260305_UPDATED.md](paper/PERFORMANCE_RUNBOOK_20260305_UPDATED.md)

### Canonical run-command reference
For **all current reproducibility run commands across all sectors**, see:

- `verdict_reproducer_commands_master.md`

This is the single master command list for:
- WEAK
- STRONG
- EM
- DM
- GW / LIGO
- FT-ICR mass spectrometry
- Entanglement
- Photon

Use `paper/PERFORMANCE_RUNBOOK_20260305_UPDATED.md` for the current performance-runbook framing, and use `verdict_reproducer_commands_master.md` when you need the **full command reference**.

This runbook is normalized to this project layout (no `bundle/CODE` command paths):

- project root scripts: `./*.py`
- real datasets: `./data/*` and `./t2k_release_extract/*`
- run outputs: `./LOCAL_RUNS/*` and `./out/*`

### Sectors currently covered by the performance runbook
- WEAK
- STRONG
- EM
- DM
- MS
- LIGO

### Important note
- **EM is included in the runbook and is currently treated as pass, but not as a performance-pass sector.**
- **Entanglement and Photon are not current performance-pass sectors and should not be reported as such from this runbook.**


### Additional command catalog for entanglement / photon
A separate command catalog should be maintained for the current **audit / bridge / prereg** lines of Entanglement and Photon.

Recommended file:
- `verdict_reproducer_commands_v2_ENT_PHOTON_ADDED.md`

This catalog should include:
- CHSH / coincidence export / memory diagnostic commands,
- data-side CH/Eberhard J audit commands,
- photon accumulation / CMB / sky-fold prereg commands,

and should be kept **separate** from the main performance-pass runbook, because these sectors are currently **not scored here** and do not yet constitute first-principles dynamic performance closure.

## Integration equivalence evidence (paper-grade)

Deterministic golden-output regeneration + strict equivalence tests live under `integration_artifacts/`.

- Overview + how to run: `integration_artifacts/README_INTEGRATION.md`
- What is checked / not checked: `integration_artifacts/EQUIVALENCE_CHECKS.md`

Run the full deterministic suite (from repo root):

```powershell
python -m pytest -q integration_artifacts/mastereq/tests
```

### Unified-equation + microphysics wiring (integration layer)

The shared unified-equation framework and microphysics hook wiring (`use_microphysics=True`, `Γ=nσv`, `γ=Γ/c`) are integrated under:

- `integration_artifacts/mastereq/`
- `integration_artifacts/mastereq/microphysics.py`
- `integration_artifacts/mastereq/defaults.py`

The integration tests check both:
1. **Runner declared-math equivalence**, and
2. **Microphysics wiring equivalence**.

### Entanglement + photon bridge integration

The bridge pack and sector hooks are integrated under:

- `integration_artifacts/entanglement_photon_bridge/`
- `integration_artifacts/mastereq/entanglement_sector.py`
- `integration_artifacts/mastereq/photon_sector.py`

Deterministic equivalence tests:

- `integration_artifacts/mastereq/tests/test_equivalence_entanglement_runner.py`
- `integration_artifacts/mastereq/tests/test_equivalence_photon_birefringence_runner.py`

Run only the bridge equivalence tests:

```powershell
python -m pytest -q integration_artifacts/mastereq/tests/test_equivalence_entanglement_runner.py integration_artifacts/mastereq/tests/test_equivalence_photon_birefringence_runner.py
```

### Important boundary
These equivalence tests show **wiring / reproducibility consistency**.  
They do **not by themselves** establish first-principles entanglement or photon performance closure.

Bridge prereg / audit reruns are typically written under:

- `integration_artifacts/out/entanglement_photon/`

Example produced files:

- `integration_artifacts/out/entanglement_photon/coinc_audit_summary_v1.csv`
- `integration_artifacts/out/entanglement_photon/birefringence_accumulation_prereg_v1.csv`

## Baselines and evaluation metrics

The phrase **baseline** is sector-specific. Not every panel is a literal Standard Model fit.

- **Weak (neutrino):** standard 3-flavor oscillation baseline under the runner’s metric.
- **EM (LEP Bhabha / MuMu):** standard imported curve / table baseline for the same observable.
- **Strong:** standard reference curve / table under the runner’s metric.
- **GW (ringdown):** some runs are sim-only; real-compare runs use GWOSC strain against the selected GR/null reference.
- **DM (SPARC/RAR):** standard reference relation under the runner’s metric.
- **Mass spectrometry:** this is **not** an SM-vs-model fit; the baseline is a frozen no-correction reference.
- **Entanglement:** current strong result is a **data-side CH/Eberhard audit branch** at `slots 4–8`; this is not yet a model-side Bell predictor.
- **Photon:** current line is a **bridge accumulation observable**, not yet a substrate-to-propagation first-principles closure.

## Quick way to reproduce the current PASS / NOT-ESTABLISHED table

1. Run the verdict batch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_verdict.ps1
```

2. Build reports:

```powershell
python .\tools\make_repro_report.py
python .\tools\verdict_group_eval.py
```

3. Read the final summaries:

- `repro/REPORT_VERDICT.md`
- `repro/run_summary.csv`

### Important scope note
This verdict batch summarizes the **current performance scoreboard sectors**.  
Entanglement and Photon need separate audit / bridge / first-principles status reporting.

## Mass spectrometry: where the mzML files go

mzML files are typically **not committed** to git due to size and licensing/data policies.

To reproduce the mass-spec runs, you must:

- place your Bruker/CompassXport mzML exports in a local folder (commonly under `data/`), or
- set the mzML paths explicitly in the mass-spec runner commands you execute.

The paper section and runner examples often use a `data/cyto_full/*.mzML` style convention, but the exact location is not required as long as the runner paths point to the files.

## Repro Entry Points

- Main verdict batch runner:
  - `tools/run_verdict.ps1`
- Command list consumed by verdict runner:
  - `tools/verdict_commands.txt`
- Curated manual command sets:
  - [paper/PERFORMANCE_RUNBOOK_20260305_UPDATED.md](paper/PERFORMANCE_RUNBOOK_20260305_UPDATED.md)

Legacy / archival command lists (reference only):
- `verdict_reproducer_commands_v1.md`
- `CODEX_FINAL_RUN_COMMANDS.md`
- `CODEX_FINAL_RUN_COMMANDS_v2.txt`
- `CODEX_FINAL_RUN_COMMANDS_v3.txt`

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

Terminology: this sector is described in the paper as **target-specific FT-ICR** (cross-domain robustness check). Script names below keep the legacy `particle_specific` naming.

What it does: produces locked final verdict artefacts (JSON+MD) from already-generated run outputs.
It does **not** rerun mzML conversion or the multi-target analysis.

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

## Future work (updated priorities)

### Priority 1 — paper-facing performance sectors
1. **GW frequency calibration closure**
2. **EM strongest full-cov holdout completion**
3. **Paper structure cleanup / figure embedding**

### Priority 2 — entanglement / photon correctness work
1. **Entanglement Bell first-principles specification**
   - define and lock the Bell forward model
   - specify \(H_s\), \(\mathcal{D}_s\), and the measurement map
   - separate data-side audit from model-side prediction

2. **Entanglement Bell forward solver**
   - generate model-side \(J_{\mathrm{model}}\) or \(E^{\mathrm{model}}_{ab}\)
   - no data-derived template / no seed / no fit
   - evaluate on the 3-run × 3-window matrix

3. **Photon first-principles propagation closure**
   - derive propagation amplitude from substrate variables
   - replace bridge-only \(\alpha(z)=\beta I(z)\) usage with a theory-generated forward model
   - run a locked multi-catalog / holdout scorecard

### Priority 3 — broader theory work
1. **Substrate-to-operator derivation**
2. **CT/RT dual-tension dimensional analysis**
3. **Stronger sector-specific microphysics derivations**

## Main output locations

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

## Data and packaging notes

Some datasets are intentionally duplicated across:
- repo root
- `data/hepdata/`
- sector-specific subfolders

Use the paths referenced by `tools/verdict_commands.txt` as canonical for runs.

Large data files may not be tracked in git depending on your clone/source; verify local data availability before running full verdict batches.

## Repo layout

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
