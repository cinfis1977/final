"""WEAK internal rate-kernel (minimal closure step).

Goal: move beyond pack-provided `N_sig_sm` and beyond signal reweighting.

This module computes reconstructed event rates from first principles *within the
repo*, given a minimal model:

  N_true(bin) = exposure * ∫_{E_lo}^{E_hi} flux(E) * sigma(E) * eff(E) * P(E) dE
  N_rec = smear_matrix @ N_true

Where:
- P(E) comes from internal dynamics (GKSL evolution).
- flux/sigma/eff are explicit parametric forms (not external curves).
- smear_matrix maps true-energy bins to reco bins.

This is still not experiment-grade (no near→far constraints, no full nuisance
covariance), but it is a concrete dynamical closure step.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Any, Callable, Protocol

import numpy as np


# ---------- Parametric models ----------


def _as_1d_float_array(x: Any, *, name: str) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be a 1D array")
    if arr.size < 1:
        raise ValueError(f"{name} must be non-empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def _tabular_linear_fn(model: dict[str, Any], *, kind_name: str) -> Callable[[np.ndarray], np.ndarray]:
    E = _as_1d_float_array(model.get("E"), name=f"{kind_name}.E")
    y = _as_1d_float_array(model.get("y"), name=f"{kind_name}.y")
    if E.size != y.size:
        raise ValueError(f"{kind_name}.E and {kind_name}.y must have the same length")
    if E.size < 2:
        raise ValueError(f"{kind_name}.E must have at least 2 points")
    if np.any(np.diff(E) <= 0):
        raise ValueError(f"{kind_name}.E must be strictly increasing")

    extrap = str(model.get("extrap", "zero")).lower()
    if extrap not in {"zero", "hold"}:
        raise ValueError(f"{kind_name}.extrap must be 'zero' or 'hold'")

    left = 0.0 if extrap == "zero" else float(y[0])
    right = 0.0 if extrap == "zero" else float(y[-1])

    def f(Ein: np.ndarray) -> np.ndarray:
        Ein = np.asarray(Ein, dtype=float)
        return np.interp(Ein, E, y, left=left, right=right).astype(float)

    return f


def _tabular_hist_fn(model: dict[str, Any], *, kind_name: str) -> Callable[[np.ndarray], np.ndarray]:
    E_lo = _as_1d_float_array(model.get("E_lo"), name=f"{kind_name}.E_lo")
    E_hi = _as_1d_float_array(model.get("E_hi"), name=f"{kind_name}.E_hi")
    y = _as_1d_float_array(model.get("y"), name=f"{kind_name}.y")
    if E_lo.size != E_hi.size or E_lo.size != y.size:
        raise ValueError(f"{kind_name}.E_lo/E_hi/y must have the same length")
    if np.any(E_hi <= E_lo):
        raise ValueError(f"{kind_name} bins must satisfy E_hi > E_lo")

    order = np.argsort(E_lo)
    E_lo = E_lo[order]
    E_hi = E_hi[order]
    y = y[order]

    if np.any(np.diff(E_lo) < 0):
        raise ValueError(f"{kind_name}.E_lo must be nondecreasing")
    if np.any(E_lo[1:] < E_hi[:-1]):
        raise ValueError(f"{kind_name} bins must not overlap")

    n_bins = int(E_lo.size)

    def f(Ein: np.ndarray) -> np.ndarray:
        Ein = np.asarray(Ein, dtype=float)
        out = np.zeros_like(Ein, dtype=float)
        idx = np.searchsorted(E_hi, Ein, side="right")
        mask = (idx < n_bins)
        if np.any(mask):
            idx_m = idx[mask]
            Ein_m = Ein[mask]
            in_bin = Ein_m >= E_lo[idx_m]
            if np.any(in_bin):
                out_mask = np.zeros_like(Ein_m, dtype=bool)
                out_mask[in_bin] = True
                out_vals = np.zeros_like(Ein_m, dtype=float)
                out_vals[in_bin] = y[idx_m[in_bin]]
                out[mask] = out_vals
        return out

    return f


def _validate_tabular_y_nonnegative(model: dict[str, Any], *, kind_name: str) -> None:
    y = np.asarray(model.get("y"), dtype=float)
    if y.ndim != 1 or y.size < 1:
        raise ValueError(f"{kind_name}.y must be a non-empty 1D array")
    if not np.all(np.isfinite(y)):
        raise ValueError(f"{kind_name}.y contains non-finite values")
    if float(np.min(y)) < 0.0:
        raise ValueError(f"{kind_name}.y must be nonnegative (min={float(np.min(y))})")


def _tabular_support_intervals(model: dict[str, Any]) -> list[tuple[float, float]]:
    """Return a sorted list of support intervals where the model is defined (hist format only)."""
    E_lo = np.asarray(model.get("E_lo"), dtype=float)
    E_hi = np.asarray(model.get("E_hi"), dtype=float)
    if E_lo.ndim != 1 or E_hi.ndim != 1 or E_lo.size != E_hi.size or E_lo.size < 1:
        raise ValueError("tabular hist format requires E_lo/E_hi 1D arrays")
    order = np.argsort(E_lo)
    E_lo = E_lo[order]
    E_hi = E_hi[order]
    intervals: list[tuple[float, float]] = []
    for lo, hi in zip(E_lo.tolist(), E_hi.tolist()):
        lo_f = float(lo)
        hi_f = float(hi)
        if not math.isfinite(lo_f) or not math.isfinite(hi_f) or hi_f <= lo_f:
            raise ValueError("tabular hist bins must have finite E_lo<E_hi")
        intervals.append((lo_f, hi_f))
    # merge touching/overlapping intervals (overlaps are already rejected upstream, but keep robust)
    intervals.sort(key=lambda t: t[0])
    merged: list[tuple[float, float]] = []
    for lo, hi in intervals:
        if not merged:
            merged.append((lo, hi))
            continue
        lo0, hi0 = merged[-1]
        if lo <= hi0 + 1e-12:
            merged[-1] = (lo0, max(hi0, hi))
        else:
            merged.append((lo, hi))
    return merged


def _intervals_cover_range(intervals: list[tuple[float, float]], lo: float, hi: float) -> bool:
    if hi <= lo:
        return True
    if not intervals:
        return False
    x = float(lo)
    for a, b in intervals:
        if x < a - 1e-12:
            return False
        if x <= b + 1e-12:
            x = max(x, b)
            if x >= hi - 1e-12:
                return True
    return x >= hi - 1e-12


def _validate_tabular_coverage(
    *,
    model: dict[str, Any],
    true_E_lo: np.ndarray,
    true_E_hi: np.ndarray,
    coverage_mode: str,
    kind_name: str,
) -> None:
    """Validate that tabular inputs cover the true-energy bins.

    coverage_mode:
      - ignore: do nothing
      - warn: emit a warning if any true bin is not fully covered
      - strict: raise ValueError if any true bin is not fully covered

    For linear-tabular, we treat extrap='hold' as covering everything; extrap='zero' requires
    the true range to lie within [E0, E_end].
    For histogram-tabular, we require the union of provided bins to cover each true bin.
    """

    mode = str(coverage_mode).lower()
    if mode == "ignore":
        return
    if mode not in {"warn", "strict"}:
        raise ValueError("tabular_coverage must be one of: ignore, warn, strict")

    lo_all = float(np.min(true_E_lo))
    hi_all = float(np.max(true_E_hi))

    ok = True
    if "E" in model:
        E = np.asarray(model.get("E"), dtype=float)
        if E.ndim != 1 or E.size < 2:
            raise ValueError(f"{kind_name}.E must be a 1D array with at least 2 points")
        extrap = str(model.get("extrap", "zero")).lower()
        if extrap not in {"zero", "hold"}:
            raise ValueError(f"{kind_name}.extrap must be 'zero' or 'hold'")
        if extrap == "zero":
            ok = (lo_all >= float(E[0]) - 1e-12) and (hi_all <= float(E[-1]) + 1e-12)
    else:
        intervals = _tabular_support_intervals(model)
        for lo, hi in zip(true_E_lo.tolist(), true_E_hi.tolist()):
            if not _intervals_cover_range(intervals, float(lo), float(hi)):
                ok = False
                break

    if ok:
        return

    msg = f"{kind_name} does not fully cover true-energy bins; outside-support values may be forced to 0"
    if mode == "strict":
        raise ValueError(msg)
    warnings.warn(msg, RuntimeWarning)

def _require_kind(m: dict[str, Any], expected: str) -> None:
    kind = m.get("kind")
    if kind != expected:
        raise ValueError(f"expected model kind='{expected}', got '{kind}'")


def flux_fn(model: dict[str, Any]) -> Callable[[np.ndarray], np.ndarray]:
    kind = str(model.get("kind", "const")).lower()

    if kind == "const":
        value = float(model.get("value", 1.0))

        def f(E):
            return np.full_like(E, value, dtype=float)

        return f

    if kind == "gaussian":
        amp = float(model.get("amp", 1.0))
        mu = float(model.get("mu", 1.0))
        sig = float(model.get("sigma", 0.3))
        sig = max(sig, 1e-12)

        def f(E):
            x = (E - mu) / sig
            return amp * np.exp(-0.5 * x * x)

        return f

    if kind in {"tabular", "hist"}:
        # Supports either:
        # - linear interpolation: {kind:tabular, E:[...], y:[...], extrap:zero|hold}
        # - histogram bins: {kind:tabular, E_lo:[...], E_hi:[...], y:[...]}
        if "E" in model:
            return _tabular_linear_fn(model, kind_name="flux_model")
        return _tabular_hist_fn(model, kind_name="flux_model")

    raise ValueError(f"Unknown flux model kind '{kind}'")


def sigma_fn(model: dict[str, Any]) -> Callable[[np.ndarray], np.ndarray]:
    kind = str(model.get("kind", "const")).lower()

    if kind == "const":
        value = float(model.get("value", 1.0))

        def f(E):
            return np.full_like(E, value, dtype=float)

        return f

    if kind == "powerlaw":
        a = float(model.get("a", 1.0))
        p = float(model.get("p", 1.0))
        E0 = float(model.get("E0", 1.0))
        E0 = max(E0, 1e-12)

        def f(E):
            return a * np.power(np.clip(E / E0, 0.0, None), p)

        return f

    if kind in {"tabular", "hist"}:
        if "E" in model:
            return _tabular_linear_fn(model, kind_name="sigma_model")
        return _tabular_hist_fn(model, kind_name="sigma_model")

    raise ValueError(f"Unknown sigma model kind '{kind}'")


def eff_fn(model: dict[str, Any] | None) -> Callable[[np.ndarray], np.ndarray]:
    if model is None:
        def f(E):
            return np.ones_like(E, dtype=float)

        return f

    kind = str(model.get("kind", "const")).lower()

    if kind == "const":
        value = float(model.get("value", 1.0))

        def f(E):
            return np.full_like(E, value, dtype=float)

        return f

    if kind == "step":
        Emin = float(model.get("Emin", 0.0))
        Emax = float(model.get("Emax", 1e9))
        value = float(model.get("value", 1.0))

        def f(E):
            out = np.zeros_like(E, dtype=float)
            mask = (E >= Emin) & (E <= Emax)
            out[mask] = value
            return out

        return f

    if kind in {"tabular", "hist"}:
        if "E" in model:
            return _tabular_linear_fn(model, kind_name="eff_model")
        return _tabular_hist_fn(model, kind_name="eff_model")

    raise ValueError(f"Unknown eff model kind '{kind}'")


# ---------- Integration + smearing ----------


class Smearing(Protocol):
    n_rec: int
    n_true: int

    def apply(self, N_true: np.ndarray) -> np.ndarray: ...


@dataclass(frozen=True)
class DenseSmearing:
    S: np.ndarray  # shape (n_rec, n_true)

    @property
    def n_rec(self) -> int:
        return int(self.S.shape[0])

    @property
    def n_true(self) -> int:
        return int(self.S.shape[1])

    def apply(self, N_true: np.ndarray) -> np.ndarray:
        return np.asarray(self.S @ N_true, dtype=float)


@dataclass(frozen=True)
class COOSmearing:
    n_rec: int
    n_true: int
    row_idx: np.ndarray
    col_idx: np.ndarray
    val: np.ndarray

    def apply(self, N_true: np.ndarray) -> np.ndarray:
        N_true = np.asarray(N_true, dtype=float)
        if N_true.shape != (int(self.n_true),):
            raise ValueError("N_true must be shape (n_true,)")
        weights = self.val * N_true[self.col_idx]
        out = np.bincount(self.row_idx, weights=weights, minlength=int(self.n_rec)).astype(float)
        return out


def _merge_duplicates_coo(row: np.ndarray, col: np.ndarray, val: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if row.size == 0:
        return row, col, val
    key = np.stack([col, row], axis=1)
    order = np.lexsort((key[:, 1], key[:, 0]))
    row_s = row[order]
    col_s = col[order]
    val_s = val[order]

    # group consecutive equal (col,row)
    same = (np.diff(col_s) == 0) & (np.diff(row_s) == 0)
    if not np.any(same):
        return row_s, col_s, val_s

    keep = np.ones_like(val_s, dtype=bool)
    keep[1:] = ~same
    row_u = row_s[keep]
    col_u = col_s[keep]
    val_u = np.zeros_like(row_u, dtype=float)

    # map each entry to its unique group index
    grp = np.cumsum(keep) - 1
    np.add.at(val_u, grp, val_s)
    return row_u, col_u, val_u


def _parse_smearing(channel_rk: dict[str, Any], *, reco_bin_count: int, n_true: int, tol: float = 1e-8) -> Smearing:
    smear_dense = channel_rk.get("smear_rec_by_true")
    smear_sparse = channel_rk.get("smear_sparse")
    if smear_dense is not None and smear_sparse is not None:
        raise ValueError("Provide only one of rate_kernel.smear_rec_by_true or rate_kernel.smear_sparse")

    if smear_sparse is not None:
        if not isinstance(smear_sparse, dict):
            raise ValueError("rate_kernel.smear_sparse must be a mapping")
        fmt = str(smear_sparse.get("format", "coo")).lower()
        if fmt != "coo":
            raise ValueError("rate_kernel.smear_sparse.format must be 'coo'")

        n_rec = int(smear_sparse.get("n_rec", reco_bin_count))
        n_true_s = int(smear_sparse.get("n_true", n_true))
        if n_rec != int(reco_bin_count) or n_true_s != int(n_true):
            raise ValueError(f"smear_sparse dimensions must match (n_rec={reco_bin_count}, n_true={n_true})")

        row = np.asarray(smear_sparse.get("row_idx", []), dtype=int)
        col = np.asarray(smear_sparse.get("col_idx", []), dtype=int)
        val = np.asarray(smear_sparse.get("val", []), dtype=float)
        if row.ndim != 1 or col.ndim != 1 or val.ndim != 1 or not (row.size == col.size == val.size):
            raise ValueError("smear_sparse row_idx/col_idx/val must be 1D arrays of equal length")
        if not np.all(np.isfinite(val)):
            raise ValueError("smear_sparse.val contains non-finite values")
        if val.size < 1:
            raise ValueError("smear_sparse must contain at least one nonzero entry")

        if np.min(row) < 0 or np.max(row) >= n_rec:
            raise ValueError("smear_sparse row_idx out of range")
        if np.min(col) < 0 or np.max(col) >= n_true_s:
            raise ValueError("smear_sparse col_idx out of range")
        if float(np.min(val)) < -float(tol):
            raise ValueError(f"smear_sparse has negative entries (min={float(np.min(val))})")

        row_u, col_u, val_u = _merge_duplicates_coo(row, col, val)

        # Column-stochastic check
        col_sums = np.bincount(col_u, weights=val_u, minlength=n_true_s).astype(float)
        max_dev = float(np.max(np.abs(col_sums - 1.0)))
        if max_dev > float(tol):
            raise ValueError(f"smearing matrix columns must sum to 1 (max_dev={max_dev})")

        return COOSmearing(n_rec=n_rec, n_true=n_true_s, row_idx=row_u.astype(int), col_idx=col_u.astype(int), val=val_u.astype(float))

    smear = np.asarray(smear_dense if smear_dense is not None else [], dtype=float)
    if smear.ndim != 2:
        raise ValueError("rate_kernel.smear_rec_by_true must be a 2D matrix")
    if smear.shape[0] != int(reco_bin_count) or smear.shape[1] != int(n_true):
        raise ValueError(f"smear matrix shape must be (n_rec={reco_bin_count}, n_true={n_true})")
    validate_physical_smearing(smear, tol=tol)
    return DenseSmearing(S=smear)


def integrate_bin_trapz(func: Callable[[np.ndarray], np.ndarray], E_lo: float, E_hi: float, *, n: int = 96) -> float:
    E_lo = float(E_lo)
    E_hi = float(E_hi)
    if not math.isfinite(E_lo) or not math.isfinite(E_hi) or E_hi <= E_lo:
        return 0.0
    n = int(n)
    n = 16 if n < 16 else n
    # NOTE: We intentionally avoid sampling exactly at bin edges.
    # Many tabular inputs are histogram-step functions; evaluating at
    # discontinuities (e.g. E == E_hi) combined with trapezoid endpoints can
    # introduce O(1/n) biases. Midpoint integration is exact for piecewise
    # constant hist models and remains stable for smooth models at large n.
    width = E_hi - E_lo
    step = width / float(n)
    grid = E_lo + (np.arange(n, dtype=float) + 0.5) * step
    vals = np.asarray(func(grid), dtype=float)
    return float(step * float(np.sum(vals)))


@dataclass(frozen=True)
class RateKernelConfig:
    exposure: float
    true_E_lo: np.ndarray
    true_E_hi: np.ndarray
    smear: Smearing
    flux_model: dict[str, Any]
    sigma_model: dict[str, Any]
    eff_model: dict[str, Any] | None
    n_steps: int = 96
    tabular_coverage: str = "ignore"


def parse_rate_kernel(channel: dict[str, Any], *, reco_bin_count: int) -> RateKernelConfig | None:
    rk = channel.get("rate_kernel")
    if rk is None:
        return None
    if not isinstance(rk, dict):
        raise ValueError("channel.rate_kernel must be a mapping")

    exposure = float(rk.get("exposure", 1.0))

    true_bins = rk.get("true_bins")
    if not isinstance(true_bins, dict):
        raise ValueError("rate_kernel.true_bins must be provided (E_lo/E_hi arrays)")

    true_E_lo = np.asarray(true_bins.get("E_lo", []), dtype=float)
    true_E_hi = np.asarray(true_bins.get("E_hi", []), dtype=float)
    if true_E_lo.ndim != 1 or true_E_hi.ndim != 1 or len(true_E_lo) != len(true_E_hi) or len(true_E_lo) < 1:
        raise ValueError("rate_kernel.true_bins E_lo/E_hi must be 1D arrays of equal length")

    smear = _parse_smearing(rk, reco_bin_count=int(reco_bin_count), n_true=int(len(true_E_lo)))

    flux_model = rk.get("flux_model")
    sigma_model = rk.get("sigma_model")
    if not isinstance(flux_model, dict) or not isinstance(sigma_model, dict):
        raise ValueError("rate_kernel.flux_model and sigma_model must be mappings")

    eff_model = rk.get("eff_model")
    if eff_model is not None and not isinstance(eff_model, dict):
        raise ValueError("rate_kernel.eff_model must be a mapping or null")

    tabular_coverage = str(rk.get("tabular_coverage", "ignore")).lower()
    if tabular_coverage not in {"ignore", "warn", "strict"}:
        raise ValueError("rate_kernel.tabular_coverage must be one of: ignore, warn, strict")

    # Validate tabular models (nonnegativity + optional coverage)
    for model, name in [(flux_model, "flux_model"), (sigma_model, "sigma_model")]:
        kind = str(model.get("kind", "const")).lower()
        if kind in {"tabular", "hist"}:
            _validate_tabular_y_nonnegative(model, kind_name=name)
            _validate_tabular_coverage(
                model=model,
                true_E_lo=true_E_lo,
                true_E_hi=true_E_hi,
                coverage_mode=tabular_coverage,
                kind_name=name,
            )

    if eff_model is not None:
        kind = str(eff_model.get("kind", "const")).lower()
        if kind in {"tabular", "hist"}:
            _validate_tabular_y_nonnegative(eff_model, kind_name="eff_model")
            _validate_tabular_coverage(
                model=eff_model,
                true_E_lo=true_E_lo,
                true_E_hi=true_E_hi,
                coverage_mode=tabular_coverage,
                kind_name="eff_model",
            )

    n_steps = int(rk.get("n_steps", 96))

    return RateKernelConfig(
        exposure=exposure,
        true_E_lo=true_E_lo,
        true_E_hi=true_E_hi,
        smear=smear,
        flux_model=flux_model,
        sigma_model=sigma_model,
        eff_model=eff_model,
        n_steps=n_steps,
        tabular_coverage=tabular_coverage,
    )


def validate_physical_smearing(smear_rec_by_true: np.ndarray, *, tol: float = 1e-8) -> None:
    """Validate a reconstructed-by-true migration matrix.

    Physical constraints (minimal):
    1) Non-negativity: S_ij >= 0
    2) Column-stochastic: for each true-bin j, sum_i S_ij = 1

    This matches the interpretation: each true event is reconstructed into exactly one reco bin
    with probabilities given by the column.
    """

    S = np.asarray(smear_rec_by_true, dtype=float)
    if S.ndim != 2:
        raise ValueError("smearing matrix must be 2D")
    if not np.all(np.isfinite(S)):
        raise ValueError("smearing matrix contains non-finite values")
    if np.min(S) < -float(tol):
        raise ValueError(f"smearing matrix has negative entries (min={float(np.min(S))})")

    col_sums = np.sum(S, axis=0)
    max_dev = float(np.max(np.abs(col_sums - 1.0))) if col_sums.size else 0.0
    if max_dev > float(tol):
        raise ValueError(f"smearing matrix columns must sum to 1 (max_dev={max_dev})")


def compute_event_rates_rec(
    *,
    config: RateKernelConfig,
    P_true: np.ndarray,
) -> np.ndarray:
    """Compute reconstructed rates per reco bin.

    Args:
        config: rate-kernel config
        P_true: oscillation probability evaluated at true-bin centers or approximated per true bin.

    Returns:
        N_rec: shape (n_rec,)
    """

    P_true = np.asarray(P_true, dtype=float)
    n_true = len(config.true_E_lo)
    if P_true.shape != (n_true,):
        raise ValueError("P_true must be shape (n_true,)")

    f_flux = flux_fn(config.flux_model)
    f_sig = sigma_fn(config.sigma_model)
    f_eff = eff_fn(config.eff_model)

    def integrand(E, p_scalar: float):
        return f_flux(E) * f_sig(E) * f_eff(E) * float(p_scalar)

    N_true = np.zeros(n_true, dtype=float)
    for j in range(n_true):
        p = float(P_true[j])
        N_true[j] = float(config.exposure) * integrate_bin_trapz(
            lambda E, p=p: integrand(E, p), float(config.true_E_lo[j]), float(config.true_E_hi[j]), n=config.n_steps
        )

    N_rec = config.smear.apply(N_true)
    return np.asarray(N_rec, dtype=float)


__all__ = [
    "RateKernelConfig",
    "validate_physical_smearing",
    "parse_rate_kernel",
    "compute_event_rates_rec",
    "flux_fn",
    "sigma_fn",
    "eff_fn",
    "DenseSmearing",
    "COOSmearing",
]
