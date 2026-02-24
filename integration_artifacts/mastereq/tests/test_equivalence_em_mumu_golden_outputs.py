import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

GEV2_TO_PB = 0.389379338e9

S_W2 = 0.23126
C_W2 = 1.0 - S_W2
MZ_GEV = 91.1876
GAMMAZ_GEV = 2.4952
ALPHA0 = 1.0 / 137.035999084

A_E = -1.0
V_E = -1.0 + 4.0 * S_W2

A_MU = -1.0
V_MU = -1.0 + 4.0 * S_W2
Q_MU = -1.0
N_C = 1.0

C_LIGHT = 299_792_458.0  # m/s


def _chis(s: float):
    denom = (s - MZ_GEV**2) ** 2 + (MZ_GEV * GAMMAZ_GEV) ** 2
    chi1 = (1.0 / (16.0 * S_W2 * C_W2)) * (s * (s - MZ_GEV**2)) / denom
    chi2 = (1.0 / (256.0 * (S_W2**2) * (C_W2**2))) * (s**2) / denom
    return chi1, chi2


def _dsigma_dOmega_mumu(c: float, sqrt_s: float) -> float:
    s = sqrt_s * sqrt_s
    chi1, chi2 = _chis(s)

    term1 = (1.0 + c * c) * (
        (Q_MU**2)
        - 2.0 * chi1 * V_E * V_MU * Q_MU
        + chi2 * (A_E * A_E + V_E * V_E) * (A_MU * A_MU + V_MU * V_MU)
    )
    term2 = 2.0 * c * (
        -2.0 * chi1 * A_E * A_MU * Q_MU
        + 4.0 * chi2 * A_E * A_MU * V_E * V_MU
    )
    return N_C * (ALPHA0**2) / (4.0 * s) * (term1 + term2)


def _dsigma_dcos_mumu(c: float, sqrt_s: float) -> float:
    return (2.0 * math.pi) * _dsigma_dOmega_mumu(c, sqrt_s) * GEV2_TO_PB


def _bin_avg(func, lo: float, hi: float, n: int = 400) -> float:
    xs = np.linspace(lo, hi, n)
    vals = np.array([func(float(x)) for x in xs], dtype=float)
    return float(vals.mean())


def _structure_factor(structure: str) -> float:
    structure = (structure or "").lower().strip()
    if structure.startswith("off"):
        return -1.0
    return 1.0


def _gen_factor(gen: str) -> float:
    gen = (gen or "").lower().strip()
    if gen == "lam2":
        return 2.0
    if gen == "lam3":
        return 3.0
    return 1.0


def _omega0_from_geom(mode: str, L0_km: float) -> float:
    mode = (mode or "").lower().strip()
    if mode == "fixed":
        return math.pi / max(L0_km, 1e-12)
    try:
        return float(mode)
    except Exception:
        return 0.0


def _load_pack(pack_path: Path):
    import json

    with open(pack_path, "r", encoding="utf-8") as f:
        pack = json.load(f)

    base = pack_path.resolve().parent

    def abspath(rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (base / p)

    data_csv = abspath(pack["data_csv"])
    cov_files = {k: abspath(v) for k, v in pack["cov_files"].items()}
    df = pd.read_csv(data_csv)
    return pack, df, cov_files


def _load_cov(cov_files: dict, which: str) -> np.ndarray:
    cov = pd.read_csv(Path(cov_files[which]), header=None).values.astype(float)
    return 0.5 * (cov + cov.T)


def _inv_cov(cov: np.ndarray) -> np.ndarray:
    cov = cov.copy()
    jitter = 0.0
    for _ in range(8):
        try:
            L = np.linalg.cholesky(cov)
            Linv = np.linalg.inv(L)
            return Linv.T @ Linv
        except np.linalg.LinAlgError:
            jitter = 1e-12 if jitter == 0.0 else jitter * 10.0
            cov += np.eye(cov.shape[0]) * jitter
    return np.linalg.pinv(cov)


def _fit_betas_group_nonneg(obs: np.ndarray, base_curve: np.ndarray, group_ids: np.ndarray, n_groups: int, cov_inv: np.ndarray, nonneg: bool) -> np.ndarray:
    N = len(obs)
    X = np.zeros((N, n_groups), dtype=float)
    for g in range(n_groups):
        m = group_ids == g
        X[m, g] = base_curve[m]

    try:
        L = np.linalg.cholesky(cov_inv)
        LT = L.T
        Xw = LT @ X
        yw = LT @ obs
    except np.linalg.LinAlgError:
        U, s, _ = np.linalg.svd(cov_inv)
        W = U * np.sqrt(np.maximum(s, 0.0))
        Xw = W.T @ X
        yw = W.T @ obs

    if nonneg:
        res = lsq_linear(Xw, yw, bounds=(0.0, np.inf), lsmr_tol="auto", verbose=0)
        beta = res.x
    else:
        beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    return beta.astype(float)


def _build_delta(
    *,
    cos_ctr: np.ndarray,
    sqrt_s: np.ndarray,
    A: float,
    alpha: float,
    phi: float,
    geo_structure: str,
    geo_gen: str,
    omega0_geom: str,
    L0_km: float,
    zeta: float,
    R_max: float,
    t_ref_GeV: float,
    env_scale: float,
) -> np.ndarray:
    s = np.asarray(sqrt_s, dtype=float) ** 2
    t_abs = 0.5 * s * (1.0 - np.asarray(cos_ctr, dtype=float))
    t_ref2 = max(float(t_ref_GeV), 1e-12) ** 2
    q = np.maximum(t_abs, t_ref2) / t_ref2
    f = float(alpha) * np.log(q)
    omega0 = _omega0_from_geom(omega0_geom, float(L0_km))
    x = float(zeta) * (1.0 + omega0 * (float(t_ref_GeV) + 1e-12)) * np.abs(f)
    R = float(R_max) * (1.0 - np.exp(-x))
    delta = float(env_scale) * float(A) * _structure_factor(geo_structure) * _gen_factor(geo_gen) * R * math.sin(float(phi)) * f
    return np.asarray(delta, dtype=float)


def _env_u_from_args(env_u: float | None, v_kms: float | None, r_over_Rs: float | None) -> float:
    if env_u is not None:
        return float(env_u)
    if v_kms is not None:
        v = float(v_kms) * 1_000.0
        return (v / C_LIGHT) ** 2
    if r_over_Rs is not None:
        r = float(r_over_Rs)
        return 0.5 / max(r, 1e-12)
    return 1e-8


def test_em_mumu_golden_outputs_match_reference_math():
    repo = Path(__file__).resolve().parents[3]
    pack_path = repo / "lep_mumu_pack.json"

    # Canonical verdict command parameters for all EM/MuMu golden runs
    alpha = 7.5e-05
    phi = 1.57079632679
    geo_structure = "offdiag"
    geo_gen = "lam2"
    omega0_geom = "fixed"
    L0_km = 810.0
    zeta = 0.05
    R_max = 10.0
    t_ref_GeV = 0.02
    shape_only = True
    freeze_betas = True
    beta_nonneg = True
    require_positive = True

    assert freeze_betas
    assert shape_only
    assert require_positive

    _, df, cov_files = _load_pack(pack_path)

    cos_lo = df["cos_lo"].to_numpy(float)
    cos_hi = df["cos_hi"].to_numpy(float)
    cos_ctr = df["cos_ctr"].to_numpy(float)
    obs = df["obs_pb"].to_numpy(float)
    sqrt_s = df["sqrt_s_GeV"].to_numpy(float)

    group_ids = df["group"].astype(int).to_numpy()
    uniq = sorted(set(int(x) for x in group_ids))
    gmap = {g: i for i, g in enumerate(uniq)}
    gid = np.array([gmap[int(x)] for x in group_ids], dtype=int)
    G = len(uniq)

    # env scaling for canonical runs (defaults imply env_scale==1)
    env_u0 = 1e-8
    env_u = _env_u_from_args(None, None, None)
    env_scale = env_u / max(env_u0, 1e-30)
    assert abs(env_scale - 1.0) < 1e-15

    cases = [
        ("total", 0.0, repo / "integration_artifacts/out/verdict_golden/out/EM/mumu_total_A0.csv"),
        ("total", 100000.0, repo / "integration_artifacts/out/verdict_golden/out/EM/mumu_total_A1e5.csv"),
        ("diag_total", 100000.0, repo / "integration_artifacts/out/verdict_golden/out/EM/mumu_diag_A1e5.csv"),
    ]

    for cov_kind, A, golden_csv in cases:
        assert golden_csv.exists(), f"Missing golden output: {golden_csv}"

        cov = _load_cov(cov_files, cov_kind)
        cov_inv = _inv_cov(cov)

        pred0 = np.array(
            [
                _bin_avg(lambda c: _dsigma_dcos_mumu(c, float(es)), float(lo), float(hi), n=400)
                for lo, hi, es in zip(cos_lo, cos_hi, sqrt_s)
            ],
            dtype=float,
        )

        betas_sm = _fit_betas_group_nonneg(obs, pred0, gid, G, cov_inv, beta_nonneg)
        pred_sm = np.zeros_like(obs, dtype=float)
        for g in range(G):
            m = gid == g
            pred_sm[m] = betas_sm[g] * pred0[m]

        delta = _build_delta(
            cos_ctr=cos_ctr,
            sqrt_s=sqrt_s,
            A=A,
            alpha=alpha,
            phi=phi,
            geo_structure=geo_structure,
            geo_gen=geo_gen,
            omega0_geom=omega0_geom,
            L0_km=L0_km,
            zeta=zeta,
            R_max=R_max,
            t_ref_GeV=t_ref_GeV,
            env_scale=env_scale,
        )

        if shape_only:
            for g in range(G):
                m = gid == g
                delta[m] = delta[m] - float(np.mean(delta[m]))

        if require_positive:
            assert not np.any(1.0 + delta <= 0.0)

        pred_geo = pred_sm * (1.0 + delta)
        betas_geo = betas_sm.copy()

        gold = pd.read_csv(golden_csv)

        # Primary computed columns
        assert np.allclose(gold["pred0_pb"].to_numpy(float), pred0, atol=5e-10, rtol=0.0)
        assert np.allclose(gold["pred_sm"].to_numpy(float), pred_sm, atol=5e-10, rtol=0.0)
        assert np.allclose(gold["delta"].to_numpy(float), delta, atol=2e-12, rtol=0.0)
        assert np.allclose(gold["pred_geo"].to_numpy(float), pred_geo, atol=5e-10, rtol=0.0)

        # Beta columns are deterministic functions of fitted betas + group ids
        beta_sm_row = np.array([betas_sm[g] for g in gid], dtype=float)
        beta_geo_row = np.array([betas_geo[g] for g in gid], dtype=float)
        assert np.allclose(gold["beta_sm"].to_numpy(float), beta_sm_row, atol=5e-12, rtol=0.0)
        assert np.allclose(gold["beta_geo"].to_numpy(float), beta_geo_row, atol=5e-12, rtol=0.0)
