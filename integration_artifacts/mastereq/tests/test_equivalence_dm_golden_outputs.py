import math
from pathlib import Path

import numpy as np
import pandas as pd

KPC_TO_M = 3.085677581491367e19


def _get_first_present(d: dict, names: tuple[str, ...]):
    for n in names:
        if n in d:
            return n
    return None


def _extract_r_m(points_df: pd.DataFrame) -> np.ndarray:
    if "r_m" in points_df.columns:
        return points_df["r_m"].astype(float).to_numpy()

    rcol = _get_first_present(points_df.iloc[0].to_dict(), ("r_kpc", "R_kpc", "R", "radius_kpc"))
    if rcol is None:
        raise RuntimeError(f"Could not find radius column. Columns={list(points_df.columns)}")

    r = points_df[rcol].astype(float).to_numpy()
    if np.nanmedian(r) < 1e6:
        r = r * KPC_TO_M
    return r


def _extract_g_bar(points_df: pd.DataFrame) -> np.ndarray:
    if "g_bar" in points_df.columns:
        return points_df["g_bar"].astype(float).to_numpy()

    vbar_col = _get_first_present(points_df.iloc[0].to_dict(), ("v_bar_kms", "Vbar", "vbar", "Vbar_kms"))
    if vbar_col is None:
        raise RuntimeError(f"Could not find g_bar or Vbar column. Columns={list(points_df.columns)}")

    r_m = _extract_r_m(points_df)
    v_mps = points_df[vbar_col].astype(float).to_numpy() * 1e3
    return (v_mps**2) / np.maximum(r_m, 1e-30)


def _extract_g_obs(points_df: pd.DataFrame) -> np.ndarray:
    if "g_obs" in points_df.columns:
        return points_df["g_obs"].astype(float).to_numpy()

    vobs_col = _get_first_present(points_df.iloc[0].to_dict(), ("v_obs_kms", "Vobs", "vobs", "Vobs_kms"))
    if vobs_col is None:
        raise RuntimeError(f"Could not find g_obs or Vobs column. Columns={list(points_df.columns)}")

    r_m = _extract_r_m(points_df)
    v_mps = points_df[vobs_col].astype(float).to_numpy() * 1e3
    return (v_mps**2) / np.maximum(r_m, 1e-30)


def _extract_sigma_log10g(points_df: pd.DataFrame):
    # Match dm_thread_env_dropin(_STIFFGATE): only accepts sigma_log10g
    if "sigma_log10g" in points_df.columns:
        s = points_df["sigma_log10g"].astype(float).to_numpy()
        return np.where(np.isfinite(s) & (s > 0), s, np.nan)

    ev_col = _get_first_present(points_df.iloc[0].to_dict(), ("ev_obs_kms", "eVobs", "evobs", "sigma_v_obs_kms"))
    vobs_col = _get_first_present(points_df.iloc[0].to_dict(), ("v_obs_kms", "Vobs", "vobs", "Vobs_kms"))
    if ev_col is None or vobs_col is None:
        return None

    ev = points_df[ev_col].astype(float).to_numpy() * 1e3
    v = points_df[vobs_col].astype(float).to_numpy() * 1e3
    frac = ev / np.maximum(v, 1e-30)
    sigma = (2.0 / np.log(10.0)) * frac
    sigma = np.where(np.isfinite(sigma) & (sigma > 0), sigma, np.nan)
    return sigma


def _chi2_log10g(g_pred: np.ndarray, g_obs: np.ndarray, sigma_log10g) -> float:
    g_pred = np.maximum(np.asarray(g_pred, dtype=float), 1e-30)
    g_obs = np.maximum(np.asarray(g_obs, dtype=float), 1e-30)
    r = np.log10(g_pred) - np.log10(g_obs)
    if sigma_log10g is None:
        return float(np.sum(r * r))

    sigma = np.asarray(sigma_log10g, dtype=float)
    w = np.where(np.isfinite(sigma) & (sigma > 0), 1.0 / (sigma * sigma), 0.0)
    return float(np.sum(w * (r * r)))


def _geo_add_const(g_bar: np.ndarray, *, A: float, alpha: float, g0: float, env_vec: np.ndarray) -> np.ndarray:
    Aeff = float(A) * np.asarray(env_vec, dtype=float)
    g0f = float(g0)
    gb = np.asarray(g_bar, dtype=float)
    g_geo = Aeff * g0f * np.power(g0f / (gb + g0f), float(alpha))
    return gb + g_geo


def _make_galaxy_folds(galaxies: np.ndarray, kfold: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(int(seed))
    gal = np.array(sorted(set(galaxies.tolist())))
    rng.shuffle(gal)
    folds = np.array_split(gal, int(kfold))
    return folds


# --- Thread env model (independent reimplementation of thread_env_model.py) ---

def _gate_factor(S: np.ndarray, *, S0: float | None, gate_p: float, k2: float, k4: float) -> np.ndarray:
    S = np.asarray(S, dtype=float)
    if S0 is None:
        return np.ones_like(S)

    S0f = float(S0)
    if not np.isfinite(S0f) or S0f <= 0:
        return np.ones_like(S)

    p = float(gate_p) if np.isfinite(gate_p) and gate_p > 0 else 1.0
    k2f = float(k2) if np.isfinite(k2) else 1.0
    k4f = float(k4) if np.isfinite(k4) else 0.0

    Seff = k2f * (S * S) + k4f * (S * S) * (S * S)
    x = np.maximum(Seff, 0.0) / max(S0f, 1e-300)
    xp = np.power(x, p)
    g = xp / (1.0 + xp)
    g = np.where(np.isfinite(g), g, 0.0)
    return np.clip(g, 0.0, 1.0)


def _stress_proxy(
    r_m: np.ndarray,
    g_bar: np.ndarray,
    *,
    g0: float,
    xi: float,
    eps: float,
    r_weight_power: float,
) -> np.ndarray:
    r_m = np.asarray(r_m, dtype=float)
    g_bar = np.asarray(g_bar, dtype=float)
    idx = np.argsort(r_m)
    r_sorted = r_m[idx]
    g_sorted = g_bar[idx]

    s_local = (np.maximum(g_sorted, 0.0) / max(float(g0), float(eps))) ** 2

    dr = np.diff(r_sorted, prepend=r_sorted[0])
    w = dr / (np.power(np.maximum(r_sorted, 0.0), float(r_weight_power)) + float(eps))
    s_cum = np.cumsum(s_local * w)

    med = float(np.median(s_cum))
    scale = med if np.isfinite(med) and med > 0 else 1.0
    s_cum_scaled = s_cum / max(scale, float(eps))

    S_sorted = (1.0 - float(xi)) * s_local + float(xi) * s_cum_scaled

    S = np.empty_like(S_sorted)
    S[idx] = S_sorted
    return S


def _env_thread(
    r_m: np.ndarray,
    g_bar: np.ndarray,
    *,
    g0: float,
    mode: str,
    q: float,
    xi: float,
    eps: float,
    r_weight_power: float,
    S0: float | None,
    gate_p: float,
    k2: float,
    k4: float,
) -> np.ndarray:
    S = _stress_proxy(r_m, g_bar, g0=g0, xi=xi, eps=eps, r_weight_power=r_weight_power)

    if mode == "down":
        e = np.power(1.0 + S, -float(q))
    elif mode == "up":
        e = np.power(1.0 + S, +float(q))
    else:
        raise ValueError(f"Unknown mode: {mode}")

    g = _gate_factor(S, S0=S0, gate_p=gate_p, k2=k2, k4=k4)
    e = 1.0 + g * (e - 1.0)

    e = np.where(np.isfinite(e), e, 1.0)
    e = np.maximum(e, 0.0)
    return e


def _norm_scale(e_raw: np.ndarray, norm: str) -> float:
    if norm == "none":
        return 1.0
    if norm == "mean":
        mu = float(np.mean(e_raw))
        return mu if np.isfinite(mu) and mu != 0 else 1.0
    if norm == "median":
        med = float(np.median(e_raw))
        return med if np.isfinite(med) and med != 0 else 1.0
    raise ValueError(f"Unknown norm: {norm}")


def _build_env_vector_thread(
    points_df: pd.DataFrame,
    *,
    g0: float,
    thread_mode: str,
    thread_q: float,
    thread_xi: float,
    thread_norm: str,
    thread_r_weight_power: float,
    thread_S0: float | None,
    thread_gate_p: float,
    thread_k2: float,
    thread_k4: float,
    norm_scale_ref: float | None,
) -> tuple[np.ndarray, float]:
    r_m = _extract_r_m(points_df)
    g_bar = _extract_g_bar(points_df)
    e_raw = _env_thread(
        r_m,
        g_bar,
        g0=float(g0),
        mode=str(thread_mode),
        q=float(thread_q),
        xi=float(thread_xi),
        eps=1e-30,
        r_weight_power=float(thread_r_weight_power),
        S0=None if thread_S0 is None else float(thread_S0),
        gate_p=float(thread_gate_p),
        k2=float(thread_k2),
        k4=float(thread_k4),
    )

    scale = float(norm_scale_ref) if norm_scale_ref is not None else float(_norm_scale(e_raw, str(thread_norm)))
    if scale == 0 or not np.isfinite(scale):
        e = np.ones_like(e_raw)
    else:
        e = e_raw / scale

    e = np.where(np.isfinite(e), e, 1.0)
    e = np.maximum(e, 0.0)
    return e, float(scale)


def _calibrate_thread_gate_from_galaxy(
    points_df: pd.DataFrame,
    *,
    g0: float,
    thread_mode: str,
    thread_q: float,
    thread_xi: float,
    thread_r_weight_power: float,
    gate_p: float,
    k2: float,
    gal_hi_p: float,
    gal_gate_eps: float,
    Sc_factor: float,
) -> dict[str, float]:
    r_m = _extract_r_m(points_df)
    g_bar = _extract_g_bar(points_df)

    S = _stress_proxy(r_m, g_bar, g0=float(g0), xi=float(thread_xi), eps=1e-30, r_weight_power=float(thread_r_weight_power))

    S_hi = float(np.percentile(S, float(gal_hi_p)))
    if not np.isfinite(S_hi) or S_hi <= 0:
        S_hi = 1.0

    Sc = float(Sc_factor) * S_hi
    k4 = float(k2) / (Sc * Sc)

    Seff_hi = float(k2) * (S_hi**2) + float(k4) * (S_hi**4)

    x_target = float((float(gal_gate_eps) / (1.0 - float(gal_gate_eps))) ** (1.0 / float(gate_p)))
    if x_target <= 0:
        x_target = float(float(gal_gate_eps) ** (1.0 / float(gate_p)))

    S0 = float(Seff_hi / max(x_target, 1e-30))

    x_hi = max(Seff_hi, 0.0) / max(S0, 1e-300)
    xp_hi = x_hi ** float(gate_p)
    gate_at_Shi = float(xp_hi / (1.0 + xp_hi))

    eps_open = 0.01
    x_open = float(((1.0 - eps_open) / eps_open) ** (1.0 / float(gate_p)))
    Seff_open_99 = float(x_open * S0)

    return {
        "S_hi": S_hi,
        "Sc": float(Sc),
        "k4": float(k4),
        "Seff_hi": float(Seff_hi),
        "S0": float(S0),
        "gate_p": float(gate_p),
        "gal_gate_eps": float(gal_gate_eps),
        "gate_at_Shi": float(gate_at_Shi),
        "Seff_open_99": float(Seff_open_99),
        # included for completeness (unused by build)
        "thread_mode": str(thread_mode),
        "thread_q": float(thread_q),
        "thread_xi": float(thread_xi),
        "thread_r_weight_power": float(thread_r_weight_power),
    }


def _run_cv(points_df: pd.DataFrame, *, env_model: str, stiffgate: bool) -> pd.DataFrame:
    gal_col = "galaxy"
    galaxies = points_df[gal_col].astype(str).to_numpy()

    kfold = 5
    seed = 2026
    folds = _make_galaxy_folds(galaxies, kfold, seed)

    # Canonical verdict command uses nA=nAlpha=1 (single-point scan)
    A = 0.1778279410038923
    alpha = 0.001

    g0 = 1.2e-10

    thread_mode = "down"
    thread_q = 0.6
    thread_xi = 0.5
    thread_norm = "median"
    thread_r_weight_power = 1.0
    thread_gate_p = 4.0
    thread_k2 = 1.0

    gal_hi_p = 99.9
    gal_gate_eps = 1e-6
    thread_Sc_factor = 10.0

    rows = []
    for i, test_gals in enumerate(folds):
        mask_test = points_df[gal_col].astype(str).isin(set(test_gals.tolist()))
        df_test = points_df[mask_test].copy()
        df_train = points_df[~mask_test].copy()

        # env vectors
        if env_model == "none":
            env_train = np.ones(len(df_train), dtype=float)
            env_test = np.ones(len(df_test), dtype=float)
        elif env_model == "thread":
            thread_S0_use = None
            thread_k4_use = 0.0
            if stiffgate:
                calib = _calibrate_thread_gate_from_galaxy(
                    df_train,
                    g0=g0,
                    thread_mode=thread_mode,
                    thread_q=thread_q,
                    thread_xi=thread_xi,
                    thread_r_weight_power=thread_r_weight_power,
                    gate_p=thread_gate_p,
                    k2=thread_k2,
                    gal_hi_p=gal_hi_p,
                    gal_gate_eps=gal_gate_eps,
                    Sc_factor=thread_Sc_factor,
                )
                thread_S0_use = float(calib["S0"])
                thread_k4_use = float(calib["k4"])

            env_train, scale = _build_env_vector_thread(
                df_train,
                g0=g0,
                thread_mode=thread_mode,
                thread_q=thread_q,
                thread_xi=thread_xi,
                thread_norm=thread_norm,
                thread_r_weight_power=thread_r_weight_power,
                thread_S0=thread_S0_use,
                thread_gate_p=thread_gate_p,
                thread_k2=thread_k2,
                thread_k4=thread_k4_use,
                norm_scale_ref=None,
            )
            env_test, _ = _build_env_vector_thread(
                df_test,
                g0=g0,
                thread_mode=thread_mode,
                thread_q=thread_q,
                thread_xi=thread_xi,
                thread_norm=thread_norm,
                thread_r_weight_power=thread_r_weight_power,
                thread_S0=thread_S0_use,
                thread_gate_p=thread_gate_p,
                thread_k2=thread_k2,
                thread_k4=thread_k4_use,
                norm_scale_ref=scale,
            )
        else:
            raise ValueError(f"Unsupported env_model for golden DM tests: {env_model}")

        gbar_train = _extract_g_bar(df_train)
        gobs_train = _extract_g_obs(df_train)
        sig_train = _extract_sigma_log10g(df_train)

        gbar_test = _extract_g_bar(df_test)
        gobs_test = _extract_g_obs(df_test)
        sig_test = _extract_sigma_log10g(df_test)

        chi2_train_base = _chi2_log10g(gbar_train, gobs_train, sig_train)
        gpred_train = _geo_add_const(gbar_train, A=A, alpha=alpha, g0=g0, env_vec=env_train)
        chi2_train_best = _chi2_log10g(gpred_train, gobs_train, sig_train)
        delta_train = float(chi2_train_base - chi2_train_best)

        chi2_test_base = _chi2_log10g(gbar_test, gobs_test, sig_test)
        gpred_test = _geo_add_const(gbar_test, A=A, alpha=alpha, g0=g0, env_vec=env_test)
        chi2_test_best = _chi2_log10g(gpred_test, gobs_test, sig_test)
        delta_test = float(chi2_test_base - chi2_test_best)

        rows.append(
            {
                "fold": i,
                "n_train_points": int(len(df_train)),
                "n_test_points": int(len(df_test)),
                "n_test_galaxies": int(len(set(test_gals.tolist()))),
                "A_best": float(A),
                "alpha_best": float(alpha),
                "chi2_train_base": float(chi2_train_base),
                "chi2_train_best": float(chi2_train_best),
                "delta_chi2_train": float(delta_train),
                "chi2_test_base": float(chi2_test_base),
                "chi2_test_best": float(chi2_test_best),
                "delta_chi2_test": float(delta_test),
            }
        )

    return pd.DataFrame(rows)


def _assert_dm_golden_matches(golden_csv: Path, *, env_model: str, stiffgate: bool):
    points_csv = Path(__file__).resolve().parents[3] / "data" / "sparc" / "sparc_points.csv"
    df_points = pd.read_csv(points_csv)

    gold = pd.read_csv(golden_csv)
    ref = _run_cv(df_points, env_model=env_model, stiffgate=stiffgate)

    assert len(gold) == 5
    assert len(ref) == 5

    # Hard checks on discrete columns
    assert np.array_equal(gold["fold"].to_numpy(int), ref["fold"].to_numpy(int))
    assert np.array_equal(gold["n_train_points"].to_numpy(int), ref["n_train_points"].to_numpy(int))
    assert np.array_equal(gold["n_test_points"].to_numpy(int), ref["n_test_points"].to_numpy(int))
    assert np.array_equal(gold["n_test_galaxies"].to_numpy(int), ref["n_test_galaxies"].to_numpy(int))

    # Float columns should match tightly (deterministic computation)
    for col, atol in [
        ("A_best", 0.0),
        ("alpha_best", 0.0),
        ("chi2_train_base", 2e-9),
        ("chi2_train_best", 2e-6),
        ("delta_chi2_train", 2e-6),
        ("chi2_test_base", 2e-9),
        ("chi2_test_best", 2e-6),
        ("delta_chi2_test", 2e-6),
    ]:
        g = gold[col].to_numpy(float)
        r = ref[col].to_numpy(float)
        assert np.allclose(g, r, atol=atol, rtol=0.0), f"Mismatch in {col} for {golden_csv.name}"


def test_dm_none_golden_outputs_match_reference_math():
    repo = Path(__file__).resolve().parents[3]
    golden_csv = repo / "integration_artifacts" / "out" / "verdict_golden" / "out" / "dm_cv_NONE_FIXED_A01778_a0001_seed2026_k5.csv"
    assert golden_csv.exists(), f"Missing golden output: {golden_csv}"
    _assert_dm_golden_matches(golden_csv, env_model="none", stiffgate=False)


def test_dm_thread_stiffgate_golden_outputs_match_reference_math():
    repo = Path(__file__).resolve().parents[3]
    golden_csv = repo / "integration_artifacts" / "out" / "verdict_golden" / "out" / "dm_cv_thread_STIFFGATE_FIXED_A01778_a0001_seed2026_k5.csv"
    assert golden_csv.exists(), f"Missing golden output: {golden_csv}"
    _assert_dm_golden_matches(golden_csv, env_model="thread", stiffgate=True)
