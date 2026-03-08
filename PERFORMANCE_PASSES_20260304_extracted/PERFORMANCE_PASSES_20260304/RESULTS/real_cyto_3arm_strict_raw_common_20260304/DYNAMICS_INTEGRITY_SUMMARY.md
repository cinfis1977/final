# Dynamics Integrity Summary

- Run root: `.\out\MS\real_cyto_3arm_strict_raw_common_20260304`
- Arms found: **6** (verdict: 6, audit: 6, telemetry: 6)
- Prereg all PASS: **True**
- Dynamics stateful all: **True**

## full

| Arm | Prereg | C1 | C2 | C3 | rank_corr_abs | third b2 | third b3 | stateful_steps | stateful_ok | anti_cancel_rankcorr |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1_B2 | PASS | True | True | True | 0.965035 | 0.874126 | 0.874126 | 527 | True | 0.615385 |
| A1_B3_holdout | PASS | True | True | True | 0.965035 | 0.874126 | 0.874126 | 527 | True | 0.636364 |
| A2_B3_thirdarm | PASS | True | True | True | 0.965035 | 0.874126 | 0.874126 | 527 | True | 0.727273 |

### Files

- **A1_B2**
  - folder: `full\A1_B2`
  - prereg verdict: `full\final\prereg_lock_and_final_verdict_goodppm3.json`
  - audit: `full\A1_B2\ms_dynamic_state_audit.json`
  - telemetry: `full\A1_B2\ms_dynamic_telemetry.json`
  - drift_common.csv: `full\A1_B2\drift_common.csv`
- **A1_B3_holdout**
  - folder: `full\A1_B3_holdout`
  - prereg verdict: `full\final\prereg_lock_and_final_verdict_goodppm3.json`
  - audit: `full\A1_B3_holdout\ms_dynamic_state_audit.json`
  - telemetry: `full\A1_B3_holdout\ms_dynamic_telemetry.json`
  - drift_common.csv: `full\A1_B3_holdout\drift_common.csv`
- **A2_B3_thirdarm**
  - folder: `full\A2_B3_thirdarm`
  - prereg verdict: `full\final\prereg_lock_and_final_verdict_goodppm3.json`
  - audit: `full\A2_B3_thirdarm\ms_dynamic_state_audit.json`
  - telemetry: `full\A2_B3_thirdarm\ms_dynamic_telemetry.json`
  - drift_common.csv: `full\A2_B3_thirdarm\drift_common.csv`

## internal_only

| Arm | Prereg | C1 | C2 | C3 | rank_corr_abs | third b2 | third b3 | stateful_steps | stateful_ok | anti_cancel_rankcorr |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1_B2 | PASS | True | True | True | 0.965035 | 0.874126 | 0.874126 | 527 | True | 0.475524 |
| A1_B3_holdout | PASS | True | True | True | 0.965035 | 0.874126 | 0.874126 | 527 | True | 0.706294 |
| A2_B3_thirdarm | PASS | True | True | True | 0.965035 | 0.874126 | 0.874126 | 527 | True | 0.769231 |

### Files

- **A1_B2**
  - folder: `internal_only\A1_B2`
  - prereg verdict: `internal_only\final\prereg_lock_and_final_verdict_goodppm3.json`
  - audit: `internal_only\A1_B2\ms_dynamic_state_audit.json`
  - telemetry: `internal_only\A1_B2\ms_dynamic_telemetry.json`
  - drift_common.csv: `internal_only\A1_B2\drift_common.csv`
- **A1_B3_holdout**
  - folder: `internal_only\A1_B3_holdout`
  - prereg verdict: `internal_only\final\prereg_lock_and_final_verdict_goodppm3.json`
  - audit: `internal_only\A1_B3_holdout\ms_dynamic_state_audit.json`
  - telemetry: `internal_only\A1_B3_holdout\ms_dynamic_telemetry.json`
  - drift_common.csv: `internal_only\A1_B3_holdout\drift_common.csv`
- **A2_B3_thirdarm**
  - folder: `internal_only\A2_B3_thirdarm`
  - prereg verdict: `internal_only\final\prereg_lock_and_final_verdict_goodppm3.json`
  - audit: `internal_only\A2_B3_thirdarm\ms_dynamic_state_audit.json`
  - telemetry: `internal_only\A2_B3_thirdarm\ms_dynamic_telemetry.json`
  - drift_common.csv: `internal_only\A2_B3_thirdarm\drift_common.csv`
