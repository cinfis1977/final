# Photon sky-fold archaeology pass 2

## Objective

Second archaeology pass focused on **indirect partition-angle evidence** in older paper packs, manifests, and archived file inventories.

## New high-value finding

A stronger provenance clue was found in older sibling-repo paper drafts:

- [paper_final_UPDATED_entanglement_photondecay.md](../new_master_equation_with_gauge_structure_test/paper/paper_final_UPDATED_entanglement_photondecay.md#L4405-L4413)
- [paper_final_UPDATED_entanglement_photondecay_UNIFIED_EQUATION_FULL_DROPIN_FINAL.md](../new_master_equation_with_gauge_structure_test/paper/paper_final_UPDATED_entanglement_photondecay_UNIFIED_EQUATION_FULL_DROPIN_FINAL.md#L4524-L4532)

Those drafts explicitly reference a **draft-only dedicated sky-fold runner** and output artifact:

- `run_prereg_birefringence_skyfold_v1_DROPIN_SELFCONTAINED_FIX.ps1`
- `out/birefringence_skyfold_prereg_v1.csv`

and tie them directly to the benchmark:

- sky-fold p-value `≈ 0.1536`

## Why this matters

This is stronger than generic paper wording because it implies:

1. the benchmark was not just narrative text
2. a dedicated script/output pair may once have existed in the author-side paper pack
3. this is historical provenance evidence only; the current workspace runner remains [integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py](integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py)

## Negative counterpart

The same archaeology pass also found:

- the referenced runner/output pair is **not present** in the sibling repo’s current file tree
- the pair is **not present** in the imported source inventory:
  - [integration_artifacts/tmp_source_entanglement_photon_files.txt](integration_artifacts/tmp_source_entanglement_photon_files.txt)
- the pair is **not present** in the current workspace history that was previously checked

So this is evidence of a **possible lost historical artifact**, not a recovered canonical chain.

## Secondary findings

### 1. Current conversation archive still points only to quasar/jet accumulation runners
- [paper/allchatgptconversationswithtimeorder.txt](paper/allchatgptconversationswithtimeorder.txt#L315086-L315112)
- [paper/allchatgptconversationswithtimeorder.txt](paper/allchatgptconversationswithtimeorder.txt#L317430-L317469)

Interpretation:
- archive preserves the external quasar/jet accumulation pipeline
- archive does **not** preserve the dedicated sky-fold runner name

### 2. Sibling quasar/jet runner family still lacks explicit partition-angle logic
- RA/Dec parsing and export fields exist
- no explicit sky-fold null-randomization implementation was found in those runner families

Interpretation:
- the missing dedicated sky-fold runner is increasingly likely to have been a separate artifact

## Updated interpretation after pass 2

The strongest current provenance picture is now:

1. paper wording says the sky-fold test used a fixed “hemisphere / angular partition” rule
2. external quasar/jet data can numerically mimic the benchmark under an RA-hemisphere split
3. older sibling paper drafts explicitly reference a **missing dedicated sky-fold runner/output pair**
4. however, the only runner that is actually present and usable in the current workspace is [integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py](integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py)

## Provenance status after pass 2

- current workspace canonical runner pinned: **yes**
- paper-historical chain fully pinned: **no**
- strongest new clue: **missing dedicated sky-fold runner reference in older sibling paper drafts**
- strongest surviving candidate family: **RA hemisphere / angular partition**
- blocker type: **historical artifact recovery**, not implementation uncertainty

## Best next step

If work continues, the next targeted action should be:

- treat [integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py](integration_artifacts/entanglement_photon_bridge/prereg_birefringence_skyfold_v1_DROPIN.py) as the fixed current runner
- treat the PS1/CSV names only as unrecovered draft references

Without an archived artifact or equivalent log, paper-historical closure will remain probabilistic rather than exact.
