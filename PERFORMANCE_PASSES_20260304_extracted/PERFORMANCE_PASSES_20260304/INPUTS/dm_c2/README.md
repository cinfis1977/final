# DM-C2 packs

This folder contains DM-C2 pack artifacts derived from real SPARC points.

- Builder: `dm_c2_build_sparc_pack_v1.py`
- Default output: `integration_artifacts/mastereq/packs/dm_c2/dm_c2_sparc_pack_v1.json`
- Schema: `dm_c2_pack_v1`

Notes
- This is an IO/schema + runner-smoke surface. It is not a fit/accuracy claim.
- Units are chosen so the DM-C1 dynamics runner can compute `v_pred = sqrt(r * a_tot)` in km/s:
  - `r`: kpc
  - `a_bary`: (km/s)^2 / kpc
  - `v_obs`, `sigma_v`: km/s
