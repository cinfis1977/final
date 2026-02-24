from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


def _build_lattice_rest_positions(nx: int, ny: int, nz: int, spacing: float) -> np.ndarray:
    xs = (np.arange(nx) - (nx - 1) / 2.0) * spacing
    ys = (np.arange(ny) - (ny - 1) / 2.0) * spacing
    zs = (np.arange(nz) - (nz - 1) / 2.0) * spacing
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    return np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1).astype(float)


def _lattice_index(i: int, j: int, k: int, nx: int, ny: int, nz: int) -> int:
    return (i * ny * nz) + (j * nz) + k


def _iter_neighbors(nx: int, ny: int, nz: int):
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                a = _lattice_index(i, j, k, nx, ny, nz)
                if i + 1 < nx:
                    yield a, _lattice_index(i + 1, j, k, nx, ny, nz)
                if j + 1 < ny:
                    yield a, _lattice_index(i, j + 1, k, nx, ny, nz)
                if k + 1 < nz:
                    yield a, _lattice_index(i, j, k + 1, nx, ny, nz)


def _edge_mask(nx: int, ny: int, nz: int) -> np.ndarray:
    mask = np.zeros(nx * ny * nz, dtype=bool)
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                if i in (0, nx - 1) or j in (0, ny - 1) or k in (0, nz - 1):
                    mask[_lattice_index(i, j, k, nx, ny, nz)] = True
    return mask


def _compute_cm(cube_pos: np.ndarray, bub_pos: np.ndarray, m_cube: float, m_bub: float) -> np.ndarray:
    r = np.vstack([cube_pos, bub_pos]).astype(float)
    m = np.hstack(
        [
            np.full(cube_pos.shape[0], m_cube, dtype=float),
            np.full(bub_pos.shape[0], m_bub, dtype=float),
        ]
    )
    M = float(np.sum(m))
    return np.sum(r * m[:, None], axis=0) / max(M, 1e-30)


def _reduced_quadrupole_components(
    cube_pos: np.ndarray,
    bub_pos: np.ndarray,
    m_cube: float,
    m_bub: float,
    cm: np.ndarray,
) -> tuple[float, float, float, float, float, float]:
    r = np.vstack([cube_pos, bub_pos]).astype(float)
    m = np.hstack(
        [
            np.full(cube_pos.shape[0], m_cube, dtype=float),
            np.full(bub_pos.shape[0], m_bub, dtype=float),
        ]
    )

    cm = np.asarray(cm, dtype=float)
    r = r - cm

    x = r[:, 0]
    y = r[:, 1]
    z = r[:, 2]
    r2 = x * x + y * y + z * z
    one_third_r2 = (1.0 / 3.0) * r2

    Q_xx = float(np.sum(m * (x * x - one_third_r2)))
    Q_yy = float(np.sum(m * (y * y - one_third_r2)))
    Q_zz = float(np.sum(m * (z * z - one_third_r2)))
    Q_xy = float(np.sum(m * (x * y)))
    Q_xz = float(np.sum(m * (x * z)))
    Q_yz = float(np.sum(m * (y * z)))
    return Q_xx, Q_yy, Q_zz, Q_xy, Q_xz, Q_yz


def _finite_diff_second(arr: np.ndarray, dt: float) -> np.ndarray:
    d1 = np.gradient(arr, dt)
    return np.gradient(d1, dt)


def _drive_envelope(t: float, drive_t1: float, drive_env: str, drive_env_pow: float) -> float:
    if drive_t1 <= 0.0:
        return 0.0
    u = t / drive_t1
    if u < 0.0 or u > 1.0:
        return 0.0

    if drive_env == "flat":
        env = 1.0
    elif drive_env == "end":
        env = u
    elif drive_env == "start":
        env = 1.0 - u
    else:
        raise ValueError(f"Unknown drive_env={drive_env!r}")

    if drive_env_pow != 1.0:
        env = env ** float(drive_env_pow)
    return float(env)


def _drive_signal(t: float, *, drive_type: str, drive_amp: float, drive_f0_hz: float, drive_f1_hz: float, drive_t1: float, drive_env: str, drive_env_pow: float) -> float:
    env = _drive_envelope(t, drive_t1, drive_env, drive_env_pow)
    if env == 0.0 or drive_type == "none":
        return 0.0
    if drive_type == "impulse":
        return float(drive_amp * env)
    if drive_type == "sine":
        return float(drive_amp * env * math.sin(2.0 * math.pi * float(drive_f0_hz) * t))
    if drive_type == "chirp":
        f0 = float(drive_f0_hz)
        f1 = float(drive_f1_hz)
        T = float(drive_t1)
        k = (f1 - f0) / max(T, 1e-30)
        phase = 2.0 * math.pi * (f0 * t + 0.5 * k * t * t)
        return float(drive_amp * env * math.sin(phase))
    raise ValueError(f"Unknown drive_type={drive_type!r}")


def _make_drive_weights(rest_pos: np.ndarray, pattern: str, norm: str) -> np.ndarray:
    N = rest_pos.shape[0]
    w = np.zeros((N, 3), dtype=float)
    r0 = rest_pos - np.mean(rest_pos, axis=0, keepdims=True)
    x = r0[:, 0]
    y = r0[:, 1]

    if pattern == "point":
        return w
    if pattern == "quad_plus_xy":
        w[:, 0] = x
        w[:, 1] = -y
    elif pattern == "quad_cross_xy":
        w[:, 0] = y
        w[:, 1] = x
    else:
        raise ValueError(f"Unknown drive_pattern={pattern!r}")

    if norm == "none":
        return w
    if norm == "max":
        s = float(np.max(np.abs(w)))
        return w / s if s > 0 else w
    if norm == "l2":
        s = float(np.sqrt(np.sum(w * w)))
        return w / s if s > 0 else w
    if norm == "rms":
        s = float(np.sqrt(np.mean(w * w)))
        return w / s if s > 0 else w
    raise ValueError(f"Unknown drive_weight_norm={norm!r}")


def _simulate_reference_quadrupole_drive(*, drive_pattern: str) -> pd.DataFrame:
    # Defaults match improved_simulation_STABLE_v17_xy_quadrupole_drive_ANISO_PHYS_TENSOR_PHYS_FIXED4.py
    nx = ny = nz = 6
    spacing = 1.0

    dt = 1.0 / 4096.0
    duration = 0.30
    substeps = 4

    m_cube = 0.05
    k_out_x = k_out_y = k_out_z = 5e4
    c_out_x = c_out_y = c_out_z = 40.0

    gamma_cube = 5.0

    pin_edges = True
    k_pin = 2e5
    c_pin = 200.0

    m_bubble = 0.005
    T0 = 1336.0
    n_threads = 8
    c_rel = 50.0
    gamma_bubble = 0.0
    bubble_offset = 0.05
    ct_soft_eps = 0.05

    drive_type = "impulse"
    drive_amp = 1.0
    drive_f0_hz = 35.0
    drive_f1_hz = 250.0
    drive_t1 = 0.006
    drive_env = "end"
    drive_env_pow = 1.0

    drive_weight_norm = "l2"
    drive_idx = 0
    drive_axis = "z"

    rest = _build_lattice_rest_positions(nx, ny, nz, spacing)
    N = rest.shape[0]
    neigh = list(_iter_neighbors(nx, ny, nz))
    is_edge = _edge_mask(nx, ny, nz) if pin_edges else np.zeros(N, dtype=bool)

    pos = rest.copy()
    vel = np.zeros_like(pos)

    bub_pos = rest.copy()
    bub_pos[:, 2] += float(bubble_offset)
    bub_vel = np.zeros_like(bub_pos)

    w_drive = _make_drive_weights(rest, drive_pattern, drive_weight_norm)

    steps = int(round(duration / dt)) + 1
    t_arr = np.arange(steps, dtype=float) * float(dt)
    drive_arr = np.zeros(steps, dtype=float)

    sidx = int(np.clip(drive_idx, 0, N - 1))

    cube_x = np.zeros(steps)
    cube_y = np.zeros(steps)
    cube_z = np.zeros(steps)
    cube_vx = np.zeros(steps)
    cube_vy = np.zeros(steps)
    cube_vz = np.zeros(steps)
    cube_ax = np.zeros(steps)
    cube_ay = np.zeros(steps)
    cube_az = np.zeros(steps)

    bub_x = np.zeros(steps)
    bub_y = np.zeros(steps)
    bub_z = np.zeros(steps)
    bub_vx = np.zeros(steps)
    bub_vy = np.zeros(steps)
    bub_vz = np.zeros(steps)
    bub_ax = np.zeros(steps)
    bub_ay = np.zeros(steps)
    bub_az = np.zeros(steps)

    Q_xx = np.zeros(steps)
    Q_yy = np.zeros(steps)
    Q_zz = np.zeros(steps)
    Q_xy = np.zeros(steps)
    Q_xz = np.zeros(steps)
    Q_yz = np.zeros(steps)

    eps = float(max(ct_soft_eps, 1e-12))
    Ttot = float(T0) * int(n_threads)

    sub = int(max(substeps, 1))
    dt_sub = float(dt) / sub

    def drive_sig(tt: float) -> float:
        return _drive_signal(
            tt,
            drive_type=drive_type,
            drive_amp=drive_amp,
            drive_f0_hz=drive_f0_hz,
            drive_f1_hz=drive_f1_hz,
            drive_t1=drive_t1,
            drive_env=drive_env,
            drive_env_pow=drive_env_pow,
        )

    for n in range(steps):
        t0 = float(t_arr[n])
        drive_arr[n] = drive_sig(t0)

        for s in range(sub):
            t = t0 + s * dt_sub
            drv = drive_sig(t)

            F = np.zeros_like(pos)
            F_b = np.zeros_like(bub_pos)

            disp = pos - rest
            for a, b in neigh:
                du = disp[b] - disp[a]
                dv = vel[b] - vel[a]

                r0_ab = rest[b] - rest[a]
                ax = int(np.argmax(np.abs(r0_ab)))
                if ax == 0:
                    k_use = k_out_x
                    c_use = c_out_x
                elif ax == 1:
                    k_use = k_out_y
                    c_use = c_out_y
                else:
                    k_use = k_out_z
                    c_use = c_out_z

                f_ab = (k_use * du) + (c_use * dv)
                F[a] += f_ab
                F[b] -= f_ab

            if pin_edges:
                u = pos[is_edge] - rest[is_edge]
                F[is_edge] += -k_pin * u - c_pin * vel[is_edge]

            if gamma_cube != 0.0:
                F += -float(gamma_cube) * vel

            rel = bub_pos - pos
            rel_v = bub_vel - vel
            d = np.linalg.norm(rel, axis=1)
            n_hat = rel / np.maximum(d[:, None], eps)
            mag = Ttot * np.tanh(d / eps)
            Fbub = (-mag[:, None] * n_hat) + (-c_rel * rel_v)
            F_b += Fbub
            F += -Fbub

            if gamma_bubble != 0.0:
                F_b += -float(gamma_bubble) * bub_vel

            if drive_pattern == "point":
                axis = {"x": 0, "y": 1, "z": 2}[drive_axis]
                F[sidx, axis] += drv
            else:
                F += drv * w_drive

            acc = F / max(m_cube, 1e-30)
            acc_b = F_b / max(m_bubble, 1e-30)

            vel += acc * dt_sub
            pos += vel * dt_sub
            bub_vel += acc_b * dt_sub
            bub_pos += bub_vel * dt_sub

        # Report forces at t0 + dt (does not affect integration)
        t_report = t0 + dt
        drv_r = drive_sig(t_report)
        F = np.zeros_like(pos)
        F_b = np.zeros_like(bub_pos)

        disp = pos - rest
        for a, b in neigh:
            du = disp[b] - disp[a]
            dv = vel[b] - vel[a]

            r0_ab = rest[b] - rest[a]
            ax = int(np.argmax(np.abs(r0_ab)))
            if ax == 0:
                k_use = k_out_x
                c_use = c_out_x
            elif ax == 1:
                k_use = k_out_y
                c_use = c_out_y
            else:
                k_use = k_out_z
                c_use = c_out_z

            f_ab = (k_use * du) + (c_use * dv)
            F[a] += f_ab
            F[b] -= f_ab

        if pin_edges:
            u = pos[is_edge] - rest[is_edge]
            F[is_edge] += -k_pin * u - c_pin * vel[is_edge]
        if gamma_cube != 0.0:
            F += -float(gamma_cube) * vel

        rel = bub_pos - pos
        rel_v = bub_vel - vel
        d = np.linalg.norm(rel, axis=1)
        n_hat = rel / np.maximum(d[:, None], eps)
        mag = Ttot * np.tanh(d / eps)
        Fbub = (-mag[:, None] * n_hat) + (-c_rel * rel_v)
        F_b += Fbub
        F += -Fbub

        if gamma_bubble != 0.0:
            F_b += -float(gamma_bubble) * bub_vel

        if drive_pattern == "point":
            axis = {"x": 0, "y": 1, "z": 2}[drive_axis]
            F[sidx, axis] += drv_r
        else:
            F += drv_r * w_drive

        acc = F / max(m_cube, 1e-30)
        acc_b = F_b / max(m_bubble, 1e-30)

        cube_x[n], cube_y[n], cube_z[n] = pos[sidx]
        cube_vx[n], cube_vy[n], cube_vz[n] = vel[sidx]
        cube_ax[n], cube_ay[n], cube_az[n] = acc[sidx]

        bub_x[n], bub_y[n], bub_z[n] = bub_pos[sidx]
        bub_vx[n], bub_vy[n], bub_vz[n] = bub_vel[sidx]
        bub_ax[n], bub_ay[n], bub_az[n] = acc_b[sidx]

        cm = _compute_cm(pos, bub_pos, m_cube, m_bubble)
        qxx, qyy, qzz, qxy, qxz, qyz = _reduced_quadrupole_components(pos, bub_pos, m_cube, m_bubble, cm=cm)
        Q_xx[n], Q_yy[n], Q_zz[n] = qxx, qyy, qzz
        Q_xy[n], Q_xz[n], Q_yz[n] = qxy, qxz, qyz

    Qdd_xx = _finite_diff_second(Q_xx, dt)
    Qdd_yy = _finite_diff_second(Q_yy, dt)
    Qdd_zz = _finite_diff_second(Q_zz, dt)
    Qdd_xy = _finite_diff_second(Q_xy, dt)
    Qdd_xz = _finite_diff_second(Q_xz, dt)
    Qdd_yz = _finite_diff_second(Q_yz, dt)

    h_plus = Qdd_xx - Qdd_yy
    h_cross = 2.0 * Qdd_xy

    zeros = np.zeros_like(h_plus)

    return pd.DataFrame(
        {
            "t_s": t_arr,
            "drive": drive_arr,
            "cube_x": cube_x,
            "cube_y": cube_y,
            "cube_z": cube_z,
            "cube_vx": cube_vx,
            "cube_vy": cube_vy,
            "cube_vz": cube_vz,
            "cube_ax": cube_ax,
            "cube_ay": cube_ay,
            "cube_az": cube_az,
            "bubble_x": bub_x,
            "bubble_y": bub_y,
            "bubble_z": bub_z,
            "bubble_vx": bub_vx,
            "bubble_vy": bub_vy,
            "bubble_vz": bub_vz,
            "bubble_ax": bub_ax,
            "bubble_ay": bub_ay,
            "bubble_az": bub_az,
            "Q_xx": Q_xx,
            "Q_yy": Q_yy,
            "Q_zz": Q_zz,
            "Q_xy": Q_xy,
            "Q_xz": Q_xz,
            "Q_yz": Q_yz,
            "Qddot_xx": Qdd_xx,
            "Qddot_yy": Qdd_yy,
            "Qddot_zz": Qdd_zz,
            "Qddot_xy": Qdd_xy,
            "Qddot_xz": Qdd_xz,
            "Qddot_yz": Qdd_yz,
            "h_plus_proxy": h_plus,
            "h_cross_proxy": h_cross,
            "h_plus_A": zeros,
            "h_cross_A": zeros,
            "h_plus_B": zeros,
            "h_cross_B": zeros,
            "h_plus_AB": zeros,
            "h_cross_AB": zeros,
        }
    )


def _golden_path(name: str) -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "out"
        / "verdict_golden"
        / "out"
        / name
    )


def _assert_df_close(golden: pd.DataFrame, ref: pd.DataFrame, *, atol: float = 1e-9, rtol: float = 1e-12):
    assert list(golden.columns) == list(ref.columns)
    assert golden.shape == ref.shape

    g = golden.astype(float).to_numpy()
    r = ref.astype(float).to_numpy()
    np.testing.assert_allclose(r, g, atol=atol, rtol=rtol)


def test_ligo_quadrupole_plus_matches_golden():
    golden = pd.read_csv(_golden_path("LIGO_quadrupole_plus_FIXED4.csv"))
    ref = _simulate_reference_quadrupole_drive(drive_pattern="quad_plus_xy")
    _assert_df_close(golden, ref)


def test_ligo_quadrupole_cross_matches_golden():
    golden = pd.read_csv(_golden_path("LIGO_quadrupole_cross_FIXED4.csv"))
    ref = _simulate_reference_quadrupole_drive(drive_pattern="quad_cross_xy")
    _assert_df_close(golden, ref)
