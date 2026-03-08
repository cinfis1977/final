# Photon sky-fold provenance diagnostic
- input = C:\Dropbox\projects\new_master_equation_with_gauge_structure_test\out\quasar_jet_matches_v1.csv
- coord_col = qso_dec_deg
- beta_col = delta_wrap90_deg
- ra_col = qso_ra_deg
- target paper p-value = 0.1536
- n_rows = 84
- permutation null = 5000 shuffles, seed 12345

## Closest partitions

### 1. ra_hemisphere
- rule = cos(qso_ra_deg - 164 deg) >= 0
- metric = abs
- statistic = -4.11556064073
- p_value_signed = 0.0798
- p_value_abs = 0.1544
- |p_abs - target| = 0.0008
- n_pos = 46, n_neg = 38

### 2. ra_hemisphere
- rule = cos(qso_ra_deg - 344 deg) >= 0
- metric = abs
- statistic = 4.11556064073
- p_value_signed = 0.0798
- p_value_abs = 0.1544
- |p_abs - target| = 0.0008
- n_pos = 38, n_neg = 46

### 3. dec_threshold
- rule = qso_dec_deg >= 11.730833
- metric = signed
- statistic = -8.18244514107
- p_value_signed = 0.0792
- p_value_abs = 0.1588
- |p_abs - target| = 0.0052
- n_pos = 29, n_neg = 55

### 4. dec_threshold
- rule = qso_dec_deg >= 55.382778
- metric = signed
- statistic = -13.2105263158
- p_value_signed = 0.0806
- p_value_abs = 0.159
- |p_abs - target| = 0.0054
- n_pos = 8, n_neg = 76

### 5. dec_threshold
- rule = qso_dec_deg >= 29.245556
- metric = signed
- statistic = -9.06963562753
- p_value_signed = 0.0808
- p_value_abs = 0.1626
- |p_abs - target| = 0.009
- n_pos = 19, n_neg = 65

### 6. ra_hemisphere
- rule = cos(qso_ra_deg - 44 deg) >= 0
- metric = abs
- statistic = 4.03636363636
- p_value_signed = 0.0842
- p_value_abs = 0.1636
- |p_abs - target| = 0.01
- n_pos = 40, n_neg = 44

### 7. ra_hemisphere
- rule = cos(qso_ra_deg - 45 deg) >= 0
- metric = abs
- statistic = 4.03636363636
- p_value_signed = 0.0842
- p_value_abs = 0.1636
- |p_abs - target| = 0.01
- n_pos = 40, n_neg = 44

### 8. ra_hemisphere
- rule = cos(qso_ra_deg - 46 deg) >= 0
- metric = abs
- statistic = 4.03636363636
- p_value_signed = 0.0842
- p_value_abs = 0.1636
- |p_abs - target| = 0.01
- n_pos = 40, n_neg = 44

### 9. ra_hemisphere
- rule = cos(qso_ra_deg - 47 deg) >= 0
- metric = abs
- statistic = 4.03636363636
- p_value_signed = 0.0842
- p_value_abs = 0.1636
- |p_abs - target| = 0.01
- n_pos = 40, n_neg = 44

### 10. ra_hemisphere
- rule = cos(qso_ra_deg - 224 deg) >= 0
- metric = abs
- statistic = -4.03636363636
- p_value_signed = 0.0842
- p_value_abs = 0.1636
- |p_abs - target| = 0.01
- n_pos = 44, n_neg = 40

### 11. ra_hemisphere
- rule = cos(qso_ra_deg - 225 deg) >= 0
- metric = abs
- statistic = -4.03636363636
- p_value_signed = 0.0842
- p_value_abs = 0.1636
- |p_abs - target| = 0.01
- n_pos = 44, n_neg = 40

### 12. ra_hemisphere
- rule = cos(qso_ra_deg - 226 deg) >= 0
- metric = abs
- statistic = -4.03636363636
- p_value_signed = 0.0842
- p_value_abs = 0.1636
- |p_abs - target| = 0.01
- n_pos = 44, n_neg = 40

## Interpretation boundary
- This is a provenance diagnostic only.
- A numerically close partition does not prove canonical identity.
- Canonical status still requires an archived source table plus exact fold-rule evidence tied to the paper benchmark.
