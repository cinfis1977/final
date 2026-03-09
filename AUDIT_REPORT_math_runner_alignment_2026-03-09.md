# Audit Report: Paper Mathematics vs Runner Implementations

Date: 2026-03-09
Repo: `new_master_equation_with_gauga_structure_test_git`
Purpose: This report is written to be shared with external LLMs/tools so they can fix the identified mismatches before a fresh rerun is requested.

## 1. Scope

This report is not a generic code review. It is a targeted audit of the following question:

`Do the paper-facing runners really implement the mathematics and score logic claimed in paper_final.md?`

The audit was done by reading:

- `paper/paper_final.md`
- current run-command lists
- paper-facing wrappers
- core sector runners
- equivalence/integration tests

The goal was to separate:

- real mathematical / implementation mismatches,
- documentation / claim-boundary mismatches,
- things that are actually fine and should not be "fixed" incorrectly.

## 2. Executive Summary

The main problem is not that every sector is mathematically wrong.

The main problem is this:

1. The paper often speaks as if there is one locked, shared, deterministic unified execution path across sectors.
2. The repository does contain a shared GKSL / `mastereq` scaffold.
3. But the actual paper-facing runs are still mixed:
   - some are legacy sector-specific runners,
   - some are wrappers around older scripts,
   - some are bridge/audit layers,
   - some are genuine shared-GKSL style integrations,
   - some record reference values rather than recomputing them.

So the primary correction is conceptual and architectural honesty:

- keep what is mathematically implemented,
- weaken claims that overstate unification where it is not yet the actual paper-facing execution path,
- upgrade the paper-facing runners where stronger claims are desired.

## 3. Confirmed Problems

### 3.1 Repo-wide claim mismatch: "single locked base parameterization + deterministic sector map"

Severity: High

The paper repeatedly says that the draft uses a single locked base parameterization plus a deterministic sector map reused across sectors.

Evidence:

- `paper/paper_final.md:3`
- `paper/paper_final.md:76`
- `paper/paper_final.md:5047`

Why this is a problem:

- The current paper-facing command sets are not actually a single deterministic projection from one shared locked base.
- Different sectors use different manually chosen parameter points or entirely different evaluation modes.
- In some places the commands are even inconsistent across repo documents.

Examples:

- `CODEX_FINAL_RUN_COMMANDS_v3.txt:47` uses WEAK with `A -0.0412 --alpha 0.0`
- `CODEX_FINAL_RUN_COMMANDS_v3.txt:82` uses EM with `A -0.0412`
- `CODEX_FINAL_RUN_COMMANDS_v3.txt:91` uses DM with `A 0.1778279410 --alpha 0.001`
- `verdict_reproducer_commands_v1.md:30` uses WEAK with `A -0.002 --alpha 0.7`
- `verdict_reproducer_commands_v1.md:151-176` uses DM scans over wide `A` / `alpha` ranges
- `verdict_reproducer_commands_v1.md:280-294` uses EM `A 100000 --alpha 7.5e-05`

Interpretation:

- This is not "one deterministic sector map" in the literal paper-facing sense.
- It is a mixed repo with a shared interface idea, some shared scaffolding, and sector-specific command conventions.

Required fix:

- Either reduce the paper claim to "shared interface / shared scaffold / partially unified implementation",
- or actually build a single locked mapping layer that produces the paper-facing parameters for every sector from one common source.

Do not leave the current wording as-is if the current runbooks remain mixed.

### 3.2 Shared `mastereq` sector hooks are explicitly placeholder/scaffolding in several sectors

Severity: Medium

The repo has a real shared integration layer, but the sector helper modules often explicitly describe themselves as toy/demo/placeholder modules.

Evidence:

- `integration_artifacts/mastereq/defaults.py:3-5`
- `integration_artifacts/mastereq/weak_sector.py:3-5`
- `integration_artifacts/mastereq/em_sector.py:3-5`
- `integration_artifacts/mastereq/dm_sector.py:3-6`
- `integration_artifacts/mastereq/strong_sector.py:3-7`
- `integration_artifacts/mastereq/ligo_sector.py:3-6`
- `integration_artifacts/mastereq/entanglement_sector.py:3-7`

Why this is a problem:

- The paper sometimes reads as if the same locked mathematical skeleton is already the operative physical engine behind all paper-facing sectors.
- The code itself says otherwise in multiple places.

Important nuance:

- This does not mean the code is fake.
- It means the current shared layer is best described as an integration scaffold / equivalence scaffold / math wiring layer, not always the final physics-grade engine used by the paper-facing runs.

Required fix:

- Align paper language with code reality.
- Distinguish clearly between:
  - shared mathematical interface,
  - validated wiring / equivalence layer,
  - paper-facing production runner,
  - placeholder microphysics.

### 3.3 Photon wrapper records canonical paper p-values instead of recomputing them

Severity: Medium

The photon paper-faithful wrapper does not fully regenerate the canonical paper p-values from source data.

Evidence:

- defaults:
  - `run_photon_birefringence_prereg_paper_v1.py:53-57`
- claim boundary:
  - `run_photon_birefringence_prereg_paper_v1.py:138-139`
- stored paper reference values:
  - `run_photon_birefringence_prereg_paper_v1.py:149-155`
- report output:
  - `run_photon_birefringence_prereg_paper_v1.py:172-175`

What the wrapper currently does:

- It computes the locked CMB and accumulation checks.
- It optionally recomputes local sky-fold statistics if a sky-fold CSV is supplied.
- But the canonical paper p-values are still passed in as CLI defaults and written into the output as reference numbers.

Why this is a problem:

- "math mirrored" is not the same thing as "paper result reproduced from data".
- If the paper text suggests full rerun reproduction, this wrapper does not yet satisfy that stronger statement.

Required fix:

- Either:
  - explicitly state in the paper and wrapper docs that these are reference constants, not recomputed canonical outputs,
- or:
  - upgrade the wrapper so the canonical p-values are actually derived from the underlying source tables in the paper-facing path.

## 4. Weak Sector Detailed Report

### 4.1 The canonical paper weak path is still a legacy proxy runner, not the stronger GKSL path described elsewhere

Severity: High

The paper describes weak-sector math in unified-equation / GKSL / MSW language:

- `paper/paper_final.md:217`
- `paper/paper_final.md:3432-3451`

But the paper's own reproducible performance command for weak still points to the legacy runner path:

- `paper/paper_final.md:4546-4557`
- `score_nova_minos_t2k_penalty.py:94-106`

That wrapper runs:

- `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py`

The `v2` runner explicitly declares itself minimal, not a full matter-accurate engine:

- `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py:15-20`

Most importantly, it states:

- `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py:410`

The exact comment is that matter density is only printed for continuity and is not used yet.

What `v2` actually does:

- Builds a minimal SM probability:
  - `prob_appearance_sm(...)`
  - `prob_disappearance_sm(...)`
  - `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py:247-271`
- Computes a kernel phase perturbation:
  - `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py:178-240`
- Applies GEO via an invert-and-reapply phase-shift trick:
  - `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py:274-301`
- Builds `P_sm` from simple formulas or `N_sig_noosc`:
  - `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py:493-501`
- Uses `P_geo / P_sm` scaling to deform the signal:
  - `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py:528-560`

Why this is a problem:

- The weak performance score itself may still be internally consistent.
- But the paper language can be read as if the canonical weak paper run is already the stronger explicit-GKSL+matter implementation.
- That is not true for the paper reproducible command block.

Required fix:

Choose one of these paths and make the repo consistent:

Path A:

- Keep the legacy `v2` runner as the canonical paper weak engine.
- Then weaken the paper wording.
- Do not imply canonical weak paper performance already comes from explicit matter-enabled GKSL dynamics.

Path B:

- Make the GKSL dynamics runner the actual canonical weak paper path.
- Update the paper reproducible commands.
- Update `score_nova_minos_t2k_penalty.py` or replace it with a GKSL-backed scorer.
- Then the paper can more safely talk about unified-equation / matter / GKSL in the canonical run path.

### 4.2 There is a newer and more faithful weak GKSL runner, but it is not consistently the canonical paper-facing runner

Severity: Medium

There is a substantially stronger weak implementation:

- `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py`

This runner:

- explicitly uses `UnifiedGKSL` / `UnifiedGKSL3`:
  - `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py:42-49`
- supports matter term:
  - `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py:198-201`
  - `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py:383-395`
- supports damping:
  - `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py:396-418`
- can run internal rate-model / rate-kernel closures:
  - `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py:248-256`
  - `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py:470-555`

The newest runbook appears to have moved in this direction:

- `CODEX_FINAL_RUN_COMMANDS_v3.txt:25-59`

But the paper reproducible section still documents the older `v2` path:

- `paper/paper_final.md:4546-4557`

Why this is a problem:

- The repo now has two different weak stories:
  - paper-facing reproducible weak score story,
  - newer GKSL dynamics runner story.
- They are related, but not the same canonical artifact chain.

Required fix:

- Declare one as canonical for the paper.
- Mark the other as either legacy compatibility or next-generation replacement.

### 4.3 Weak documentation is stale and internally inconsistent

Severity: Medium

Weak parameter examples are inconsistent across paper and runbooks.

Examples:

- `paper/paper_final.md:3438-3444` shows one example parameter set
- `paper/paper_final.md:4550` uses `A -0.002 --alpha 0.7`
- `CODEX_FINAL_RUN_COMMANDS_v3.txt:47` uses `A -0.0412 --alpha 0.0`

Why this matters:

- It becomes unclear which weak run is the real paper lock.
- External reviewers cannot tell whether later changes are upgrades, replacements, or accidental drift.

Required fix:

- Add an explicit "canonical weak lock for this paper revision" section.
- Put one command set there.
- Mark all others as:
  - legacy compatibility,
  - historical run,
  - exploratory scan,
  - post-paper candidate,
  - or deprecated.

### 4.4 Weak tests partially prove equivalence, but test naming can mislead

Severity: Low

The repo does contain useful weak tests:

- legacy equivalence:
  - `integration_artifacts/mastereq/tests/test_equivalence_weak_runner.py`
- rate-kernel / dynamics tests on GKSL runner:
  - `integration_artifacts/mastereq/tests/test_e2e_weak_runner_internal_rate_kernel.py`
  - `integration_artifacts/mastereq/tests/test_weak_rate_model_pack_mode.py`
- 3-flavor integrity:
  - `integration_artifacts/mastereq/tests/test_weak_3flavor_dynamics_integrity.py`

However:

- `integration_artifacts/mastereq/tests/test_e2e_weak_gksl_runner_matches_golden.py`

is named as if it runs the GKSL dynamics runner, but it actually calls:

- `nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py`

Evidence:

- `test_e2e_weak_gksl_runner_matches_golden.py:68-73`
- `test_e2e_weak_gksl_runner_matches_golden.py:137-142`

Why this is a problem:

- It weakens audit clarity.
- It can make a reviewer think the true GKSL path has stronger golden coverage than it actually does.

Required fix:

- Rename that test to reflect what it really covers,
- or make it actually run `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py`.

### 4.5 Weak score logic itself is not the main bug

Important non-finding:

The weak composite score logic itself is straightforward and implemented as declared:

- `score_nova_minos_t2k_penalty.py:5`
- `score_nova_minos_t2k_penalty.py:149-165`
- `t2k_penalty_cli.py:121-139`

So the main weak issue is not "the total score formula is missing."

The main weak issue is:

- canonical engine mismatch,
- stale documentation,
- over-strong paper reading relative to the actual paper-facing runner.

## 5. Mass Spectrometry (MS) Detailed Report

### 5.1 The MS prereg score logic is implemented correctly

Important non-finding:

The MS score criteria in the paper match the finalizer code very closely.

Paper criteria:

- `paper/paper_final.md:2719-2735`

Finalizer implementation:

- `runners/particle_specific_finalize_from_runs_v1_0_DROPIN/finalize_particle_specific_goodppm_lock_from_runs_v1_0.py:179-188`

This is one of the cleaner sectors in terms of score-criterion implementation.

### 5.2 The main MS problem is interpretational: the paper pass is based on `raw_ppm`, not on drift-corrected dynamics output

Severity: Medium

The runner has a real dynamic state layer:

- common drift state built from baseline scans:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:523-536`
- stateful recursion enforcement:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:538-547`
- integrity telemetry:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:576-599`
- dynamics audit layer:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:723-839`

However, the paper-facing prereg observable is explicitly locked to `raw_ppm`:

- CLI definition:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:370-379`
- comment:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:381-389`
- actual branch:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:615-620`

The paper reproducible commands also explicitly use:

- `--prereg_observable raw_ppm`

Evidence:

- `paper/paper_final.md:4718`
- `paper/paper_final.md:4736`
- `paper/paper_final.md:4754`
- `paper/paper_final.md:4829`
- `paper/paper_final.md:4847`
- `paper/paper_final.md:4865`

Why this is a problem:

- A reader may think the MS performance pass is a direct consequence of the state-corrected dynamic model.
- In fact, the performance verdict is still generated from the locked raw-ppm observable.
- The dynamics layer is currently an integrity / audit / anti-shortcut layer, not the direct basis of the final pass verdict.

This is not fraudulent by itself.

But it must be described correctly.

Required fix:

- Make the paper text explicit:
  - the final prereg performance pass is based on the locked raw-ppm target-specific signature,
  - the stateful dynamics layer is separately enforced and audited as an integrity requirement,
  - the current pass is not yet a "fully dynamics-corrected observable pass" if that stronger phrase would imply `corrected_ppm` was the scoring observable.

### 5.3 The MS paper already contains hints of this distinction, but the distinction should be made explicit

Severity: Medium

The paper says:

- `paper/paper_final.md:4531`

and later records:

- `prereg_all_pass = true`
- `dynamics_stateful_all = true`

Evidence:

- `paper/paper_final.md:4689-4692`
- `paper/paper_final.md:4791-4802`

The repo aggregator also keeps these as separate dimensions:

- prereg pass flags:
  - `ms_dynamics_integrity_aggregate_v1_DROPIN.py:295-305`
- stateful expectations:
  - `ms_dynamics_integrity_aggregate_v1_DROPIN.py:327-337`
- overall summary:
  - `ms_dynamics_integrity_aggregate_v1_DROPIN.py:364-365`

Why this is still a problem:

- The paper summary prose can still be read too strongly.
- "performance pass and dynamics integrity true" is not the same thing as "performance pass because the dynamic-corrected observable succeeded."

Required fix:

- In the paper, add one explicit sentence:
  - the pass criterion is computed on the locked `raw_ppm` observable;
  - dynamics integrity is an additional required audit layer in this repo revision.

### 5.4 The MS pipeline is otherwise one of the stronger sectors

Important non-finding:

The MS code does have real anti-shortcut structure:

- raw -> state -> dynamics -> observables framing:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:5-28`
- baseline-only common drift state:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:523-536`
- stateful recursion requirement:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:538-547`
- anti-cancel diagnostics:
  - `ms_particle_specific_dynamic_runner_v1_0_DROPIN.py:770-837`

So this sector should not be described as a fake pass.

The correction needed here is wording precision, not destruction of the current MS result.

## 6. Sector Summary Outside Weak/MS

These are included because they affect the repo-wide report.

### 6.1 EM

Current status:

- The EM proxy formula appears honestly implemented as a proxy layer.
- `pred_geo = pred_sm * (1 + delta_i)` is explicit.

Evidence:

- `em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py:8`
- `em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py:130-165`
- `em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.py:15-20`
- `em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.py:200-212`

Main caution:

- The paper should keep calling this a proxy / bridge / shape-only branch, not overstate it as final first-principles EM closure.

### 6.2 DM

Current status:

- The DM score criterion is implemented correctly.

Evidence:

- formula:
  - `dm_holdout_cv_thread.py:96-99`
- fold scoring:
  - `dm_holdout_cv_thread.py:242-262`
- performance flag:
  - `dm_holdout_cv_thread.py:365-370`
- paper criterion:
  - `paper/paper_final.md:49`

Main caution:

- This sector still participates in the repo-wide "single deterministic map" overclaim problem.

### 6.3 LIGO

Current status:

- The null p-metrics described in the paper are explicitly present in code.

Evidence:

- `gw170814_ringdown_only_null_v1_FIXED_v7_consistency_3det_projected_peakalign_v6_fixedlags.py:1160-1175`
- `paper/paper_final.md:53`

Main caution:

- Same repo-wide claim-boundary issue as above.

### 6.4 Entanglement

Current status:

- This sector is comparatively honest in the current revision.
- The wrapper explicitly says it is a validated audit / benchmark path, not a full first-principles Bell derivation.

Evidence:

- `run_entanglement_nist_run4_chsh_audit_paper_v1.py:125-141`
- `run_entanglement_nist_run4_chsh_audit_paper_v1.py:157-161`
- `paper/paper_final.md:68`
- `paper/paper_final.md:99`

Main caution:

- Do not let external models "upgrade" this sector by overclaiming physics closure that the repo does not yet have.

### 6.5 Strong

Current status:

- The paper-facing strong wrapper openly frames itself as reproducibility / IO closure / anti-fallback evidence, not a physical-accuracy claim.

Evidence:

- `run_strong_c5a_paper_run.py:3-9`
- `run_strong_c5a_paper_run.py:139-214`

Main caution:

- This sector was not audited as deeply as Weak/MS in this pass.
- Do not claim it was fully line-by-line cleared beyond the wrapper-level framing and repo-wide unification issue.

## 7. What Must Be Fixed Before Fresh Reruns

The following corrections should be requested from ChatGPT / Claude before asking for a full rerun.

### 7.1 Global paper claim cleanup

They should:

1. revise the paper text around "single locked base parameterization" and "deterministic sector map";
2. explicitly distinguish:
   - shared GKSL interface,
   - shared scaffold,
   - paper-facing production runners,
   - bridge/audit sectors,
   - placeholder microphysics;
3. remove wording that suggests stronger unification than the current paper-facing code actually uses.

### 7.2 Photon correction

They should do one of the following:

1. keep the wrapper as a reference-value recorder and state that clearly everywhere; or
2. implement full canonical p-value recomputation from actual source data in the paper-facing wrapper.

If they choose option 2, they should also add a test showing that the canonical paper values are reproduced from input data rather than injected as CLI constants.

### 7.3 Weak correction

They must choose a canonical weak path.

If canonical = legacy `v2` runner:

- weaken the paper math language;
- do not imply matter-enabled GKSL is the actual paper score engine.

If canonical = GKSL runner:

- update paper reproducible commands,
- update the scorer wrapper,
- update tests,
- document the exact locked parameter set,
- and ensure matter use is explicitly on if the paper claims matter participation.

They should also clean up:

- stale parameter examples,
- test names that misdescribe coverage,
- duplicate or conflicting weak command lists.

### 7.4 MS correction

They should make the paper explicitly say:

- final prereg performance pass uses locked `raw_ppm`,
- dynamics layer is separately required and audited,
- current MS result is not yet a "corrected_ppm-based pass" unless they intentionally move the scoring observable to that branch.

If they want a stronger dynamics claim, they must:

- switch the canonical scoring observable,
- re-freeze the lock,
- rerun all three arms,
- and justify the change as a new revision rather than silently reinterpreting the current one.

## 8. Suggested Acceptance Criteria For The Fixes

Before asking for new runs, the following should be true:

1. One canonical weak runner is declared.
2. One canonical weak command block is declared.
3. The paper uses wording consistent with that canonical weak engine.
4. Photon wrapper either recomputes the canonical p-values or explicitly labels them as reference constants.
5. MS wording explicitly separates:
   - prereg pass basis,
   - dynamics integrity basis.
6. Repo-wide "single deterministic map" wording is corrected unless implemented literally.
7. Test names and coverage are cleaned up enough that a reviewer can see what is actually being tested.

## 9. What Should Not Be "Fixed" Incorrectly

When sharing this report with other models, the following should be preserved:

1. Do not delete the shared GKSL / `mastereq` scaffold. It is useful and real.
2. Do not falsely claim that EM, DM, LIGO, or Entanglement are all broken.
3. Do not turn the MS result into "invalid" just because dynamics is not the direct scoring observable.
4. Do not over-upgrade Entanglement or Photon into first-principles closure if that code does not exist.
5. Do not silently swap legacy and GKSL weak paths without updating paper wording and runbooks.

## 10. Final Bottom Line

The current repo does contain substantial real work:

- real score criteria,
- real wrappers,
- real integration scaffolding,
- real weak GKSL development,
- real MS integrity layering,
- real bridge/audit sectors.

But the paper-facing narrative is stronger and cleaner than the actual current execution topology.

That is the central correction.

In one sentence:

`The biggest issue is not that the sectors are all mathematically fake; it is that the paper currently overstates how unified, canonical, and fully regenerated the paper-facing execution path already is.`

