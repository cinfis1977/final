# Dynamics Integrity Summary

- Run root: `.\out\MS\ms_strict_raw_common_local`
- Arms found: **3** (verdict: 3, audit: 3, telemetry: 3)
- Prereg all PASS: **True**
- Dynamics stateful all: **True**

## internal_only

| Arm | Prereg | C1 | C2 | C3 | rank_corr_abs | third b2 | third b3 | stateful_steps | stateful_ok | anti_cancel_rankcorr |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1_B2 | PASS | True | True | True | 0.965035 | 0.853147 | 0.853147 | 527 | True | 0.475524 |
| A1_B3_holdout | PASS | True | True | True | 0.965035 | 0.853147 | 0.853147 | 527 | True | 0.706294 |
| A2_B3_thirdarm | PASS | True | True | True | 0.965035 | 0.853147 | 0.853147 | 527 | True | 0.741259 |

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
