# Photon sky-fold candidate rule ledger

## Purpose

This ledger narrows the remaining canonical photon sky-fold provenance gap.
It does **not** upgrade any candidate into canonical status.
A candidate becomes canonical only if it is tied to:

- an archived source table
- an archived fold rule / runner
- paper-facing evidence that the rule was the one used for the reported benchmark

## Canonical benchmark to explain

From the paper-facing layer:

- paper sky-fold benchmark: `p ≈ 0.1536`
- wording in the paper: “hemisphere / angular partition fixed in code”

Relevant references:
- [paper/paper_final.md](paper/paper_final.md#L3144-L3164)
- [ENT_PHOTON_FINAL_AUDIT_NOTE.md](ENT_PHOTON_FINAL_AUDIT_NOTE.md#L147-L167)

## Source material currently available

### Local repo
- paper wording only; no exact canonical source table or fold-rule artifact was found
- current canonical workspace runner:
  - [integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py](integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py)
- current implementation helper uses sign-of-coordinate split:
  - `fold_rule = sky_coord_deg >= 0`
- diagnostic scan runner:
  - [integration_artifacts/entanglement_photon_bridge/diagnose_birefringence_skyfold_partitions_v1.py](integration_artifacts/entanglement_photon_bridge/diagnose_birefringence_skyfold_partitions_v1.py)

### Sibling repo external chain
- external matched table:
  - `C:/Dropbox/projects/new_master_equation_with_gauge_structure_test/out/quasar_jet_matches_v1.csv`
- join/debug evidence:
  - `qso_ra_deg`
  - `qso_dec_deg`
  - `delta_wrap90_deg`
- older sibling paper drafts also reference a draft-only missing dedicated sky-fold runner/output pair:
  - `run_prereg_birefringence_skyfold_v1_DROPIN_SELFCONTAINED_FIX.ps1`
  - `out/birefringence_skyfold_prereg_v1.csv`
- these names are historical references only; they are not current workspace artifacts
- supporting provenance notes:
  - [out/photon_paper/photon_skyfold_provenance_diagnostic_v1.md](out/photon_paper/photon_skyfold_provenance_diagnostic_v1.md)
  - [PHOTON_SKYFOLD_ARCHAEOLOGY_PASS2.md](PHOTON_SKYFOLD_ARCHAEOLOGY_PASS2.md)

## Candidate ranking

Ranked by numerical closeness to the paper benchmark on the **external** quasar/jet table.
These are provenance clues only.

### Tier A — strongest numerical candidates

#### Candidate A1
- family: RA hemisphere
- rule: `cos(qso_ra_deg - 164 deg) >= 0`
- metric: `abs(delta_wrap90_deg)`
- result: `p_value_abs = 0.1544`
- distance to paper benchmark: `|0.1544 - 0.1536| = 0.0008`
- partition sizes: `n_pos = 46`, `n_neg = 38`
- status: **closest numeric match found so far**
- weakness: no archival evidence that RA hemisphere was the paper rule

#### Candidate A2
- family: RA hemisphere
- rule: `cos(qso_ra_deg - 344 deg) >= 0`
- metric: `abs(delta_wrap90_deg)`
- result: `p_value_abs = 0.1544`
- distance to paper benchmark: `0.0008`
- partition sizes: `n_pos = 38`, `n_neg = 46`
- status: symmetric complement of A1
- weakness: same canonical-evidence gap

### Tier B — plausible declination-threshold candidates

#### Candidate B1
- family: declination threshold
- rule: `qso_dec_deg >= 11.730833`
- metric: `signed(delta_wrap90_deg)`
- result: `p_value_abs = 0.1588`
- distance to paper benchmark: `0.0052`
- partition sizes: `n_pos = 29`, `n_neg = 55`
- status: closest declination-style candidate found in the current scan
- weakness: not especially close; also differs from the current helper’s zero-threshold rule

#### Candidate B2
- family: declination threshold
- rule: `qso_dec_deg >= 55.382778`
- metric: `signed(delta_wrap90_deg)`
- result: `p_value_abs = 0.1590`
- distance to paper benchmark: `0.0054`
- partition sizes: `n_pos = 8`, `n_neg = 76`
- weakness: highly imbalanced split; weak canonical plausibility

### Tier C — current implemented helper rule

#### Candidate C1
- family: sign-of-coordinate split
- rule: `qso_dec_deg >= 0`
- metric: `signed(delta_wrap90_deg)`
- result on external quasar/jet table: `p_value_abs ≈ 0.02395`
- status: matches the **current local implementation pattern**
- weakness: clearly does **not** match the paper benchmark

#### Candidate C2
- family: sign-of-coordinate split
- rule: `qso_dec_deg >= 0`
- metric: `abs(delta_wrap90_deg)`
- result on external quasar/jet table: `p_value_abs ≈ 0.65425`
- weakness: very far from the paper benchmark

## Current inference

Best working inference at this point:

1. the paper benchmark `≈ 0.1536` is likely compatible with some **angular partition rule**
2. the current helper rule `sky_coord_deg >= 0` is probably **not** the original paper-facing rule if the external quasar/jet table is even approximately comparable
3. the strongest surviving clue is an **RA hemisphere** style split, not the currently implemented declination-sign split
4. older sibling paper drafts make it likely that a separate dedicated sky-fold runner once existed and is now missing

This remains an inference only.

## What would upgrade a candidate to canonical

Any one of the following would materially close the gap:

- an archived source file used for the paper run
- an old runner or snippet showing the exact fold rule
- a report/log that names the exact coordinate and partition rule
- a paper draft fragment linking the benchmark directly to a concrete source table and rule

Current blocker after archaeology passes 1-3:

- older sibling paper drafts prove that a dedicated sky-fold runner/output pair once existed
- accessible repos and scanned zip archives still do **not** contain that pair
- so the missing link is now best described as **external artifact recovery**, not further rule enumeration inside the current trees

## Recommended next narrowing step

If provenance closure continues, search specifically for archived wording or logs consistent with:

- “RA hemisphere”
- “angular partition”
- “partition angle / center angle”
- “cos(ra - phi) >= 0” style rules
- any photon sky-fold output produced from a quasar/jet matched table rather than the current simple helper default

## Ledger status

- candidate ledger prepared: yes
- current workspace canonical runner pinned: yes
- paper-historical source chain recovered: no
- strongest candidate family: `RA hemisphere`
- canonical claim allowed: no
