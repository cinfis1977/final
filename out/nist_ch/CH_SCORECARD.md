# NIST CH/Eberhard scorecard

| run_id | label         | window   | slots | bitmask_hex | trials_valid | J   | J_per_1M | N_pp_ab | N_p0_abp | N_0p_apb | N_pp_apbp | dropped_invalid_settings |
| ------ | ------------- | -------- | ----- | ----------- | ------------ | --- | -------- | ------- | -------- | -------- | --------- | ------------------------ |
| 01_11  | real_run      | slot6    | 6     | 0x20        | 337818518    | 122 | 0.361141 | 2416    | 1101     | 1177     | 16        | 121                      |
| 01_11  | real_run      | slots5-7 | 5-7   | 0x70        | 337818518    | 398 | 1.17815  | 7248    | 3314     | 3473     | 63        | 121                      |
| 01_11  | real_run      | slots4-8 | 4-8   | 0xf8        | 337818518    | 550 | 1.62809  | 12082   | 5580     | 5836     | 116       | 121                      |
| 02_54  | real_run      | slot6    | 6     | 0x20        | 203681460    | 8   | 0.039277 | 1348    | 641      | 686      | 13        | 2                        |
| 02_54  | real_run      | slots5-7 | 5-7   | 0x70        | 203681460    | 41  | 0.201295 | 3983    | 1882     | 2022     | 38        | 2                        |
| 02_54  | real_run      | slots4-8 | 4-8   | 0xf8        | 203681460    | 176 | 0.864094 | 6653    | 3095     | 3312     | 70        | 2                        |
| 03_31  | training_stub | slot6    | 6     | 0x20        | 363          | 0   | 0        | 0       | 0        | 0        | 0         | 0                        |
| 03_31  | training_stub | slots5-7 | 5-7   | 0x70        | 363          | 0   | 0        | 0       | 0        | 0        | 0         | 0                        |
| 03_31  | training_stub | slots4-8 | 4-8   | 0xf8        | 363          | 0   | 0        | 0       | 0        | 0        | 0         | 0                        |
| 03_43  | real_run      | slot6    | 6     | 0x20        | 107109594    | 13  | 0.121371 | 783     | 370      | 391      | 9         | 2                        |
| 03_43  | real_run      | slots5-7 | 5-7   | 0x70        | 107109594    | 49  | 0.457475 | 2348    | 1082     | 1187     | 30        | 2                        |
| 03_43  | real_run      | slots4-8 | 4-8   | 0xf8        | 107109594    | 151 | 1.40977  | 3953    | 1801     | 1947     | 54        | 2                        |

## Notes
- `J = N(++|ab) - N(+0|ab') - N(0+|a'b) - N(++|a'b')`; local realism bound is `J <= 0` (violation if `J > 0`).
- `trials_valid` is the sum of per-setting valid trials from `*.counts.csv` (preferred over scanned count).