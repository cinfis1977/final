# Photon sky-fold archaeology pass 3

## Objective

Third archaeology pass focused on **artifact recovery attempts** for the missing historical sky-fold runner/output pair referenced by older sibling paper drafts, while distinguishing that pair from the current workspace runner.

Target artifacts:
- `run_prereg_birefringence_skyfold_v1_DROPIN_SELFCONTAINED_FIX.ps1`
- `out/birefringence_skyfold_prereg_v1.csv`
- `prereg_birefringence_skyfold_v1_DROPIN.py`

Current workspace runner to keep fixed:
- `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`

## Recovery actions executed

### 1. Exact filename sweep across both repos
Searched both:
- `C:/Dropbox/projects/new_master_equation_with_gauge_structure_test`
- `C:/Dropbox/projects/new_master_equation_with_gauga_structure_test_git`

Result:
- exact historical PS1 runner: **not found**
- exact historical CSV output: **not found**
- current Python sky-fold implementation only exists as:
  - `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`

### 2. Text-reference sweep in sibling repo
Searched sibling text/code files for exact strings:
- `run_prereg_birefringence_skyfold_v1_DROPIN_SELFCONTAINED_FIX.ps1`
- `birefringence_skyfold_prereg_v1.csv`
- `prereg_birefringence_skyfold_v1_DROPIN.py`

Result:
- references appear in older sibling paper drafts
- no standalone runner file or archived output file was found in the live tree

### 3. ZIP-archive content sweep in sibling repo
Inspected zip archives likely to contain photon or entanglement paper packs.

Positive result:
- archives contain paper markdown/html packs

Negative result:
- no zip entry matching the missing sky-fold runner or CSV output was found

### 4. Broad hidden/backup path sweep in sibling repo
Searched recursively for path fragments:
- `skyfold`
- `sky-fold`
- `birefringence_skyfold`
- `run_prereg_birefringence_skyfold`

Result:
- no hidden or backup-path recovery hit was found in the accessible sibling repo tree

## Strongest conclusion after pass 3

The historical artifact is now supported by **paper-draft references** but remains **unrecovered** after:

- exact filename search
- text-reference search
- zip-entry search
- broad path sweep

This leaves the missing runner/output pair as a draft-referenced historical possibility that is no longer present in the accessible repositories or included paper archives, while the current fixed runner is `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`.

## Status update

- historical runner existence evidence: **yes, indirect via paper drafts**
- historical runner recovered: **no**
- historical output CSV recovered: **no**
- current workspace canonical runner pinned: **yes**
- paper-historical source chain fully pinned: **no**

## Implication for next step

For current workspace use, the runner should be fixed to `integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py`.

Any further archaeology is optional historical follow-up only. Without archived evidence, the PS1/CSV pair remains an unrecovered draft reference rather than an active canonical target.
