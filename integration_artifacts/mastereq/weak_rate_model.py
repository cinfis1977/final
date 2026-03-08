"""Weak-sector rate model helpers.

This module is intentionally minimal: it provides a way to compute a per-bin
"no-oscillation" signal normalization from a factorized model

  N_noosc(bin) = norm * ∫_{E_lo}^{E_hi} flux(E) * sigma(E) * eff(E) dE

Then a WEAK runner can compute
  N_sig(bin) = N_noosc(bin) * P(E,L)

This is not a full experiment-grade pipeline (no near→far extrapolation, no
migration matrices, no separate interaction channels). It is the smallest step
beyond packs that directly provide `N_sig_sm`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Tabulated1D:
    E_GeV: np.ndarray
    y: np.ndarray

    @staticmethod
    def from_mapping(m: dict[str, Any], *, E_key: str = "E_GeV", y_key: str = "y") -> "Tabulated1D":
        E = np.asarray(m.get(E_key, []), dtype=float)
        y = np.asarray(m.get(y_key, []), dtype=float)
        if E.ndim != 1 or y.ndim != 1 or len(E) != len(y) or len(E) < 2:
            raise ValueError(f"Invalid tabulation for keys {E_key}/{y_key}")
        if not np.all(np.isfinite(E)) or not np.all(np.isfinite(y)):
            raise ValueError("Non-finite values in tabulation")
        if not np.all(np.diff(E) > 0):
            raise ValueError("E grid must be strictly increasing")
        return Tabulated1D(E_GeV=E, y=y)

    def eval(self, E_GeV: np.ndarray) -> np.ndarray:
        # Linear interpolation with endpoint clamping.
        return np.interp(E_GeV, self.E_GeV, self.y, left=self.y[0], right=self.y[-1])


def integrate_bin_trapz(func, E_lo: float, E_hi: float, *, n: int = 64) -> float:
    """Trapezoidal rule on a uniform grid within the bin."""
    E_lo = float(E_lo)
    E_hi = float(E_hi)
    if not math.isfinite(E_lo) or not math.isfinite(E_hi) or E_hi <= E_lo:
        return 0.0
    n = int(n)
    n = 8 if n < 8 else n
    E = np.linspace(E_lo, E_hi, n)
    y = func(E)
    return float(np.trapz(y, E))


def compute_N_noosc_bins(
    *,
    E_lo: np.ndarray,
    E_hi: np.ndarray,
    flux: Tabulated1D,
    sigma: Tabulated1D,
    eff: Tabulated1D | None,
    norm: float,
    n_steps: int = 64,
) -> np.ndarray:
    """Compute N_noosc per bin given a factorized rate model."""

    E_lo = np.asarray(E_lo, dtype=float)
    E_hi = np.asarray(E_hi, dtype=float)
    if E_lo.shape != E_hi.shape:
        raise ValueError("E_lo/E_hi shape mismatch")

    eff_tab = eff

    def integrand(E):
        val = flux.eval(E) * sigma.eval(E)
        if eff_tab is not None:
            val = val * eff_tab.eval(E)
        return val

    out = np.zeros_like(E_lo, dtype=float)
    for i in range(len(out)):
        out[i] = float(norm) * integrate_bin_trapz(integrand, float(E_lo[i]), float(E_hi[i]), n=int(n_steps))
    return out


def parse_rate_model(channel: dict[str, Any]) -> dict[str, Any] | None:
    """Return the rate model mapping if present; else None."""
    rm = channel.get("rate_model")
    if rm is None:
        return None
    if not isinstance(rm, dict):
        raise ValueError("channel.rate_model must be a mapping")
    return rm


def compute_sig_sm_from_pack_rate_model(
    *,
    channel: dict[str, Any],
    E_lo: np.ndarray,
    E_hi: np.ndarray,
) -> np.ndarray:
    """Compute a pack-provided SM signal baseline from an optional rate model.

    Supports two minimal modes:
    1) Provide `bins.N_noosc` directly → return it (interpreted as signal norm).
    2) Provide `channel.rate_model` with tabulated flux/sigma/(eff) and `norm`.

    Returns:
        sig_sm (array)

    Raises:
        ValueError if neither `N_noosc` nor `rate_model` is present.
    """

    bins = channel.get("bins", {})
    if isinstance(bins, dict) and "N_noosc" in bins:
        N_noosc = np.asarray(bins["N_noosc"], dtype=float)
        if N_noosc.shape != np.asarray(E_lo).shape:
            raise ValueError("bins.N_noosc must match bin count")
        return N_noosc

    rm = parse_rate_model(channel)
    if rm is None:
        raise ValueError("No rate model found: provide bins.N_noosc or channel.rate_model")

    norm = float(rm.get("norm", 1.0))
    flux = Tabulated1D.from_mapping(rm.get("flux", {}), E_key="E_GeV", y_key="phi")
    sigma = Tabulated1D.from_mapping(rm.get("sigma", {}), E_key="E_GeV", y_key="sigma")

    eff = None
    if "eff" in rm and rm["eff"] is not None:
        eff = Tabulated1D.from_mapping(rm.get("eff", {}), E_key="E_GeV", y_key="eff")

    n_steps = int(rm.get("n_steps", 64))

    return compute_N_noosc_bins(
        E_lo=np.asarray(E_lo, dtype=float),
        E_hi=np.asarray(E_hi, dtype=float),
        flux=flux,
        sigma=sigma,
        eff=eff,
        norm=norm,
        n_steps=n_steps,
    )
