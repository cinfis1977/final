# Dynamics Integrity Summary

- Run root: `.\out\MS\ms_strict_raw_common_full_local`
- Arms found: **3** (verdict: 3, audit: 3, telemetry: 3)
- Prereg all PASS: **True**
- Dynamics stateful all: **True**

## full

| Arm | Prereg | C1 | C2 | C3 | rank_corr_abs | third b2 | third b3 | stateful_steps | stateful_ok | anti_cancel_rankcorr |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1_B2 | PASS | True | True | True | 0.965035 | 0.853147 | 0.853147 | 527 | True | 0.615385 |
| A1_B3_holdout | PASS | True | True | True | 0.965035 | 0.853147 | 0.853147 | 527 | True | 0.636364 |
| A2_B3_thirdarm | PASS | True | True | True | 0.965035 | 0.853147 | 0.853147 | 527 | True | 0.797203 |

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
