# DM-C1 paper run report

This report is produced by `run_dm_c1_paper_run.py`.
It is an IO/closure + schema-stability artifact for DM-C1 dynamics; not a physical-accuracy claim.

## Run settings

- seed: 2026
- dt: 0.2
- n_steps: 240
- DM_POISON_PROXY_CALLS: 1

## Forward order

- pack: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\dm_c1_paper\pack_dm_c1_toy.json
- chi2.total: 2.409680769042054e-10
- ndof: 240
- dm_dynamics_core_used: True
- proxy_overlay_used: False
- stiffgate_in_evolution: True
- bounded.g_in_0_1: True
- bounded.epsilon_nonneg: True
- bounded.finite_all: True
- stability_not_accuracy: True

## Reverse order

- pack: C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git\out\dm_c1_paper\pack_dm_c1_toy.json
- chi2.total: 0.09799198619178467
- ndof: 240
- dm_dynamics_core_used: True
- proxy_overlay_used: False
- stiffgate_in_evolution: True
- bounded.g_in_0_1: True
- bounded.epsilon_nonneg: True
- bounded.finite_all: True
- stability_not_accuracy: True
