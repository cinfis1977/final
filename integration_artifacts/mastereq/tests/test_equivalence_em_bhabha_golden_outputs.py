import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

C_LIGHT = 299_792_458.0  # m/s


def _load_pack(pack_path: Path):
    import json

    with open(pack_path, "r", encoding="utf-8") as f:
        pack = json.load(f)

    base = pack_path.resolve().parent

    def abspath(rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (base / p)

    paths = {k: abspath(v) for k, v in pack["paths"].items()}
    cols = pack.get("columns", {})
    return pack, paths, cols


def _load_cov(paths: dict, which: str) -> np.ndarray:
    key_map = {
        "total": "cov_total_csv",
        "stat": "cov_stat_csv",
        "sys_corr": "cov_sys_csv",
        "diag_total": "cov_diag_total_csv",
    }
    cov_path = Path(paths[key_map[which]])
    return pd.read_csv(cov_path, header=None).values.astype(float)


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


def _gen_factor(name: str) -> float:
    name = (name or "").lower()
    if name == "lam1":
        return 0.5
    if name == "lam2":
        return 1.0
    if name == "lam3":
        return 1.5
    if name == "lam4":
        return 2.0
    try:
        return float(name)
    except Exception:
        return 1.0


def _struct_factor(name: str) -> float:
    name = (name or "").lower()
    if name == "diag":
        return 1.0
    if name == "offdiag":
        return -1.0
    return 1.0


def _omega0_from_geom(mode: str, L0_km: float) -> float:
    mode = (mode or "").lower()
    if mode == "fixed":
        return math.pi / max(L0_km, 1e-12)
    try:
        return float(mode)
    except Exception:
        return 0.0


def _build_delta(
    *,
    cos_ctr: np.ndarray,
    sqrt_s_GeV: float,
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
    shape_only: bool,
) -> np.ndarray:
    s = float(sqrt_s_GeV) ** 2
    t_abs = 0.5 * s * (1.0 - np.asarray(cos_ctr, dtype=float))
    t_ref2 = max(float(t_ref_GeV), 1e-12) ** 2
    q = np.maximum(t_abs, t_ref2) / t_ref2
    f = float(alpha) * np.log(q)
    omega0 = _omega0_from_geom(omega0_geom, float(L0_km))
    x = float(zeta) * (1.0 + omega0 * (float(t_ref_GeV) + 1e-12)) * np.abs(f)
    R = float(R_max) * (1.0 - np.exp(-x))
    delta = float(env_scale) * float(A) * _struct_factor(geo_structure) * _gen_factor(geo_gen) * R * math.sin(float(phi)) * f
    if shape_only:
        delta = delta - float(np.mean(delta))
    return np.asarray(delta, dtype=float)


def _infer_group_ids_from_repeated_bins(df: pd.DataFrame, xlo_col: str, xhi_col: str, mode: str = "auto"):
    if "group_id" in df.columns:
        g = df["group_id"].astype(int).to_numpy()
        return g, int(g.max()) + 1, int(df[[xlo_col, xhi_col]].drop_duplicates().shape[0]), "data"

    keys = [(round(float(a), 8), round(float(b), 8)) for a, b in zip(df[xlo_col].to_numpy(float), df[xhi_col].to_numpy(float))]
    N = len(keys)

    def _is_period(P: int) -> bool:
        if P <= 0 or N % P != 0:
            return False
        base = keys[:P]
        for g in range(N // P):
            if keys[g * P : (g + 1) * P] != base:
                return False
        return True

    if mode in ("auto", "block"):
        first = keys[0]
        candidates = [i for i, k in enumerate(keys) if (i > 0 and k == first)]
        P = None
        for cand in candidates:
            if _is_period(cand):
                P = cand
                break
        if P is None:
            n_unique = len(set(keys))
            if _is_period(n_unique):
                P = n_unique
        if P is not None:
            g = np.array([i // P for i in range(N)], dtype=int)
            return g, int(N // P), int(P), "block"

        if mode == "block":
            raise RuntimeError("group_mode=block selected, but could not infer repeated contiguous blocks from data")

    if mode in ("auto", "occ"):
        counter: dict[tuple[float, float], int] = {}
        g = []
        for k in keys:
            occ = counter.get(k, 0)
            g.append(occ)
            counter[k] = occ + 1
        g = np.array(g, dtype=int)
        return g, int(g.max()) + 1, int(df[[xlo_col, xhi_col]].drop_duplicates().shape[0]), "occ"

    raise RuntimeError(f"Unknown group_mode: {mode}")


def _build_import_base_curve(
    *,
    df_data: pd.DataFrame,
    baseline_df: pd.DataFrame,
    baseline_col: str,
    baseline_group_col: str,
    group_ids: np.ndarray,
    xlo_data: str,
    xhi_data: str,
    xlo_base: str,
    xhi_base: str,
) -> np.ndarray:
    def _k(a, b):
        return (round(float(a), 8), round(float(b), 8))

    bmap: dict[tuple[int, float, float], float] = {}
    for gid, a, b, v in zip(
        baseline_df[baseline_group_col].astype(int).to_numpy(int),
        baseline_df[xlo_base].to_numpy(float),
        baseline_df[xhi_base].to_numpy(float),
        baseline_df[baseline_col].to_numpy(float),
    ):
        kk = (int(gid),) + _k(a, b)
        if kk in bmap:
            bmap[kk] = 0.5 * (bmap[kk] + float(v))
        else:
            bmap[kk] = float(v)

    keys = [(int(g),) + _k(a, b) for g, a, b in zip(group_ids, df_data[xlo_data].to_numpy(float), df_data[xhi_data].to_numpy(float))]
    missing = [kk for kk in set(keys) if kk not in bmap]
    assert not missing, f"baseline_csv missing (group_id, bin) pairs (showing up to 5): {missing[:5]}"

    return np.array([bmap[kk] for kk in keys], dtype=float)


def _fit_betas_import_groups(
    *,
    obs: np.ndarray,
    base_curve: np.ndarray,
    group_ids: np.ndarray,
    n_groups: int,
    cov_inv: np.ndarray,
    nonneg: bool,
) -> np.ndarray:
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


def test_em_bhabha_golden_outputs_match_reference_math():
    repo = Path(__file__).resolve().parents[3]

    pack_path = repo / "lep_bhabha_pack.json"
    baseline_csv = repo / "bhagen_cos09_v4_baseline_L0_Sp1.csv"

    # Canonical verdict command parameters for all EM/Bhabha golden runs
    sqrt_s_GeV = 189.0
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

    assert freeze_betas  # keep this test aligned to the canonical golden runs

    pack, paths, cols = _load_pack(pack_path)
    df = pd.read_csv(Path(paths["data_csv"]))

    xlo = cols["x_lo"]
    xhi = cols["x_hi"]
    xct = cols["x_ctr"]
    y = cols["y"]

    obs = df[y].to_numpy(float)
    cos_ctr = df[xct].to_numpy(float)

    # group inference + baseline import
    group_ids, n_groups, _, _ = _infer_group_ids_from_repeated_bins(df, xlo, xhi, mode="auto")
    bdf = pd.read_csv(baseline_csv)

    # baseline CSV uses the same bin edge columns in this repo
    base_curve = _build_import_base_curve(
        df_data=df,
        baseline_df=bdf,
        baseline_col="sm_pred_pb",
        baseline_group_col="group_id",
        group_ids=group_ids,
        xlo_data=xlo,
        xhi_data=xhi,
        xlo_base=xlo,
        xhi_base=xhi,
    )

    # env scaling for canonical runs (defaults imply env_scale==1)
    env_u0 = 1e-8
    env_u = _env_u_from_args(None, None, None)
    env_scale = env_u / max(env_u0, 1e-30)
    assert abs(env_scale - 1.0) < 1e-15

    cases = [
        ("total", 0.0, repo / "integration_artifacts/out/verdict_golden/out/EM/bhabha_total_A0.csv"),
        ("total", 100000.0, repo / "integration_artifacts/out/verdict_golden/out/EM/bhabha_total_A1e5.csv"),
        ("total", -100000.0, repo / "integration_artifacts/out/verdict_golden/out/EM/bhabha_total_Aneg1e5.csv"),
        ("diag_total", 0.0, repo / "integration_artifacts/out/verdict_golden/out/EM/bhabha_diag_A0.csv"),
        ("diag_total", 100000.0, repo / "integration_artifacts/out/verdict_golden/out/EM/bhabha_diag_A1e5.csv"),
        ("diag_total", -100000.0, repo / "integration_artifacts/out/verdict_golden/out/EM/bhabha_diag_Aneg1e5.csv"),
    ]

    for cov_kind, A, golden_csv in cases:
        assert golden_csv.exists(), f"Missing golden output: {golden_csv}"

        cov = _load_cov(paths, cov_kind)
        cov_inv = _inv_cov(cov)

        betas_sm = _fit_betas_import_groups(
            obs=obs,
            base_curve=base_curve,
            group_ids=group_ids,
            n_groups=n_groups,
            cov_inv=cov_inv,
            nonneg=beta_nonneg,
        )
        pred_sm = np.zeros_like(obs, dtype=float)
        for g in range(n_groups):
            m = group_ids == g
            pred_sm[m] = betas_sm[g] * base_curve[m]

        delta = _build_delta(
            cos_ctr=cos_ctr,
            sqrt_s_GeV=sqrt_s_GeV,
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
            shape_only=shape_only,
        )

        pred_geo = pred_sm * (1.0 + delta)
        ratio_geo_sm = np.where(pred_sm != 0, pred_geo / pred_sm, np.nan)

        gold = pd.read_csv(golden_csv)
        assert np.array_equal(gold["group_id"].astype(int).to_numpy(), group_ids)
        assert np.allclose(gold["obs_pb"].to_numpy(float), obs, atol=0.0, rtol=0.0)

        for col, ref, atol in [
            ("pred_sm", pred_sm, 2e-10),
            ("delta", delta, 2e-12),
            ("pred_geo", pred_geo, 2e-10),
            ("ratio_geo_sm", ratio_geo_sm, 2e-12),
        ]:
            assert np.allclose(gold[col].to_numpy(float), ref, atol=atol, rtol=0.0), f"Mismatch in {col} for cov={cov_kind} A={A}"
