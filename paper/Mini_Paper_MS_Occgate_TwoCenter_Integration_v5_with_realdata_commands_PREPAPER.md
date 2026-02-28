# Mini paper - Mass Spectrometer addendum: single-center occgate and two-center diagnostic-boundary integration (v2, current-scope only)

## 1. Purpose and scope

This note consolidates the current-scope Mass Spectrometer-side branch work that extends the canonical real-mzML target-specific PASS already documented in the main paper. The aim is narrow: determine whether two additional internal structures can be carried forward under the same falsification-first discipline without overclaiming:

1. a single-center occupancy-gate correction on the already-locked success layer; and
2. a two-center diagnostic-boundary layer built on the frozen target registry.

This note is written in the same conservative style as the main paper. It is not a claim that the full model is physically proven. It is a current-scope statement about what survives the present locked internal tests and how those surviving pieces attach to the unified equation.

## 2. Explicit unified-equation adapter hook (the mathematical attachment)

The common attachment point is the same cross-sector skeleton already used elsewhere in the project:

\[
\frac{d\rho}{dL}
=
-i\!\left[H_{\mathrm{vac}} + H_{\mathrm{MS}}^{(0)} + \delta H_{\mathrm{MS}}^{(2c)} + \sum_{s\neq \mathrm{MS}} H_s,\rho\right]
+
\mathcal D_{\mathrm{MS}}^{(0)}\!\left[\rho;\gamma_{\mathrm{MS}}^{\mathrm{eff}}\right]
+
\delta \mathcal D_{\mathrm{MS}}^{(2c)}\!\left[\rho;\gamma_A^{\mathrm{eff}},\gamma_B^{\mathrm{eff}}\right]
+
\sum_{s\neq \mathrm{MS}} \mathcal D_s[\rho].
\]

This is the minimal adapter statement that makes the present branch mathematically attach to the unified equation instead of floating as a detached side note.

### 2.1 Single-center adapter

\[
x_{\mathrm{occ}} = \frac{I_{\mathrm{core}}}{I_{\mathrm{core}} + I_{\mathrm{shoulder}} + I_{\mathrm{outer}}},
\qquad
\gamma_{\mathrm{MS}}^{\mathrm{eff}} = \gamma_{\mathrm{MS}}^{(0)}\left(1-\rho_{\mathrm{occ}} x_{\mathrm{occ}}\right),
\qquad
\rho_{\mathrm{occ}} = 0.10.
\]

The directly implemented observable-level equivalent is

\[
p_{\mathrm{success,occ}} = p_{\mathrm{success,legacy}}\left(1-\rho_{\mathrm{occ}} x_{\mathrm{occ}}\right).
\]

This is a constrained multiplicative modulation of the already-frozen MS success / damping channel. It is not a new fitted layer.

The value \(\rho_{\mathrm{occ}}=0.10\) is not used here as a fit parameter. It is the pre-committed minimal carry-forward value selected by the locked single-center hard-regression screen after larger trial values failed to remain uniformly safe under the current three-arm coverage.

### 2.2 Two-center adapter

The conceptual two-center law remains the bounded entanglement-first working law:

\[
\frac{d\Psi_{AB}}{dt}
=
(\alpha-\gamma)\Psi_{AB}
-\beta |\Psi_{AB}|^2\Psi_{AB}
+\eta L_{\mathrm{overlap}}.
\]

Here \(t\) is only an internal interaction parameter for the local two-center working law. The attachment back to the unified equation is still carried at the path-length level \(L\) through the MS-sector adapter, so this does not introduce a competing evolution variable in the main framework.

The minimal explicit adapter into the unified equation is then carried as

\[
B_{AB} = |\Psi_{AB}|^2,
\qquad
\gamma_A^{\mathrm{eff}} = \gamma_A^{(0)}\left(1-\xi B_{AB}\right),
\qquad
\gamma_B^{\mathrm{eff}} = \gamma_B^{(0)}\left(1-\xi B_{AB}\right),
\]

and

\[
\delta H_{\mathrm{MS}}^{(2c)} = \kappa_B B_{AB}\left(|A\rangle\langle B| + |B\rangle\langle A|\right).
\]

This is an adapter-only bookkeeping bridge. It shows where the branch sits mathematically in the unified equation. It is not claimed here as a fully validated microscopic Hamiltonian.

## 3. Single-center occupancy-gate branch (locked full-run result)

Using the full 3-arm occgate runner on the current locked real-data MS family:

- arms: `ModeA_points`, `ModeB_points`, `ModeB_holdout_points`
- targets: 12
- settings: 3
- baseline `p_success = 1.0` across the current locked rows
- `p_success_occ` / `gate_occ_factor_mean` range: `0.9310250312` to `0.9677384486`
- mean `p_success_occ` / `gate_occ_factor_mean`: `0.9459447610`
- mean `mean_abs_delta_p_success_occ` across compares: `0.0030917513`
- worst `max_abs_delta_p_success_occ`: `0.0191164089`
- worst target: `T02` vs `ModeB_holdout_points`

### 3.1 Branch verdict

Current-scope verdict: the single-center minimal occupancy-gate insertion with `rho = 0.10` survives the full 3-arm occgate runner on the current locked real-data MS family.

What this supports:
- `rho = 0.10` remains the default carry-forward candidate for the single-center branch.
- the adapter is safe to keep as a constrained MS-sector modulation inside the unified-equation bookkeeping.

What this does not support:
- physical proof
- validity beyond the current MS family
- full model validation

## 4. Two-center diagnostic-boundary branch

### 4.1 Frozen pair-layer status

The implemented diagnostic pair layer remains deliberately modest:
- deterministic pair construction from the frozen target ordering
- adjacent baseline preserved at all times
- refinement allowed only if it increases resolution without changing the story

Current frozen pair-layer results:
- adjacent baseline: `11` pairs = `8 stable / 3 repulsive / 0 inconclusive`
- adjacent + next-nearest refined layer: `21` pairs = adjacent subset preserved, added shell `5 stable / 5 repulsive / 0 inconclusive`
- shell monotonicity stability sweep: `27 / 27` scenarios passed under mild deterministic parameter variation

### 4.2 Raw-data rebuild under frozen thresholds

Frozen thresholds:
- `width_scale = 1.0`
- `corridor_min = 0.25`
- `reject_max = 0.75`
- `leak_ratio_max = 0.90`
- `sep_s0 = 0.11`
- `confidence_quantile = 0.25`

Under four separate rebuild runs (`A1_B2 ModeA`, `A1_B2 ModeB`, `A1_B2_direct ModeB_holdout`, and the combined pool), all four runs yielded:
- `classification_changes = 0`
- `confidence_changes = 1`
- `shell_monotonicity = OK`
- verdict: `PASS-DIAGNOSTIC-REBUILD`

Explicit rollup answer:
- the observed two-center skeleton is not only a pooled-data effect; the same classification skeleton survives in each arm individually.

### 4.3 Weak-stable boundary hard falsifier (single global frozen edge)

The weak-stable boundary question was reduced to the two weakest stable-boundary pairs:
- `T05 <-> T12`
- `T08 <-> T09`

The strict version used one single frozen weak-stable edge for all runs:
- `global_frozen_weak_stable_edge = 0.33904771546`
- `global_edge_band_median_abs_distance = 0.022510457733`

Across all `4 runs x 2 pairs = 8` checks:
- `near_global_edge = True`
- base label stayed `STABLE-INTERMEDIATE-CANDIDATE`
- confidence stayed `WEAK_STABLE`
- `conf_changed_vs_track8 = False`

Signed distance to the same edge stayed small and negative:
- approximately `-0.000879170387197` to `-0.00163583576279`

These signed distances are small relative to the frozen edge-band median absolute distance (`0.022510457733`), so they are consistent with weak-stable boundary proximity and are not a boundary-violation signal.

### 4.4 Branch verdict

Current-scope verdict: the two-center weak-stable boundary story survives the current hard internal falsifier and is safe to keep as a diagnostic-boundary adapter within the unified-equation bookkeeping.

What this supports:
- a bounded two-center bridge adapter can be carried forward as a prepaper working component
- the current weak-stable boundary reading is internally stable under frozen raw-data rebuild and a single global frozen edge

What this does not support:
- chemistry explained
- molecular bond validated
- direct entanglement measurement from the MS data
- full physical proof

## 5. Integrated claim boundary

The correct current-scope statement is:

> Under the current locked MS real-data scope, the single-center occgate adapter and the two-center diagnostic-boundary adapter both survive the present internal falsification ladder and may be carried forward as constrained working components of the unified-equation framework.

The incorrect statement is:
- the full model is physically proven.

For stronger claims, the next requirement is not more repetition on the same pack, but new independent real data or a more direct observable.


## 6. Reproducible real-data run commands (current MS closure set)

This section records the real-data runs that fed the present Mass Spectrometer closure state. Derived-only pair-layer sweeps (Track 1-8 on already-derived CSV layers) are intentionally omitted here; what follows are the runs that touched raw MS points or the final locked 3-arm pack.

### 6.1 Single-center full 3-arm occgate closure (exact local CLI)

This is the exact full-run command for the locked 3-arm occupancy-gate closure at `rho = 0.10`.

```powershell
py -3 -X utf8 .\multi_target_particle_specific_v1_0_occgate_v1_PREPAPER.py `
  --inputs `
    .\out\particle_specific_cytofull_A1_B2\ModeA_points.csv `
    .\out\particle_specific_cytofull_A1_B2\ModeB_points.csv `
    .\out\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --targets_csv .\out\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --out_dir .\out\particle_specific_cytofull_A1_B2_occgate_rho010_3arm `
  --setting_from filename `
  --baseline ModeA_points `
  --enable_occ_gate `
  --occ_rho 0.10
```

Expected closure outputs:
- `alltargets_bin_success_width_stats_occgate.csv`
- `alltargets_delta_success_width_pairs_occgate.csv`
- `targets_summary_occgate.csv`

### 6.2 Single-center memory-safe streaming cross-check (exact local CLI; auxiliary)

This auxiliary real-data cross-check was the memory-safe streaming fallback used to confirm that the occupancy-gate factor stayed mild across all 3 raw-data arms.

```powershell
Copy-Item .\out\particle_specific_cytofull_A1_B2_direct\targets_used.csv .\targets_used.csv
Copy-Item .\out\particle_specific_cytofull_A1_B2\ModeA_points.csv .\ModeA_points.csv
Copy-Item .\out\particle_specific_cytofull_A1_B2\ModeB_points.csv .\ModeB_points.csv
Copy-Item .\out\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv .\ModeB_holdout_points.csv
py -3 -X utf8 .\single_center_occgate_streaming_rho010_3arm_DROPIN.py
```

Expected auxiliary output:
- `single_center_occgate_streaming_rho010_3arm.csv`

### 6.3 Two-center pre-freeze combined raw rebuild (exact local CLI; infer-threshold diagnostic)

This is the exact recoverable pre-freeze raw-data rebuild command preserved in the mounted artifact set. It is the infer-threshold diagnostic rebuild that generated the first combined raw-data comparison.

```powershell
py -3 -X utf8 .\rebuild_two_center_diagnostic_from_raw.py `
  --targets_csv .\targets_used.csv `
  --current_two_center_csv .\Two_Center_Shadow_Pair_Classification_Track5_v1_PREPAPER_live.csv `
  --raw_points `
    .\out\particle_specific_cytofull_A1_B2\ModeA_points.csv `
    .\out\particle_specific_cytofull_A1_B2\ModeB_points.csv `
    .\out\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --out_dir .\out\two_center_rebuild_from_raw `
  --confidence_quantile 0.25
```

Expected outputs:
- `rebuilt_target_windows.csv`
- `rebuilt_two_center_pair_metrics.csv`
- `rebuilt_vs_current_comparison.csv`
- `rebuilt_two_center_verdict.md`

### 6.4 Two-center frozen arm-by-arm rebuild (exact automation launcher preserved; standalone frozen driver filename not preserved)

The stricter frozen arm-by-arm rebuild was executed as a local Codex automation step. The mounted artifact set preserves the outputs, the frozen thresholds, and the archived comparator, but it does not preserve the generated standalone frozen driver filename. To avoid fabricating a missing script name, the paper records the exact launcher plus the exact preserved run contract.

```bash
codex --full-auto
```

Preserved run contract:
- inputs:
  - `out/particle_specific_cytofull_A1_B2/ModeA_points.csv`
  - `out/particle_specific_cytofull_A1_B2/ModeB_points.csv`
  - `out/particle_specific_cytofull_A1_B2_direct/ModeB_holdout_points.csv`
  - `out/particle_specific_cytofull_A1_B2_direct/targets_used.csv`
  - `track8_current_layer_generated_frozen.csv`
- frozen thresholds:
  - `width_scale = 1.0`
  - `corridor_min = 0.25`
  - `reject_max = 0.75`
  - `leak_ratio_max = 0.90`
  - `sep_s0 = 0.11`
  - `confidence_quantile = 0.25`
- runs:
  - `A1_B2 ModeA`
  - `A1_B2 ModeB`
  - `A1_B2_direct ModeB_holdout`
  - `Combined_A1_B2_plus_holdout`
- preserved output pack:
  - `arm_by_arm_rebuild_frozen_20260227.zip`

### 6.5 Two-center weak-stable pair falsifier and global frozen-edge hard falsifier (exact automation launcher preserved; standalone driver filenames not preserved)

The pair-focused raw-window falsifier and the final single-global-edge hard falsifier were also executed as local Codex automation steps. Their output packs are preserved, but the generated standalone driver filenames are not present in the mounted artifact set, so only the exact launcher and the preserved input/output contract are recorded here.

```bash
codex --full-auto
```

Preserved weak-stable pair falsifier contract:
- raw-data arms: `ModeA`, `ModeB`, `ModeB_holdout`, and the combined pool
- fixed pair focus: `T05 <-> T12` and `T09 <-> T08`
- preserved output pack:
  - `weakstable_pair_falsifier_20260227.zip`

```bash
codex --full-auto
```

Preserved global-edge hard falsifier contract:
- same raw-data arms and the same two weak-stable boundary pairs
- one single archived frozen edge from the comparator (no per-run edge recalculation)
- preserved output pack:
  - `weakstable_pair_globaledge_20260227.zip`

These two automation-run families are intentionally documented this way because the output artifacts are preserved but the exact generated `.py` filenames are not. This keeps the paper honest while still recording the real-data launch path used in practice.

