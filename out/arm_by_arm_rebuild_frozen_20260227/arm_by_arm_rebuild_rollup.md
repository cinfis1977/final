# Arm-by-Arm Frozen Rebuild Rollup

| run | matched_pairs | class_changes | conf_changes | shell_monotonicity | anchor T02<->T03 | anchor T12<->T07 | verdict |
|---|---:|---:|---:|---|---|---|---|
| A1_B2_ModeA | 21 | 0 | 1 | OK | STABLE-INTERMEDIATE-CANDIDATE->STABLE-INTERMEDIATE-CANDIDATE;STRONG_STABLE->STRONG_STABLE | REPULSIVE->REPULSIVE;STRONG_REPULSIVE->STRONG_REPULSIVE | PASS-DIAGNOSTIC-REBUILD |
| A1_B2_ModeB | 21 | 0 | 1 | OK | STABLE-INTERMEDIATE-CANDIDATE->STABLE-INTERMEDIATE-CANDIDATE;STRONG_STABLE->STRONG_STABLE | REPULSIVE->REPULSIVE;STRONG_REPULSIVE->STRONG_REPULSIVE | PASS-DIAGNOSTIC-REBUILD |
| A1_B2_direct_ModeB_holdout | 21 | 0 | 1 | OK | STABLE-INTERMEDIATE-CANDIDATE->STABLE-INTERMEDIATE-CANDIDATE;STRONG_STABLE->STRONG_STABLE | REPULSIVE->REPULSIVE;STRONG_REPULSIVE->STRONG_REPULSIVE | PASS-DIAGNOSTIC-REBUILD |
| Combined_A1_B2_plus_holdout | 21 | 0 | 1 | OK | STABLE-INTERMEDIATE-CANDIDATE->STABLE-INTERMEDIATE-CANDIDATE;STRONG_STABLE->STRONG_STABLE | REPULSIVE->REPULSIVE;STRONG_REPULSIVE->STRONG_REPULSIVE | PASS-DIAGNOSTIC-REBUILD |

## Shell Distribution
- A1_B2_ModeA: adjacent(S:8 R:3 I:0), next_nearest(S:5 R:5 I:0)
- A1_B2_ModeB: adjacent(S:8 R:3 I:0), next_nearest(S:5 R:5 I:0)
- A1_B2_direct_ModeB_holdout: adjacent(S:8 R:3 I:0), next_nearest(S:5 R:5 I:0)
- Combined_A1_B2_plus_holdout: adjacent(S:8 R:3 I:0), next_nearest(S:5 R:5 I:0)

## Direct Answer
- Not only a pooled-data effect: the same skeleton survives in each arm individually.

