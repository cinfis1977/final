# Photon sky-fold archaeology pass 1

## Objective

Targeted archaeology pass for evidence that the paper-facing photon sky-fold benchmark

- `p ≈ 0.1536`

came from an **angular partition** or **RA hemisphere** rule rather than the current sign-of-coordinate helper.

## Search scope executed

### Current workspace
- paper text and paper-derived docs
- conversation archive `paper/allchatgptconversationswithtimeorder.txt`
- current provenance notes and candidate ledger
- current repo git history for photon / birefringence / quasar / sky-fold filenames

### Sibling repo
- quasar/jet README files
- quasar/jet runner family:
  - `prereg_quasar_jet_birefringence_accum_v1_DROPIN.py`
  - `prereg_quasar_jet_v8*_DROPIN.py`
  - `prereg_quasar_jet_v9*_DROPIN.py`
  - `prereg_quasar_jet_birefringence_cdsarc_v5/v6/v7_DROPIN.py`
- external outputs:
  - `out/quasar_jet_matches_v1.csv`
  - `out/quasar_jet_join_debug_v1.txt`

## Positive findings

### 1. Paper wording explicitly allows an angular partition
- [paper/paper_final.md](paper/paper_final.md#L3144-L3146)
- wording: “hemisphere / angular partition fixed in code”
- classification: **direct wording clue**, not implementation evidence

### 2. External quasar/jet table preserves RA and Dec
- external table contains:
  - `qso_ra_deg`
  - `qso_dec_deg`
  - `delta_wrap90_deg`
- classification: **usable external data chain**

### 3. Diagnostic scan found a near-match RA hemisphere rule
- [out/photon_paper/photon_skyfold_provenance_diagnostic_v1.md](out/photon_paper/photon_skyfold_provenance_diagnostic_v1.md#L10-L17)
- closest match:
  - rule: `cos(qso_ra_deg - 164 deg) >= 0`
  - metric: `abs(delta_wrap90_deg)`
  - `p_value_abs = 0.1544`
- classification: **strong numerical clue**, not canonical proof

### 4. Conversation archive preserves the external quasar/jet reconstruction path
- [paper/allchatgptconversationswithtimeorder.txt](paper/allchatgptconversationswithtimeorder.txt#L317430-L317469)
- shows refreshed TAP-based quasar/jet run and the matched-table pipeline
- classification: **external chain provenance**, not paper-canonical sky-fold rule evidence

## Negative findings

### 1. No archived RA-hemisphere or partition-angle code was found in current workspace history
- current repo git history did not reveal older committed sky-fold/photon/quasar artifacts beyond the currently tracked bridge files
- classification: **negative evidence**

### 2. No angular-partition logic was found in sibling quasar/jet runners
- targeted scan of v8/v9 quasar runners found RA/Dec parsing and export fields only
- no explicit logic for:
  - `hemisphere`
  - `partition angle`
  - `center_deg`
  - `permutation` sky-fold test
  - `cos(ra - phi) >= 0` style split
- classification: **negative evidence**

### 3. No conversation-archive hit for explicit RA-hemisphere wording
- targeted archive search did not recover phrases like:
  - `RA hemisphere`
  - `angular partition`
  - `center angle`
  - `cos(ra - phi)`
- classification: **negative evidence**

## Working interpretation after pass 1

Current best interpretation:

1. the paper wording leaves room for an angular-partition rule
2. the external quasar/jet table is rich enough to support such a rule
3. a simple RA hemisphere split reproduces the benchmark numerically to within `0.0008`
4. but no archived runner, log, or source file currently ties that rule to the canonical paper benchmark

## Status impact

- candidate narrowing: improved
- current workspace canonical runner: **pinned to** [integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py](integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py)
- paper-historical source chain: **not pinned**
- strongest surviving family: **RA hemisphere / angular partition**

## Recommended pass 2

Search next for hidden or indirect evidence of a partition-angle convention, especially:

- old markdown snippets or scratch notes mentioning `phi`, `angle`, `hemisphere`, `sky split`
- output tables or JSON files with two balanced sky subsets but without explicit rule text
- any archived photon-sector note outside the main paper that mentions directional null randomization
