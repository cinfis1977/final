# WEAK χ² construction audit (run02) — what χ² actually means here

Scope: This note documents **exactly** what statistic the WEAK runners compute and what inputs it consumes, so we can judge whether “χ²/ndof” is a meaningful *real-data closeness* test vs a debug-only distance.

## Evidence inputs (pack)

Pack inspected: `t2k_channels_real_approx.json`

Pack `meta.note` explicitly states this is a **NON-OFFICIAL approx pack** created by pixel-digitizing inset projections and is **“ONLY for rough debugging; NOT for claims/falsification.”** It also states (key):

- `N_sig_sm` is taken as digitized **“Best fit”** red curve
- `N_bkg_sm = 0` (no decomposition available in the figure)
- `N_obs` is digitized black-cross data, rounded

So: for this pack, `N_sig_sm` is *not guaranteed to be SM*, and it is *not guaranteed to be signal-only*.

## What the WEAK runners compute

There are two WEAK runners in this repo that print per-channel χ² and Δχ²:

- `nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py` (phase-shift / proxy-style)
- `nova_mastereq_forward_kernel_BREATH_THREAD_GKSL_DYNAMICS.py` (GKSL state evolution)

Both ultimately compute χ² via the same helper `chi2_gauss_loose`.

### Common data flow per channel (both runners)

From each `channel.bins`, they ingest arrays:

- `obs[i] := bins.N_obs[i]`
- `bkg_sm[i] := bins.N_bkg_sm[i]`
- `sig_sm[i] := bins.N_sig_sm[i]` (unless a special mode is enabled; see below)

Baseline prediction:

- `pred_sm[i] = sig_sm[i] + bkg_sm[i]`

Then they compute baseline and GEO probabilities per bin:

- `P_sm[i]` and `P_geo[i]` are probabilities on the reconstructed-energy bin centers

GEO prediction (legacy contract):

- `ratio[i] = P_geo[i] / P_sm[i]` (with floors to avoid division by 0)
- `sig_geo[i] = sig_sm[i] * ratio[i]`
- `pred_geo[i] = sig_geo[i] + bkg_sm[i]`

So, outside of `--use_rate_kernel`, **GEO is implemented as a multiplicative deformation of whatever the pack calls `N_sig_sm`.**

### Differences between the two runners

#### `...fixedbyclaude.py` (proxy-style)

- `P_geo` is computed by *phase-shifting* a reference probability curve.
- `P_sm` is obtained either from `N_sig_sm/N_sig_noosc` (if `N_sig_noosc` exists) or from a minimal built-in probability formula.
- It always consumes `bins.N_sig_sm` as the baseline rate.

#### `...GKSL_DYNAMICS.py` (dynamics)

- `P_sm` and `P_geo` are computed by integrating a GKSL equation per bin (optionally with matter and damping).
- In default mode it still consumes `bins.N_sig_sm` as the baseline rate, then applies the same `P_geo/P_sm` scaling.
- It has two special switches:
  - `--use_rate_model`: compute `sig_sm` from `bins.N_noosc` or `channel.rate_model` **instead of** `bins.N_sig_sm`.
  - `--use_rate_kernel`: compute `pred_sm/pred_geo` end-to-end from an internal rate kernel (flux×sigma×eff×smear×exposure) using state-derived probabilities.

## The χ² actually used: `chi2_gauss_loose`

Defined in `nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py` and imported/used by the GKSL runner.

Per bin $i$:

- $\mathrm{var}_i = \max(\mathrm{pred}_i, 1) + (f\,\mathrm{pred}_i)^2$ where $f = \texttt{--systfrac}$
- $$\chi^2 = \sum_i \frac{(\mathrm{obs}_i - \mathrm{pred}_i)^2}{\mathrm{var}_i}$$

Important: the function docstring says explicitly: **“NOT the publication-grade statistic; it’s for debug sanity only.”**

## What this χ² does NOT include (by construction)

This is a purely diagonal, per-bin Gaussian-ish distance with an ad-hoc variance model.

It does **not** include:

- A Poisson likelihood / official -2logL treatment (esp. relevant when counts are small)
- Any bin-to-bin covariance, correlated systematics, nuisance parameters, flux/xsec constraints, detector response uncertainties, etc.
- Any profiling/marginalization over oscillation + systematic parameters as in experiment fits
- Any guarantee that `N_sig_sm` corresponds to the SM prediction (pack-dependent)

## Consequences for the T2K approx pack specifically

Given the pack’s own metadata:

1) `N_sig_sm` is digitized **“best fit”** curve, not guaranteed to be the SM signal prediction.

2) `N_bkg_sm=0` means any true backgrounds are either omitted or implicitly folded into `N_sig_sm`.

3) Since GEO is applied by scaling `sig_sm` by `P_geo/P_sm`, **if `sig_sm` contains background-like structure**, GEO will scale it as if it were oscillation-driven signal. That breaks the intended semantics of the deformation.

Therefore, for this pack, large χ² or χ²/ndof is strong evidence of “the debug distance is large”, but it is **not** evidence of a publication-grade “real-data closeness test” failing.

## Practical next step (if you want a meaningful closeness test)

To upgrade WEAK “closeness” from debug-distance to something interpretable, we need at least one of:

- An official pack with (a) a clean prediction decomposition and (b) an experimental covariance / likelihood surrogate, or
- A pack with a `channel.rate_kernel` so `--use_rate_kernel` can generate *signal* rates from physics inputs (still needs a systematics model for a real χ²), or
- A dedicated likelihood definition for the approx pack that matches what was digitized (and clearly labeled as approximate).
