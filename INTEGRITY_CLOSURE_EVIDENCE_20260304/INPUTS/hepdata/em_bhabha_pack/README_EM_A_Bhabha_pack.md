# EM-A (Bhabha) pack + drop-in forward

This folder contains a **pack** in the same spirit as the ATLAS strong-elastic pack:
- **data CSV** with bin edges/centers + observable + errors
- **covariance matrices** (stat, sys, total, and diag_total)
- a **drop-in forward** script that reads the pack and outputs a per-bin debug CSV

## Files

- `lep_bhabha_pack.json`
- `lep_bhabha_table18_clean.csv`
- `lep_bhabha_cov_stat.csv` (diagonal)
- `lep_bhabha_cov_sys_corr.csv` (two sys sources treated as 100% correlated across bins)
- `lep_bhabha_cov_total.csv` (stat + sys)
- `lep_bhabha_cov_diag_total.csv` (diagonal-only total, for sanity checks)
- `em_bhabha_forward_dropin.py`

## Quick run example (Windows PowerShell)

```powershell
py -3 .\em_bhabha_forward_dropin.py `
  --pack .\em_bhabha_pack\lep_bhabha_pack.json `
  --cov total `
  --sqrt_s_GeV 189 `
  --A 0.0085 --alpha 7.5e-05 --phi 1.57079632679 `
  --geo_structure offdiag --geo_gen lam2 `
  --omega0_geom fixed --L0_km 810 `
  --zeta 0.05 --R_max 10 --t_ref_GeV 0.02 `
  --aic_k 2 `
  --out .\out_em_bhabha_debug.csv
```

Notes:
- `sqrt_s_GeV` is used only to build a **|t| proxy**: |t| ≈ s/2 (1-cosθ). If the table corresponds to a different energy, update it.
- The SM baseline is a **two-shape linear proxy**:
  β1/(1-c)^2 + β2/(1+c)^2 (β1,β2 refit each run, not counted in AIC/BIC).

## How to wire into your existing project tree

Suggested structure:

```
data/
  hepdata/
    em_bhabha_pack/
      lep_bhabha_pack.json
      lep_bhabha_table18_clean.csv
      lep_bhabha_cov_*.csv
scripts/
  em_bhabha_forward.py   (copy of em_bhabha_forward_dropin.py)
```

Then you can reuse your existing sweep/robustness harness by pointing `--forward` at `em_bhabha_forward.py`.
