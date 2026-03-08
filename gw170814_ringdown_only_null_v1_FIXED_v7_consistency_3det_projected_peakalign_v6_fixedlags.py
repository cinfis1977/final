#!/usr/bin/env python3
"""
GW150914 ringdown-only comparison (toy model vs LIGO strain) + off-source null test.

This script is intentionally *simple and robust*:
- Anchor step (35-350 Hz by default): find H1 peak near center_guess_gps and estimate H1->L1 lag by maximizing
  cross-correlation in a small lag window.
- Analysis step (e.g. 80-300 Hz): cut a *ringdown* segment starting at t_peak + ringdown_start_s of length ringdown_dur_s.
- Whitening via Welch PSD (estimated from the full 32s record excluding a guard around the segment).
- Compare whitened data to a supplied model time series (CSV) by normalized inner product, scanning time_scale and small model lag.
- Off-source null: repeat the same pipeline at random off-source centers to get a p-value.

Outputs:
- <out_prefix>.summary.json
- <out_prefix>.offsource.csv
- <out_prefix>_event_overlay_{H1,L1,AVG}.png   (if --plot_png is provided)
- <out_prefix>_null_hist.png                  (if --plot_png is provided)

Requires: numpy, pandas, scipy, matplotlib, h5py
"""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional, List

import numpy as np
import pandas as pd
import h5py
import datetime as _dt
from scipy import signal
import matplotlib.pyplot as plt


# -------------------------
# Antenna pattern helper (no external deps)
# -------------------------
# We use detector arm unit vectors in Earth-centered Earth-fixed (ECEF) coordinates from LALSuite.
# This lets us compute (F+, Fx) given an approximate sky location (RA/Dec) and polarization angle psi.
#
# Notes:
# - We treat GPS seconds as UTC for sidereal-time purposes (leap-second difference is negligible for this use).
# - This is meant for *sanity* / coherence checks, not precision PE.
#
# References for detector geometry:
#   - LALSuite "Detector Constants" (arm direction unit vectors in Earth-centered frame).
#
DETECTOR_ARMS_ECEF = {
    "H1": {
        "ux": np.array([-0.22389266154,  0.79983062746,  0.55690487831], dtype=float),
        "uy": np.array([-0.91397818574,  0.02609403989, -0.40492342125], dtype=float),
    },
    "L1": {
        "ux": np.array([-0.95457412153, -0.14158077340, -0.26218911324], dtype=float),
        "uy": np.array([ 0.29774156894, -0.48791033647, -0.82054461286], dtype=float),
    },
    "V1": {
        "ux": np.array([-0.70045821479,  0.20848948619,  0.68256166277], dtype=float),
        "uy": np.array([-0.05379255368, -0.96908220039,  0.24080451708], dtype=float),
    },
}

EVENT_RADECS_DEG = {
    # From the GW170814 discovery letter: maximum-a-posteriori sky position ~ RA=03h11m, Dec=-44°57'.
    # (Convert to degrees: 3h = 45°, 11m = 2.75° => 47.75°; 57' = 0.95° => -44.95°)
    "gw170814": {"ra_deg": 47.75, "dec_deg": -44.95},
}

def _julian_date_from_datetime(dt: _dt.datetime) -> float:
    """Julian Date (UTC) from a naive datetime assumed UTC."""
    # Algorithm from Meeus (astronomical formulas). Good to <1s for our purposes.
    y = dt.year
    m = dt.month
    d = dt.day + (dt.hour + (dt.minute + dt.second / 60.0) / 60.0) / 24.0

    if m <= 2:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
    return float(jd)

def _gmst_rad_from_jd(jd_ut1: float) -> float:
    """Greenwich mean sidereal time (radians). IAU 1982-ish formula."""
    T = (jd_ut1 - 2451545.0) / 36525.0
    gmst_sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * T + 0.093104 * (T ** 2) - 6.2e-6 * (T ** 3)
    gmst_sec = gmst_sec % 86400.0
    return float(gmst_sec * (2.0 * np.pi / 86400.0))

def _r3(theta: float) -> np.ndarray:
    """Rotation about +z by angle theta (radians)."""
    c = float(np.cos(theta))
    s = float(np.sin(theta))
    return np.array([[ c,  s, 0.0],
                     [-s,  c, 0.0],
                     [0.0, 0.0, 1.0]], dtype=float)

def _detector_tensor(ux: np.ndarray, uy: np.ndarray) -> np.ndarray:
    # d_ij = (u_i u_j - v_i v_j)/2
    return 0.5 * (np.outer(ux, ux) - np.outer(uy, uy))

def _polarization_tensors(n_ecef: np.ndarray, psi_rad: float) -> Tuple[np.ndarray, np.ndarray]:
    """Return (e_plus, e_cross) in ECEF for propagation direction n (unit, from origin to source)."""
    n = n_ecef / max(float(np.linalg.norm(n_ecef)), 1e-30)

    z = np.array([0.0, 0.0, 1.0], dtype=float)
    p0 = np.cross(z, n)
    if float(np.linalg.norm(p0)) < 1e-6:
        # near pole: use x-axis
        p0 = np.cross(np.array([1.0, 0.0, 0.0], dtype=float), n)
    p = p0 / max(float(np.linalg.norm(p0)), 1e-30)
    q = np.cross(n, p)

    cp = float(np.cos(psi_rad))
    sp = float(np.sin(psi_rad))
    ppsi = cp * p + sp * q
    qpsi = -sp * p + cp * q

    e_plus = np.outer(ppsi, ppsi) - np.outer(qpsi, qpsi)
    e_cross = np.outer(ppsi, qpsi) + np.outer(qpsi, ppsi)
    return e_plus, e_cross

def antenna_patterns_from_radec(
    gps: float,
    ra_deg: float,
    dec_deg: float,
    psi_deg: float = 0.0,
) -> Dict[str, Tuple[float, float]]:
    """Compute (F+, Fx) for H1/L1/V1 given sky location and polarization angle."""
    # Approximate UTC from GPS epoch.
    gps0 = _dt.datetime(1980, 1, 6, 0, 0, 0)  # naive UTC
    dt = gps0 + _dt.timedelta(seconds=float(gps))
    jd = _julian_date_from_datetime(dt)
    theta = _gmst_rad_from_jd(jd)

    ra = float(np.deg2rad(ra_deg))
    dec = float(np.deg2rad(dec_deg))
    psi = float(np.deg2rad(psi_deg))

    # Source direction in ECI (equatorial): n points from Earth to source.
    n_eci = np.array([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)], dtype=float)

    # Rotate to ECEF using GMST.
    n_ecef = _r3(theta) @ n_eci

    e_plus, e_cross = _polarization_tensors(n_ecef, psi)

    out: Dict[str, Tuple[float, float]] = {}
    for det, arms in DETECTOR_ARMS_ECEF.items():
        d = _detector_tensor(arms["ux"], arms["uy"])
        Fp = float(np.sum(d * e_plus))
        Fx = float(np.sum(d * e_cross))
        out[det] = (Fp, Fx)
    return out


# -------------------------
# Utilities
# -------------------------

def parse_band(s: str) -> Tuple[float, float]:
    parts = [p.strip() for p in s.split(",")]
    if len(parts) != 2:
        raise ValueError(f"Band must be 'f_lo,f_hi' got: {s}")
    return float(parts[0]), float(parts[1])

def parse_floats_csv(s: str) -> List[float]:
    return [float(x.strip()) for x in s.split(",") if x.strip()]

def tukey_window(n: int, alpha: float = 0.1) -> np.ndarray:
    # robust across SciPy versions
    try:
        return signal.windows.tukey(n, alpha=alpha)
    except Exception:
        # fallback: cosine taper
        w = np.ones(n, dtype=float)
        m = int(alpha * (n - 1) / 2)
        if m <= 1:
            return w
        x = np.linspace(0, math.pi, m)
        taper = 0.5 * (1 - np.cos(x))
        w[:m] = taper
        w[-m:] = taper[::-1]
        return w

def bandpass_filt(x: np.ndarray, fs: float, band: Tuple[float, float], order: int = 4) -> np.ndarray:
    f_lo, f_hi = band
    nyq = 0.5 * fs
    lo = max(f_lo / nyq, 1e-6)
    hi = min(f_hi / nyq, 0.999999)
    if not (0 < lo < hi < 1):
        raise ValueError(f"Invalid band after normalization: {band} for fs={fs}")
    b, a = signal.butter(order, [lo, hi], btype="bandpass")
    return signal.filtfilt(b, a, x)

def welch_psd(x: np.ndarray, fs: float, nperseg: int = 4096, noverlap: int = 2048) -> Tuple[np.ndarray, np.ndarray]:
    f, pxx = signal.welch(x, fs=fs, window="hann", nperseg=nperseg, noverlap=noverlap, detrend="constant", scaling="density")
    # avoid zeros
    pxx = np.maximum(pxx, 1e-30)
    return f, pxx

def whiten_fft(x: np.ndarray, fs: float, psd_f: np.ndarray, psd_pxx: np.ndarray) -> np.ndarray:
    """Frequency-domain whitening using PSD. Returns real whitened time series (same length)."""
    n = len(x)
    win = tukey_window(n, alpha=0.1)
    xw = x * win
    X = np.fft.rfft(xw)
    freqs = np.fft.rfftfreq(n, d=1.0/fs)
    P = np.interp(freqs, psd_f, psd_pxx)
    W = X / np.sqrt(P)
    y = np.fft.irfft(W, n=n)
    # normalize (optional): keep overall scale reasonable
    y = y / (np.std(y) + 1e-12)
    return y

def norm_corr(a: np.ndarray, b: np.ndarray) -> float:
    """Normalized dot (cosine similarity) on the overlapping prefix.

    We intentionally allow off-by-one length differences (common when converting
    fixed lags in seconds to integer samples). We compute correlation on the
    common overlap to avoid crashes without introducing any new scan freedom.
    """
    n = min(len(a), len(b))
    if n <= 1:
        return 0.0
    a = a[:n]
    b = b[:n]
    a0 = a - np.mean(a)
    b0 = b - np.mean(b)
    na = np.linalg.norm(a0)
    nb = np.linalg.norm(b0)
    if (not np.isfinite(na)) or (not np.isfinite(nb)) or na < 1e-30 or nb < 1e-30:
        return 0.0
    return float(np.dot(a0, b0) / (na * nb))

def shift_samples(x: np.ndarray, k: int) -> np.ndarray:
    """Shift by k samples (positive => delay), padding with zeros."""
    if k == 0:
        return x.copy()
    n = len(x)
    y = np.zeros_like(x)
    if k > 0:
        y[k:] = x[:n-k]
    else:
        kk = -k
        y[:n-kk] = x[kk:]
    return y

@dataclass
class GWSeries:
    det: str
    fs: float
    t0_gps: float
    strain: np.ndarray

    def time_axis(self) -> np.ndarray:
        return self.t0_gps + np.arange(len(self.strain)) / self.fs

def load_gwosc_hdf5(path: str, det_label: str) -> GWSeries:
    with h5py.File(path, "r") as f:
        s = np.array(f["strain"]["Strain"], dtype=float)
        dt = float(f["strain"]["Strain"].attrs["Xspacing"])
        fs = 1.0 / dt
        t0 = float(f["meta"]["GPSstart"][()])
    return GWSeries(det=det_label, fs=fs, t0_gps=t0, strain=s)

def read_model_csv(path: str, t_col: str, y_col: str) -> Tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    if t_col not in df.columns:
        raise ValueError(f"Model CSV missing t_col={t_col}. Have columns: {list(df.columns)}")
    if y_col not in df.columns:
        raise ValueError(f"Model CSV missing model_col={y_col}. Have columns: {list(df.columns)}")
    t = df[t_col].to_numpy(dtype=float)
    y = df[y_col].to_numpy(dtype=float)
    # ensure sorted
    idx = np.argsort(t)
    t = t[idx]
    y = y[idx]
    # normalize amplitude (scale later)
    y = y - np.mean(y)
    y = y / (np.std(y) + 1e-12)
    return t, y

def read_model_csv_raw2(path: str, t_col: str, y_col_plus: str, y_col_cross: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read plus/cross columns from model CSV WITHOUT per-column standardization.
    We only demean each column; scaling is preserved so linear combinations are physical.
    """
    df = pd.read_csv(path)
    if t_col not in df.columns:
        raise ValueError(f"Model CSV missing t_col={t_col}. Have columns: {list(df.columns)}")
    for c in (y_col_plus, y_col_cross):
        if c not in df.columns:
            raise ValueError(f"Model CSV missing column={c}. Have columns: {list(df.columns)}")
    t = df[t_col].to_numpy(dtype=float)
    y_plus = df[y_col_plus].to_numpy(dtype=float)
    y_cross = df[y_col_cross].to_numpy(dtype=float)
    idx = np.argsort(t)
    t = t[idx]
    y_plus = y_plus[idx]
    y_cross = y_cross[idx]
    # demean only (keep relative amplitude)
    y_plus = y_plus - np.mean(y_plus)
    y_cross = y_cross - np.mean(y_cross)
    return t, y_plus, y_cross

def standardize_series(y: np.ndarray) -> np.ndarray:
    y0 = y - np.mean(y)
    s = np.std(y0)
    return y0 / (s + 1e-12)

def sample_model_segment(t_model: np.ndarray, y_model: np.ndarray, fs: float, seg_len_s: float,
                         time_scale: float, lag_s: float) -> np.ndarray:
    """
    Create a model segment sampled at fs with duration seg_len_s.

    time scaling: m(t) = y_model(t / time_scale)
      - time_scale > 1 stretches (slower), < 1 compresses (faster)

    lag_s shifts the model relative to data: positive lag => model delayed.
    """
    n = int(round(seg_len_s * fs))
    t_data = np.arange(n) / fs
    # apply lag: data time t corresponds to model time (t - lag) / time_scale
    t_query = (t_data - lag_s) / max(time_scale, 1e-9)
    y = np.interp(t_query, t_model, y_model, left=0.0, right=0.0)
    # normalize
    y = y - np.mean(y)
    y = y / (np.std(y) + 1e-12)
    return y

def find_anchor_peak_and_lag(h1: GWSeries, l1: GWSeries, center_guess_gps: float,
                             anchor_band: Tuple[float, float],
                             peak_search_halfwin_s: float,
                             lag_search_s: float,
                             lag_window_s: float,
                             n_peak_candidates: int = 8,
                             min_peak_sep_s: float = 0.008) -> Dict[str, float]:
    """
    Coherent anchor (data-only):

      1) Bandpass both detectors in anchor_band.
      2) In H1, inside [center_guess_gps ± peak_search_halfwin_s], collect top-N peaks of |H1|.
         (Enforce a minimum separation to avoid choosing multiple samples from the same peak.)
      3) For each candidate peak, compute the best H1->L1 lag (within ±lag_search_s) that maximizes |corr|
         between an H1 window and an L1 window shifted by that lag.
      4) Choose the candidate peak whose best |corr| is largest (coherence-driven peak selection).

    Conventions:
      - anchor_lag_s > 0 means L1 arrives later than H1 by anchor_lag_s (H1->L1).
      - We report signed corr at the selected lag, and anchor_abs_corr = |corr|.

    Notes:
      - This avoids locking onto a loud single-detector glitch: the chosen peak must be coherent with the other detector.
    """
    fs = h1.fs
    if abs(l1.fs - fs) > 1e-6:
        raise ValueError("H1 and L1 sampling rates differ; resampling not implemented here.")

    # Bandpass full records (32s is fine)
    xh = bandpass_filt(h1.strain, fs, anchor_band)
    xl = bandpass_filt(l1.strain, fs, anchor_band)

    t = h1.time_axis()
    n = len(t)

    center_idx = int(np.argmin(np.abs(t - center_guess_gps)))
    half = int(round(peak_search_halfwin_s * fs))
    lo = max(0, center_idx - half)
    hi = min(n, center_idx + half + 1)
    if hi - lo < 64:
        raise RuntimeError("Peak search window too small / outside data range (check center_guess_gps).")

    # --- candidate peaks (by |H1|), with simple non-maximum suppression ---
    min_sep = max(int(round(min_peak_sep_s * fs)), 1)
    local = np.abs(xh[lo:hi]).copy()
    order = np.argsort(local)[::-1]  # descending
    cand_idx: List[int] = []
    for j in order:
        i = lo + int(j)
        if all(abs(i - k) >= min_sep for k in cand_idx):
            cand_idx.append(i)
            if len(cand_idx) >= max(1, n_peak_candidates):
                break
    if not cand_idx:
        # fallback: global max
        cand_idx = [lo + int(np.argmax(np.abs(xh[lo:hi])))]

    # window length for correlation
    w = int(round(lag_window_s * fs))
    w = max(w, 128)

    max_lag_samp = int(round(lag_search_s * fs))

    best = {
        "abs_corr": -1.0,
        "corr": 0.0,
        "lag_samp": 0,
        "i_peak": cand_idx[0],
    }

    for i_peak in cand_idx:
        # clamp window around i_peak
        a0 = i_peak - w // 2
        a1 = a0 + w
        if a0 < 0:
            a0 = 0
            a1 = a0 + w
        if a1 > n:
            a1 = n
            a0 = max(0, a1 - w)
        if a1 - a0 < 64:
            continue

        seg_h = xh[a0:a1]

        # scan lags
        local_best_abs = -1.0
        local_best_corr = 0.0
        local_best_k = 0

        for k in range(-max_lag_samp, max_lag_samp + 1):
            b0 = a0 + k
            b1 = a1 + k
            if b0 < 0 or b1 > n:
                continue
            c = norm_corr(seg_h, xl[b0:b1])
            ac = abs(c)
            if ac > local_best_abs:
                local_best_abs = ac
                local_best_corr = c
                local_best_k = k

        if local_best_abs > best["abs_corr"]:
            best["abs_corr"] = local_best_abs
            best["corr"] = local_best_corr
            best["lag_samp"] = local_best_k
            best["i_peak"] = i_peak

    anchor_lag_s = float(best["lag_samp"] / fs)
    edge_hit = (best["lag_samp"] == -max_lag_samp) or (best["lag_samp"] == max_lag_samp)
    t_peak = float(t[int(best["i_peak"])])
    t_peak_l1 = t_peak + anchor_lag_s

    return {
        "t_peak_h1": float(t_peak),
        "t_peak_l1": float(t_peak_l1),
        "anchor_lag_s": float(anchor_lag_s),
        "anchor_corr": float(best["corr"]),
        "anchor_abs_corr": float(abs(best["corr"])),
        "anchor_edge_hit": bool(edge_hit),
        "anchor_peak_candidates": int(len(cand_idx)),
    }


def find_anchor_peak_and_lag_3(h1: GWSeries, l1: GWSeries, v1: GWSeries, center_guess_gps: float,
                               anchor_band: Tuple[float, float],
                               peak_search_halfwin_s: float,
                               lag_search_s: float,
                               lag_window_s: float,
                               n_peak_candidates: int = 8,
                               min_peak_sep_s: float = 0.008) -> Dict[str, float]:
    """
    3-detector coherence-driven anchor.

    Strategy:
      - Use H1 as reference.
      - In anchor_band, pick candidate peaks in |H1| within [center_guess ± halfwin].
      - For each candidate, find best H1->L1 lag and best H1->V1 lag (within ±lag_search_s)
        maximizing |corr| over a lag_window_s window.
      - Score candidates by the MIN of the two abs correlations (forces coherence in both baselines).
      - Return peak times and both lags.

    Conventions:
      - lag_h1_l1_s > 0 means L1 arrives later than H1.
      - lag_h1_v1_s > 0 means V1 arrives later than H1.
    """
    fs = h1.fs
    if abs(l1.fs - fs) > 1e-9 or abs(v1.fs - fs) > 1e-9:
        raise RuntimeError("Sampling rates must match for coherent anchor.")

    # Anchor-band bandpass
    h1_bp = bandpass_filt(h1.strain, fs, anchor_band)
    l1_bp = bandpass_filt(l1.strain, fs, anchor_band)
    v1_bp = bandpass_filt(v1.strain, fs, anchor_band)

    t = h1.time_axis()
    wmask = (t >= center_guess_gps - peak_search_halfwin_s) & (t <= center_guess_gps + peak_search_halfwin_s)
    idxw = np.where(wmask)[0]
    if len(idxw) < int(0.2 * peak_search_halfwin_s * fs):
        raise RuntimeError("Anchor peak search window out of range.")

    # candidate peaks = top-N of |H1|, enforce min separation
    abs_h1 = np.abs(h1_bp[idxw])
    order = np.argsort(abs_h1)[::-1]  # descending
    candidates = []
    for oi in order:
        i = idxw[oi]
        if all(abs(i - j) >= int(min_peak_sep_s * fs) for j in candidates):
            candidates.append(i)
        if len(candidates) >= n_peak_candidates:
            break
    if not candidates:
        raise RuntimeError("No anchor peak candidates found.")

    # helper to compute best lag against a target series
    def best_lag_and_corr(ref_bp: np.ndarray, tgt_bp: np.ndarray, i_peak: int) -> Tuple[float, float]:
        half = int(round(0.5 * lag_window_s * fs))
        i1 = max(i_peak - half, 0)
        i2 = min(i_peak + half, len(ref_bp))
        ref_win = ref_bp[i1:i2]
        if len(ref_win) < int(0.5 * lag_window_s * fs):
            return 0.0, 0.0

        max_k = int(round(lag_search_s * fs))
        best_abs = -1.0
        best_corr = 0.0
        best_k = 0
        for k in range(-max_k, max_k + 1):
            tgt_win = tgt_bp[i1 + k:i2 + k] if (i1 + k >= 0 and i2 + k <= len(tgt_bp)) else None
            if tgt_win is None or len(tgt_win) != len(ref_win):
                continue
            c = norm_corr(ref_win, tgt_win)
            a = abs(c)
            if a > best_abs:
                best_abs = a
                best_corr = c
                best_k = k
        lag_s = best_k / fs
        return lag_s, best_corr

    best_score = -1.0
    best = None
    for i_peak in candidates:
        lag_l1, corr_l1 = best_lag_and_corr(h1_bp, l1_bp, i_peak)
        lag_v1, corr_v1 = best_lag_and_corr(h1_bp, v1_bp, i_peak)
        a_l1, a_v1 = abs(corr_l1), abs(corr_v1)
        score = min(a_l1, a_v1)
        if score > best_score:
            best_score = score
            best = (i_peak, lag_l1, corr_l1, lag_v1, corr_v1)

    i_peak, lag_l1, corr_l1, lag_v1, corr_v1 = best
    t_peak_h1 = float(t[i_peak])
    t_peak_l1 = float(t_peak_h1 + lag_l1)
    t_peak_v1 = float(t_peak_h1 + lag_v1)

    return {
        "t_peak_h1": t_peak_h1,
        "t_peak_l1": t_peak_l1,
        "t_peak_v1": t_peak_v1,
        "anchor_lag_h1_l1_s": float(lag_l1),
        "anchor_lag_s": float(lag_l1),
        "anchor_lag_h1_v1_s": float(lag_v1),
        "anchor_corr_h1_l1": float(corr_l1),
        "anchor_corr": float(corr_l1),
        "anchor_abs_corr_h1_l1": float(abs(corr_l1)),
        "anchor_corr_h1_v1": float(corr_v1),
        "anchor_abs_corr_h1_v1": float(abs(corr_v1)),
        "anchor_abs_corr": float(best_score),
        "anchor_edge_hit": False,
        "anchor_peak_candidates": int(len(candidates)),
    }



def find_h1_peak_time(h1: GWSeries, center_guess_gps: float,
                      anchor_band: Tuple[float, float],
                      peak_search_halfwin_s: float) -> Dict[str, float]:
    """Pick the absolute-peak time in H1 within the peak-search window, after anchor-band bandpass."""
    fs = h1.fs
    h1_bp = bandpass_filt(h1.strain, fs, anchor_band)
    t = h1.time_axis()
    wmask = (t >= center_guess_gps - peak_search_halfwin_s) & (t <= center_guess_gps + peak_search_halfwin_s)
    idxw = np.where(wmask)[0]
    if len(idxw) < int(0.2 * peak_search_halfwin_s * fs):
        raise RuntimeError("Anchor peak search window out of range.")
    abs_h1 = np.abs(h1_bp[idxw])
    i_peak = int(idxw[int(np.argmax(abs_h1))])
    return {"t_peak_h1": float(t[i_peak]), "i_peak": float(i_peak)}

def anchor_corr_at_fixed_lag(h1: GWSeries, l1: GWSeries, v1: Optional[GWSeries],
                            center_guess_gps: float,
                            anchor_band: Tuple[float, float],
                            peak_search_halfwin_s: float,
                            lag_window_s: float,
                            lag_h1_l1_s: float,
                            lag_h1_v1_s: Optional[float] = None) -> Dict[str, Any]:
    """Compute anchor correlations at user-fixed lags, around H1 peak."""
    fs = h1.fs
    if abs(l1.fs - fs) > 1e-9 or (v1 is not None and abs(v1.fs - fs) > 1e-9):
        raise RuntimeError("Sampling rates must match for anchor correlation.")

    # bandpass for anchor correlation
    h1_bp = bandpass_filt(h1.strain, fs, anchor_band)
    l1_bp = bandpass_filt(l1.strain, fs, anchor_band)
    v1_bp = bandpass_filt(v1.strain, fs, anchor_band) if v1 is not None else None

    pk = find_h1_peak_time(h1, center_guess_gps, anchor_band, peak_search_halfwin_s)
    i_peak = int(pk["i_peak"])
    t_peak_h1 = float(pk["t_peak_h1"])
    t_peak_l1 = float(t_peak_h1 + lag_h1_l1_s)
    t_peak_v1 = float(t_peak_h1 + (lag_h1_v1_s if lag_h1_v1_s is not None else 0.0)) if v1 is not None else None

    half = int(round(0.5 * lag_window_s * fs))
    i1 = max(i_peak - half, 0)
    i2 = min(i_peak + half, len(h1_bp))

    def corr_for_lag(tgt_bp: np.ndarray, lag_s: float) -> float:
        k = int(round(lag_s * fs))
        if i1 + k < 0 or i2 + k > len(tgt_bp):
            return 0.0
        return float(norm_corr(h1_bp[i1:i2], tgt_bp[i1 + k:i2 + k]))

    corr_l1 = corr_for_lag(l1_bp, lag_h1_l1_s)
    corr_v1 = None
    if v1_bp is not None and lag_h1_v1_s is not None:
        corr_v1 = corr_for_lag(v1_bp, lag_h1_v1_s)

    out = {
        "t_peak_h1": t_peak_h1,
        "t_peak_l1": t_peak_l1,
        "anchor_lag_h1_l1_s": float(lag_h1_l1_s),
        "anchor_lag_s": float(lag_h1_l1_s),
        "anchor_corr_h1_l1": float(corr_l1),
        "anchor_corr": float(corr_l1),
        "anchor_abs_corr_h1_l1": float(abs(corr_l1)),
        "anchor_abs_corr": float(abs(corr_l1)),
        "anchor_edge_hit": False,
        "anchor_peak_candidates": 1,
        "anchor_fixed_lags": True,
    }
    if v1 is not None:
        out["t_peak_v1"] = float(t_peak_v1)
        out["anchor_lag_h1_v1_s"] = float(lag_h1_v1_s if lag_h1_v1_s is not None else 0.0)
        if corr_v1 is not None:
            out["anchor_corr_h1_v1"] = float(corr_v1)
            out["anchor_abs_corr_h1_v1"] = float(abs(corr_v1))
            out["anchor_abs_corr"] = float(min(abs(corr_l1), abs(corr_v1)))
    return out


def make_ringdown_segment(series: GWSeries, t_peak_gps: float,
                          start_s: float, dur_s: float,
                          band: Tuple[float, float],
                          psd_guard_s: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns whitened ringdown segment and PSD used:
      xw, raw_segment, psd_f, psd_pxx
    """
    fs = series.fs
    t = series.time_axis()
    t1 = t_peak_gps + start_s
    t2 = t1 + dur_s
    mask = (t >= t1) & (t < t2)
    idx = np.where(mask)[0]
    if len(idx) < int(0.5 * dur_s * fs):
        raise RuntimeError("Ringdown segment too small / outside data range.")
    x_raw = series.strain[idx]
    x_bp = bandpass_filt(x_raw, fs, band)

    # PSD estimation from the *full* record, excluding a guard around [t1,t2]
    guard1 = t1 - psd_guard_s
    guard2 = t2 + psd_guard_s
    mask_psd = (t < guard1) | (t > guard2)
    x_psd = series.strain[mask_psd]
    # bandpass PSD data too (stabilizes)
    x_psd_bp = bandpass_filt(x_psd, fs, band)
    psd_f, psd_pxx = welch_psd(x_psd_bp, fs, nperseg=4096, noverlap=2048)

    xw = whiten_fft(x_bp, fs, psd_f, psd_pxx)
    return xw, x_bp, psd_f, psd_pxx

def best_template_match(xw: np.ndarray, fs: float,
                        t_model: np.ndarray, y_model: np.ndarray,
                        time_scales: List[float],
                        max_model_lag_s: float,
                        allow_sign_flip: bool = True) -> Dict[str, Any]:
    """Find best (time_scale, lag, sign, amplitude) match by maximizing |corr|."""
    n = len(xw)
    seg_len_s = n / fs
    max_lag_samp = int(round(max_model_lag_s * fs))
    lags = np.arange(-max_lag_samp, max_lag_samp + 1, dtype=int)

    best = {
        "abs_corr": -1.0,
        "corr": 0.0,
        "time_scale": None,
        "lag_s": 0.0,
        "sign": +1,
    }
    for s in time_scales:
        # precompute model at zero lag, then shift
        m0 = sample_model_segment(t_model, y_model, fs, seg_len_s, time_scale=s, lag_s=0.0)
        for k in lags:
            m = shift_samples(m0, k)
            c = norm_corr(xw, m)
            if allow_sign_flip:
                c2 = norm_corr(xw, -m)
                if abs(c2) > abs(c):
                    c = c2
                    sign = -1
                else:
                    sign = +1
            else:
                sign = +1
            if abs(c) > best["abs_corr"]:
                best.update({
                    "abs_corr": float(abs(c)),
                    "corr": float(c),
                    "time_scale": float(s),
                    "lag_s": float(k / fs),
                    "sign": int(sign),
                })
    return best

def coherent_average(h1w: np.ndarray, l1w: np.ndarray, fs: float, anchor_lag_s: float) -> Tuple[np.ndarray, float]:
    """
    Align-and-average H1 and L1 using the anchor lag.

    IMPORTANT (stability/physics):
      We return the **overlap-only** average to avoid zero-padding artifacts.
      This prevents the coherent average from being diluted by padding zeros near the edges
      when a non-zero lag is applied.

    Convention:
      - anchor_lag_s > 0 means L1 arrives later than H1.
      - To align L1 to H1, we must ADVANCE L1 by anchor_lag_s, i.e. shift left by +lag,
        which corresponds to k = -round(lag_s * fs) in shift_samples (k>0 => delay).
    """
    k = int(round(-anchor_lag_s * fs))
    if k == 0:
        return 0.5 * (h1w + l1w), 0.0

    n = len(h1w)
    if abs(k) >= n:
        # no overlap
        return np.zeros(0, dtype=h1w.dtype), k / fs

    if k > 0:
        # L1 delayed by k: overlap is h1[k:] with l1[:-k]
        avg = 0.5 * (h1w[k:] + l1w[:n-k])
    else:
        kk = -k
        # L1 advanced by kk: overlap is h1[:-kk] with l1[kk:]
        avg = 0.5 * (h1w[:n-kk] + l1w[kk:])
    return avg, k / fs


# -------------------------
# Main pipeline
# -------------------------

def run_once(h1: GWSeries, l1: GWSeries,
             center_guess_gps: float,
             anchor_band: Tuple[float, float],
             analysis_band: Tuple[float, float],
             peak_search_halfwin_s: float,
             lag_search_s: float,
             lag_window_s: float,
             ringdown_start_s: float,
             ringdown_dur_s: float,
             psd_guard_s: float,
             model_t: np.ndarray, model_y_by: Dict[str, np.ndarray],
             time_scales: List[float],
             max_model_lag_s: float,
             allow_sign_flip: bool = True,
             fixed_anchor_lag_s: Optional[float] = None,
             fixed_anchor_lag_h1_v1_s: Optional[float] = None,
             v1: Optional[GWSeries] = None) -> Dict[str, Any]:

    # --- Anchor selection ---
    # If V1 exists, prefer a 3-detector coherence-driven anchor (min of |corr(H1,L1)| and |corr(H1,V1)|).
    # If user provides fixed lags, use them to avoid noise-driven anchor "edge hits".
    if v1 is not None and (fixed_anchor_lag_s is None) and (fixed_anchor_lag_h1_v1_s is None):
        anc = find_anchor_peak_and_lag_3(
            h1, l1, v1,
            center_guess_gps=center_guess_gps,
            anchor_band=anchor_band,
            peak_search_halfwin_s=peak_search_halfwin_s,
            lag_search_s=lag_search_s,
            lag_window_s=lag_window_s
        )
    elif (fixed_anchor_lag_s is not None) or (v1 is not None and fixed_anchor_lag_h1_v1_s is not None):
        if fixed_anchor_lag_s is None:
            raise ValueError("When fixing V1 lag, also provide --fixed_anchor_lag_s (H1->L1).")
        anc = anchor_corr_at_fixed_lag(
            h1, l1, v1,
            center_guess_gps=center_guess_gps,
            anchor_band=anchor_band,
            peak_search_halfwin_s=peak_search_halfwin_s,
            lag_window_s=lag_window_s,
            lag_h1_l1_s=float(fixed_anchor_lag_s),
            lag_h1_v1_s=(float(fixed_anchor_lag_h1_v1_s) if fixed_anchor_lag_h1_v1_s is not None else None)
        )
    else:
        anc = find_anchor_peak_and_lag(
            h1, l1,
            center_guess_gps=center_guess_gps,
            anchor_band=anchor_band,
            peak_search_halfwin_s=peak_search_halfwin_s,
            lag_search_s=lag_search_s,
            lag_window_s=lag_window_s
        )


    h1w, h1bp, psd_f_h1, psd_pxx_h1 = make_ringdown_segment(
        h1, anc["t_peak_h1"], start_s=ringdown_start_s, dur_s=ringdown_dur_s,
        band=analysis_band, psd_guard_s=psd_guard_s
    )

    # L1 ringdown segment should start relative to L1's own peak time.
    # This avoids including pre-peak content in L1 when ringdown_start_s=0.
    t_peak_l1_for_seg = anc["t_peak_l1"]
    if fixed_anchor_lag_s is not None:
        # If user pins the H1-L1 lag, pin the implied L1 peak time too.
        t_peak_l1_for_seg = anc["t_peak_h1"] + float(fixed_anchor_lag_s)

    l1w, l1bp, psd_f_l1, psd_pxx_l1 = make_ringdown_segment(
        l1, t_peak_l1_for_seg, start_s=ringdown_start_s, dur_s=ringdown_dur_s,
        band=analysis_band, psd_guard_s=psd_guard_s
    )

    # Optional V1 ringdown segment (3-detector)
    v1w = None
    if v1 is not None:
        t_peak_v1_for_seg = float(anc.get("t_peak_v1", anc["t_peak_h1"]))
        v1w, v1bp, psd_f_v1, psd_pxx_v1 = make_ringdown_segment(
            v1, t_peak_v1_for_seg, start_s=ringdown_start_s, dur_s=ringdown_dur_s,
            band=analysis_band, psd_guard_s=psd_guard_s
        )

    lag_for_avg = 0.0  # segments are already peak-aligned (each detector's own peak)

    if v1w is None:
        avgw, applied_lag = coherent_average(h1w, l1w, h1.fs, lag_for_avg)
    else:
        n = min(len(h1w), len(l1w), len(v1w))
        avgw = (h1w[:n] + l1w[:n] + v1w[:n]) / 3.0
        applied_lag = 0.0

    best_h1 = best_template_match(h1w, h1.fs, model_t, model_y_by['H1'], time_scales, max_model_lag_s, allow_sign_flip=allow_sign_flip)
    best_l1 = best_template_match(l1w, l1.fs, model_t, model_y_by['L1'], time_scales, max_model_lag_s, allow_sign_flip=allow_sign_flip)
    best_v1 = None
    if v1w is not None:
        best_v1 = best_template_match(v1w, v1.fs, model_t, model_y_by['V1'], time_scales, max_model_lag_s, allow_sign_flip=allow_sign_flip)
    best_avg = best_template_match(avgw, h1.fs, model_t, model_y_by['AVG'], time_scales, max_model_lag_s, allow_sign_flip=allow_sign_flip)

    # --- H1/L1 consistency diagnostic (evaluate both detectors at the *AVG* best-fit params) ---
    seg_len_s = len(h1w) / h1.fs
    mseg = sample_model_segment(model_t, model_y_by['AVG'], h1.fs, seg_len_s,
                               time_scale=best_avg["time_scale"], lag_s=best_avg["lag_s"])
    if best_avg.get("sign", 1) == -1:
        mseg = -mseg
    c_h1_at_avg = norm_corr(h1w, mseg)
    c_l1_at_avg = norm_corr(l1w, mseg)
    c_v1_at_avg = None
    if v1w is not None:
        c_v1_at_avg = norm_corr(v1w[:len(mseg)], mseg)

    if c_v1_at_avg is None:
        at_avg = {
            "h1": {"corr": float(c_h1_at_avg), "abs_corr": float(abs(c_h1_at_avg))},
            "l1": {"corr": float(c_l1_at_avg), "abs_corr": float(abs(c_l1_at_avg))},
            "min_abs_corr": float(min(abs(c_h1_at_avg), abs(c_l1_at_avg))),
            "sign_agree": bool(c_h1_at_avg * c_l1_at_avg > 0.0),
        }
    else:
        at_avg = {
            "h1": {"corr": float(c_h1_at_avg), "abs_corr": float(abs(c_h1_at_avg))},
            "l1": {"corr": float(c_l1_at_avg), "abs_corr": float(abs(c_l1_at_avg))},
            "v1": {"corr": float(c_v1_at_avg), "abs_corr": float(abs(c_v1_at_avg))},
            "min_abs_corr": float(min(abs(c_h1_at_avg), abs(c_l1_at_avg), abs(c_v1_at_avg))),
            "sign_agree": bool((c_h1_at_avg * c_l1_at_avg > 0.0) and (c_h1_at_avg * c_v1_at_avg > 0.0) and (c_l1_at_avg * c_v1_at_avg > 0.0)),
        }

    return {
        "anchor": {**anc, "applied_lag_s": applied_lag, "avg_lag_s_requested": float(lag_for_avg), "avg_lag_fixed": bool(fixed_anchor_lag_s is not None)},
        "best_h1": best_h1,
        "best_l1": best_l1,
        "best_v1": best_v1,
        "best_avg": best_avg,
        "at_avg": at_avg,
        "ringdown": {
            "start_s": float(ringdown_start_s),
            "dur_s": float(ringdown_dur_s),
            "analysis_band": list(map(float, analysis_band)),
            "anchor_band": list(map(float, anchor_band)),
        }
    }, h1w, l1w, avgw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h1_hdf5", required=True)
    ap.add_argument("--l1_hdf5", required=True)
    ap.add_argument("--v1_hdf5", default=None, help="Optional Virgo V1 HDF5 (GWOSC) for 3-detector analysis")
    ap.add_argument("--model_csv", required=True)
    ap.add_argument("--model_col", default=None, help="Single model column (legacy). If using plus/cross projection, set --model_col_plus/--model_col_cross instead.")
    ap.add_argument("--model_col_plus", default=None, help="Model plus polarization column (e.g., h_plus_proxy)")
    ap.add_argument("--model_col_cross", default=None, help="Model cross polarization column (e.g., h_cross_proxy)")
    ap.add_argument("--Fplus_H1", type=float, default=1.0)
    ap.add_argument("--Fcross_H1", type=float, default=0.0)
    ap.add_argument("--Fplus_L1", type=float, default=1.0)
    ap.add_argument("--Fcross_L1", type=float, default=0.0)
    ap.add_argument("--Fplus_V1", type=float, default=1.0)
    ap.add_argument("--Fcross_V1", type=float, default=0.0)

    ap.add_argument("--auto_event", default="", choices=["", "gw170814"],
                help="If set, fill RA/Dec from a published sky-location guess for that event (coarse).")
    ap.add_argument("--auto_antenna", action="store_true",
                help="Compute (F+,Fx) from RA/Dec/psi and center_guess_gps; overrides --Fplus_* / --Fcross_*.")
    ap.add_argument("--ra_deg", type=float, default=None, help="Right ascension in degrees (required for --auto_antenna).")
    ap.add_argument("--dec_deg", type=float, default=None, help="Declination in degrees (required for --auto_antenna).")
    ap.add_argument("--psi_deg", type=float, default=0.0, help="Polarization angle in degrees (default 0).")


    ap.add_argument("--t_col", default="t_s")

    ap.add_argument("--center_guess_gps", type=float, default=1126259462.0)

    ap.add_argument("--anchor_band", default="35,350")
    ap.add_argument("--analysis_band", default="80,300")
    ap.add_argument("--peak_search_halfwin_s", type=float, default=0.15)
    ap.add_argument("--lag_search_s", type=float, default=0.012)
    ap.add_argument("--lag_window_s", type=float, default=0.06)
    ap.add_argument("--fixed_anchor_lag_s", type=float, default=None,
                    help="If set, use this fixed H1->L1 lag (seconds) for coherent averaging instead of data-estimated anchor lag. Positive means L1 arrives later than H1.")
    ap.add_argument("--fixed_anchor_lag_h1_v1_s", type=float, default=None,
                    help="If set (3-detector), use this fixed H1->V1 lag (seconds). Positive means V1 arrives later than H1. If provided, you should also set --fixed_anchor_lag_s for H1->L1.")


    ap.add_argument("--ringdown_start_s", type=float, default=0.0,
                    help="Start offset from anchor peak time. Use 0.0 for 'from peak', or +0.005 to skip chirp tail.")
    ap.add_argument("--ringdown_dur_s", type=float, default=0.08,
                    help="Ringdown segment duration in seconds.")
    ap.add_argument("--psd_guard_s", type=float, default=0.8)

    ap.add_argument("--time_scales", default="0.75,1,1.25,1.5,2")
    ap.add_argument("--max_model_lag_s", type=float, default=0.03)

    ap.add_argument("--offsource_n", type=int, default=300)
    ap.add_argument("--offsource_guard_s", type=float, default=0.8)
    ap.add_argument("--seed", type=int, default=123)

    ap.add_argument("--out_prefix", required=True)
    ap.add_argument("--plot_png", nargs="?", const="__AUTO__", default=None,
                    help="Optional plot output prefix. If provided without a value, uses --out_prefix.")
    ap.add_argument("--no_sign_flip", action="store_true", help="Disable template sign flip (reduces trials)")
    ap.add_argument("--model_t0peak_col", default=None, help="If set, shift model time so peak(|this column|) is at t=0 before sampling (peak picked on abs value).")
    args = ap.parse_args()
    # Auto-fill RA/Dec from event name (coarse sky-location guess)
    if args.auto_event:
        ev = EVENT_RADECS_DEG.get(args.auto_event.lower())
        if ev is None:
            raise ValueError(f"Unknown --auto_event={args.auto_event}")
        if args.ra_deg is None:
            args.ra_deg = float(ev["ra_deg"])
        if args.dec_deg is None:
            args.dec_deg = float(ev["dec_deg"])

    # Auto-compute antenna patterns (F+, Fx) from RA/Dec/psi and center_guess_gps
    if args.auto_antenna or args.auto_event:
        if args.ra_deg is None or args.dec_deg is None:
            raise ValueError("Need --ra_deg and --dec_deg (or --auto_event) to compute antenna patterns.")
        F = antenna_patterns_from_radec(args.center_guess_gps, args.ra_deg, args.dec_deg, args.psi_deg)
        args.Fplus_H1, args.Fcross_H1 = F["H1"]
        args.Fplus_L1, args.Fcross_L1 = F["L1"]
        args.Fplus_V1, args.Fcross_V1 = F["V1"]
        print("[AUTO] Antenna patterns (ECEF, coarse):")
        print(f"  H1: F+={args.Fplus_H1:.6f}  Fx={args.Fcross_H1:.6f}")
        print(f"  L1: F+={args.Fplus_L1:.6f}  Fx={args.Fcross_L1:.6f}")
        print(f"  V1: F+={args.Fplus_V1:.6f}  Fx={args.Fcross_V1:.6f}")

    if args.plot_png == "__AUTO__":
        args.plot_png = args.out_prefix


    anchor_band = parse_band(args.anchor_band)
    analysis_band = parse_band(args.analysis_band)
    time_scales = parse_floats_csv(args.time_scales)

    h1 = load_gwosc_hdf5(args.h1_hdf5, "H1")
    l1 = load_gwosc_hdf5(args.l1_hdf5, "L1")
    v1 = load_gwosc_hdf5(args.v1_hdf5, "V1") if args.v1_hdf5 else None

    # --------------------------
    # Load model (single-col OR plus/cross projection)
    # --------------------------
    use_proj = (args.model_col_plus is not None) or (args.model_col_cross is not None)

    model_t0peak_s = 0.0

    if use_proj:
        if (args.model_col_plus is None) or (args.model_col_cross is None):
            raise ValueError("If using projection, set BOTH --model_col_plus and --model_col_cross.")
        model_t, y_plus, y_cross = read_model_csv_raw2(args.model_csv, args.t_col, args.model_col_plus, args.model_col_cross)

        # Optional: shift model time so peak(|model_t0peak_col|) is at t=0 (use RAW column for peak-pick)
        if args.model_t0peak_col:
            df_pk = pd.read_csv(args.model_csv)
            if args.t_col not in df_pk.columns:
                raise ValueError(f"Model CSV missing t_col={args.t_col} for model_t0peak_col pick")
            if args.model_t0peak_col not in df_pk.columns:
                raise ValueError(f"Model CSV missing model_t0peak_col={args.model_t0peak_col}")
            t_pk = df_pk[args.t_col].to_numpy(dtype=float)
            y_pk = df_pk[args.model_t0peak_col].to_numpy(dtype=float)
            idx = np.argsort(t_pk)
            t_pk = t_pk[idx]
            y_pk = y_pk[idx]
            y_pk = y_pk - np.mean(y_pk)
            if len(t_pk) == 0:
                raise ValueError("model_t0peak_col produced empty series")
            i_pk = int(np.argmax(np.abs(y_pk)))
            model_t0peak_s = float(t_pk[i_pk])
            model_t = model_t - model_t0peak_s

        # Project template for each detector: h_det = F+ * h+ + Fx * h×
        raw_h1 = args.Fplus_H1 * y_plus + args.Fcross_H1 * y_cross
        raw_l1 = args.Fplus_L1 * y_plus + args.Fcross_L1 * y_cross
        model_y_by = {
            "H1": standardize_series(raw_h1),
            "L1": standardize_series(raw_l1),
        }
        raws = [raw_h1, raw_l1]

        if v1 is not None:
            raw_v1 = args.Fplus_V1 * y_plus + args.Fcross_V1 * y_cross
            model_y_by["V1"] = standardize_series(raw_v1)
            raws.append(raw_v1)

        raw_avg = np.mean(np.vstack(raws), axis=0)
        model_y_by["AVG"] = standardize_series(raw_avg)

        model_meta = {
            "mode": "plus_cross_projection",
            "model_col_plus": args.model_col_plus,
            "model_col_cross": args.model_col_cross,
            "F": {
                "H1": [args.Fplus_H1, args.Fcross_H1],
                "L1": [args.Fplus_L1, args.Fcross_L1],
                "V1": [args.Fplus_V1, args.Fcross_V1] if v1 is not None else None,
            },
        }
    else:
        if not args.model_col:
            raise ValueError("Provide --model_col (legacy) OR (--model_col_plus AND --model_col_cross).")
        model_t, model_y = read_model_csv(args.model_csv, args.t_col, args.model_col)

        # Optional: shift model time so peak(|model_t0peak_col|) is at t=0 before sampling
        if args.model_t0peak_col:
            t_p, y_p = read_model_csv(args.model_csv, args.t_col, args.model_t0peak_col)
            if len(t_p) == 0:
                raise ValueError("model_t0peak_col produced empty series")
            i_pk = int(np.argmax(np.abs(y_p)))
            model_t0peak_s = float(t_p[i_pk])
            model_t = model_t - model_t0peak_s

        model_y_by = {"H1": model_y, "L1": model_y, "AVG": model_y}
        if v1 is not None:
            model_y_by["V1"] = model_y

        model_meta = {"mode": "single_col", "model_col": args.model_col}



    # Event
    event_summary, ev_h1w, ev_l1w, ev_avgw = run_once(
        h1, l1,
        center_guess_gps=args.center_guess_gps,
        anchor_band=anchor_band,
        analysis_band=analysis_band,
        peak_search_halfwin_s=args.peak_search_halfwin_s,
        lag_search_s=args.lag_search_s,
        lag_window_s=args.lag_window_s,
        ringdown_start_s=args.ringdown_start_s,
        ringdown_dur_s=args.ringdown_dur_s,
        psd_guard_s=args.psd_guard_s,
        model_t=model_t,
        model_y_by=model_y_by,
        time_scales=time_scales,
        max_model_lag_s=args.max_model_lag_s,
        allow_sign_flip=(not args.no_sign_flip),
        fixed_anchor_lag_s=args.fixed_anchor_lag_s,
        fixed_anchor_lag_h1_v1_s=args.fixed_anchor_lag_h1_v1_s,
        v1=v1
    )

    event_abs_corr = float(event_summary["best_avg"]["abs_corr"])

    event_min_abs_corr = float(event_summary["at_avg"]["min_abs_corr"])

    # Off-source null
    rng = np.random.default_rng(args.seed)
    t_full = h1.time_axis()
    t_min = t_full[0] + 1.0
    t_max = t_full[-1] - 1.0

    # guard away from the *event* center guess (not the found peak)
    guard_lo = args.center_guess_gps - args.offsource_guard_s
    guard_hi = args.center_guess_gps + args.offsource_guard_s

    null_rows = []
    tries = 0
    while len(null_rows) < args.offsource_n and tries < args.offsource_n * 50:
        tries += 1
        c = float(rng.uniform(t_min, t_max))
        if guard_lo <= c <= guard_hi:
            continue
        try:
            summ, _, _, _ = run_once(
                h1, l1,
                center_guess_gps=c,
                anchor_band=anchor_band,
                analysis_band=analysis_band,
                peak_search_halfwin_s=args.peak_search_halfwin_s,
                lag_search_s=args.lag_search_s,
                lag_window_s=args.lag_window_s,
                ringdown_start_s=args.ringdown_start_s,
                ringdown_dur_s=args.ringdown_dur_s,
                psd_guard_s=args.psd_guard_s,
                model_t=model_t,
                model_y_by=model_y_by,
                time_scales=time_scales,
                max_model_lag_s=args.max_model_lag_s,
        allow_sign_flip=(not args.no_sign_flip),
                fixed_anchor_lag_s=args.fixed_anchor_lag_s,
        fixed_anchor_lag_h1_v1_s=args.fixed_anchor_lag_h1_v1_s,
                v1=v1
            )
            null_rows.append({
                "center_gps": c,
                "anchor_lag_s": summ["anchor"]["anchor_lag_s"],
                "anchor_corr": summ["anchor"]["anchor_corr"],
                "avg_lag_s_requested": summ["anchor"].get("avg_lag_s_requested", summ["anchor"]["anchor_lag_s"]),
                "avg_lag_fixed": summ["anchor"].get("avg_lag_fixed", False),
                "abs_corr_avg": summ["best_avg"]["abs_corr"],
                "corr_avg": summ["best_avg"]["corr"],
                "time_scale": summ["best_avg"]["time_scale"],
                "model_lag_s": summ["best_avg"]["lag_s"],

                # Per-detector corr evaluated at AVG best-fit params:
                "abs_corr_h1": summ["at_avg"]["h1"]["abs_corr"],
                "corr_h1": summ["at_avg"]["h1"]["corr"],
                "abs_corr_l1": summ["at_avg"]["l1"]["abs_corr"],
                "corr_l1": summ["at_avg"]["l1"]["corr"],

                # Consistency metric:
                "min_abs_corr": summ["at_avg"]["min_abs_corr"],
                "sign_agree": int(summ["at_avg"]["sign_agree"]),
            })
        except Exception:
            # skip failures
            continue

    null_df = pd.DataFrame(null_rows)
    # p-value for abs corr
    if len(null_df) > 0:
        p_abs = float(np.mean(null_df["abs_corr_avg"].to_numpy() >= event_abs_corr))
        p_min_abs = float(np.mean(null_df["min_abs_corr"].to_numpy() >= event_min_abs_corr))
        p_joint = float(np.mean((null_df["abs_corr_avg"].to_numpy() >= event_abs_corr) & (null_df["min_abs_corr"].to_numpy() >= event_min_abs_corr)))
        null_stats = {
            "n": int(len(null_df)),
            "mean": float(np.mean(null_df["abs_corr_avg"])),
            "p95": float(np.quantile(null_df["abs_corr_avg"], 0.95)),
            "p_abs_corr": p_abs,
            "p_min_abs_corr": p_min_abs,
            "p_joint_abs_and_minabs": p_joint,
            "abs_corr_p05": float(np.quantile(null_df["abs_corr_avg"], 0.05)),
            "abs_corr_p50": float(np.quantile(null_df["abs_corr_avg"], 0.50)),
            "min_abs_mean": float(np.mean(null_df["min_abs_corr"])),
            "min_abs_p95": float(np.quantile(null_df["min_abs_corr"], 0.95)),
            "min_abs_p50": float(np.quantile(null_df["min_abs_corr"], 0.50)),
        }
    else:
        p_abs = float("nan")
        null_stats = {"n": 0, "p_abs_corr": p_abs}

    out = {
        "event": event_summary,
        "event_abs_corr_avg": event_abs_corr,
        "event_min_abs_corr": event_min_abs_corr,
        "null": null_stats,
        "args": vars(args),
        "model_t0peak_s": model_t0peak_s,
        "model_projection": model_meta,
    }

    os.makedirs(os.path.dirname(args.out_prefix) or ".", exist_ok=True)
    summary_path = args.out_prefix + ".summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print(f"[WROTE] {summary_path}")

    off_path = args.out_prefix + ".offsource.csv"
    null_df.to_csv(off_path, index=False)
    print(f"[WROTE] {off_path}")

    # Plots
    if args.plot_png:
        # Overlay plot for event (avg)
        fs = h1.fs
        n = len(ev_avgw)
        tt = np.arange(n) / fs

        # best model for AVG
        b = event_summary["best_avg"]
        m = sample_model_segment(model_t, model_y_by['AVG'], fs, seg_len_s=n/fs,
                                 time_scale=b["time_scale"], lag_s=b["lag_s"])
        if b["sign"] == -1:
            m = -m

        # scale model to data in least-squares
        scale = float(np.dot(ev_avgw, m) / (np.dot(m, m) + 1e-12))
        m_fit = scale * m

        def plot_one(sig, name):
            # Robust against ±1 sample length mismatches introduced by rounding
            n = min(len(sig), len(m_fit))
            tt_local = np.arange(n) / fs
            plt.figure(figsize=(10,4))
            plt.plot(tt_local, sig[:n], label="data (whitened)")
            plt.plot(tt_local, m_fit[:n], label="model (scaled)")
            plt.xlabel("t [s]")
            plt.ylabel("whitened strain (arb.)")
            plt.title(f"ringdown-only match ({name})")
            plt.legend()
            plt.tight_layout()
            path = args.out_prefix + f"_event_overlay_{name}.png"
            plt.savefig(path, dpi=150)
            plt.close()
            print(f"[PLOT] {path}")

        plot_one(ev_h1w, "H1")
        plot_one(ev_l1w, "L1")
        plot_one(ev_avgw, "AVG")

        if len(null_df) > 0:
            plt.figure(figsize=(7,4))
            plt.hist(null_df["abs_corr_avg"].to_numpy(), bins=30)
            plt.axvline(event_abs_corr, linestyle="--", linewidth=2)
            plt.xlabel("|corr| (AVG)")
            plt.ylabel("count")
            plt.title("Off-source null distribution (ringdown-only)")
            plt.tight_layout()
            hpath = args.out_prefix + "_null_hist.png"
            plt.savefig(hpath, dpi=150)
            plt.close()
            print(f"[PLOT] {hpath}")

if __name__ == "__main__":
    main()