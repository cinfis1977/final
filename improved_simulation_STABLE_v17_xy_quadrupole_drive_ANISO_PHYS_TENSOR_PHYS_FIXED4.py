#!/usr/bin/env python3
"""
improved_simulation_STABLE_v17_xy_quadrupole_drive.py

Drop-in successor to v14 that focuses on **numerical stability** while keeping the
physics-motivated observable (global reduced mass quadrupole → strain proxy).

Why v17 exists:
  In v14, users can hit NaN/Inf blow-ups when using 3D DOF + constant-tension (CT)
  coupling + distributed quadrupole drive. The root cause is an inconsistent
  "T0AUTO" estimate for CT-softened tension (tanh(d/eps)) plus too-large initial
  offsets (bubble_offset >> ct_soft_eps) that start the CT force in saturation.

Fixes in v17:
  1) **T0AUTO is CT-consistent**:
       For small d, tanh(d/eps)≈d/eps ⇒ effective stiffness k_eff≈Ttot/eps.
       Targeting f implies: Ttot ≈ m (2πf)^2 eps ⇒ T0 = Ttot/n_threads.

  2) **Substepping**:
       Integrate with dt_sub = dt/substeps (default 4) but still output at dt.

  3) **Cube damping** (gamma_cube):
       Adds -gamma_cube * v to cube forces to prevent runaway energy growth.

  4) Safer defaults:
       bubble_offset default is 0.05 (matches ct_soft_eps default), keeping the
       initial CT force in its linear regime.

Outputs (CSV):
  t_s, drive,
  cube_{x,y,z}, cube_v{xyz}, cube_a{xyz},
  bubble_{x,y,z}, bubble_v{xyz}, bubble_a{xyz},
  Q_{xx,yy,zz,xy,xz,yz}, Qddot_{xx,yy,zz,xy,xz,yz},
  h_plus_proxy, h_cross_proxy
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Optional

import numpy as np

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


@dataclass
class SimParams:
    nx: int
    ny: int
    nz: int
    spacing: float

    dt: float
    duration: float
    substeps: int

    m_cube: float
    k_out: float
    k_out_x: float
    k_out_y: float
    k_out_z: float
    c_out: float
    c_out_x: float
    c_out_y: float
    c_out_z: float

    gamma_cube: float

    pin_edges: bool
    k_pin: float
    c_pin: float

    m_bubble: float
    T0: float
    n_threads: int
    c_rel: float
    gamma_bubble: float
    bubble_offset: float
    ct_soft_eps: float

    drive_type: str
    drive_amp: float
    drive_f0_hz: float
    drive_f1_hz: float
    drive_t1: float
    drive_env: str
    drive_env_pow: float
    drive_pattern: str
    drive_weight_norm: str
    drive_idx: int
    drive_axis: str

    abort_on_nan: bool

    # Optional full-tensor anisotropy (rotated principal axes). If k_diag/c_diag are set,
    # bond coefficients are computed as k_use = e0^T K e0 (same for C), where e0 is the bond rest-unit-vector.
    k_diag: Optional[Tuple[float, float, float]] = None
    c_diag: Optional[Tuple[float, float, float]] = None
    k_rot_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # yaw,pitch,roll in degrees (ZYX order)
    c_rot_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # yaw,pitch,roll in degrees (ZYX order)
    gyro_omega: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # rad/s; adds F += gyro_gain*m*(omega×v)
    gyro_gain: float = 0.0

    tensor_mode: str = "projected"  # projected: k_use=e0^TKe0; full: f=K@du (mixing)
    readout_split: str = "none"  # none|x|y: A/B half readouts + differential channels (readout trick)
def _parse_triplet(s: str) -> Tuple[float, float, float]:
    parts = [p.strip() for p in str(s).split(',') if p.strip() != '']
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Expected three comma-separated numbers like '1,2,3'.")
    return (float(parts[0]), float(parts[1]), float(parts[2]))

def _rot_zyx_deg(yaw_deg: float, pitch_deg: float, roll_deg: float) -> np.ndarray:
    """Return rotation matrix R = Rz(yaw) @ Ry(pitch) @ Rx(roll), angles in degrees."""
    yaw = np.deg2rad(yaw_deg)
    pitch = np.deg2rad(pitch_deg)
    roll = np.deg2rad(roll_deg)
    cz, sz = float(np.cos(yaw)), float(np.sin(yaw))
    cy, sy = float(np.cos(pitch)), float(np.sin(pitch))
    cx, sx = float(np.cos(roll)), float(np.sin(roll))
    Rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]], dtype=float)
    Ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=float)
    Rx = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]], dtype=float)
    return Rz @ Ry @ Rx

def _tensor_from_diag_rot(diag: Tuple[float, float, float], rot_deg: Tuple[float, float, float]) -> np.ndarray:
    """Build symmetric tensor: K = R diag(diag) R^T."""
    R = _rot_zyx_deg(rot_deg[0], rot_deg[1], rot_deg[2])
    D = np.diag(np.array(diag, dtype=float))
    return R @ D @ R.T


def build_lattice_rest_positions(nx: int, ny: int, nz: int, spacing: float) -> np.ndarray:
    xs = (np.arange(nx) - (nx - 1) / 2.0) * spacing
    ys = (np.arange(ny) - (ny - 1) / 2.0) * spacing
    zs = (np.arange(nz) - (nz - 1) / 2.0) * spacing
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    return np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1).astype(float)


def lattice_index(i: int, j: int, k: int, nx: int, ny: int, nz: int) -> int:
    return (i * ny * nz) + (j * nz) + k


def iter_neighbors(nx: int, ny: int, nz: int):
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                a = lattice_index(i, j, k, nx, ny, nz)
                if i + 1 < nx:
                    yield a, lattice_index(i + 1, j, k, nx, ny, nz)
                if j + 1 < ny:
                    yield a, lattice_index(i, j + 1, k, nx, ny, nz)
                if k + 1 < nz:
                    yield a, lattice_index(i, j, k + 1, nx, ny, nz)


def edge_mask(nx: int, ny: int, nz: int) -> np.ndarray:
    mask = np.zeros(nx * ny * nz, dtype=bool)
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                if i in (0, nx - 1) or j in (0, ny - 1) or k in (0, nz - 1):
                    mask[lattice_index(i, j, k, nx, ny, nz)] = True
    return mask


def compute_cm(
    cube_pos: np.ndarray,
    bub_pos: np.ndarray,
    m_cube: float,
    m_bub: float,
) -> np.ndarray:
    r = np.vstack([cube_pos, bub_pos]).astype(float)
    m = np.hstack([
        np.full(cube_pos.shape[0], m_cube, dtype=float),
        np.full(bub_pos.shape[0],  m_bub,  dtype=float),
    ])
    M = float(np.sum(m))
    cm = np.sum(r * m[:, None], axis=0) / max(M, 1e-30)
    return cm


def reduced_quadrupole_components(
    cube_pos: np.ndarray,
    bub_pos: np.ndarray,
    m_cube: float,
    m_bub: float,
    cm: Optional[np.ndarray] = None,
) -> Tuple[float, float, float, float, float, float]:
    r = np.vstack([cube_pos, bub_pos]).astype(float)
    m = np.hstack([
        np.full(cube_pos.shape[0], m_cube, dtype=float),
        np.full(bub_pos.shape[0],  m_bub,  dtype=float),
    ])
    if cm is None:
        M = float(np.sum(m))
        cm = np.sum(r * m[:, None], axis=0) / max(M, 1e-30)
    cm = np.asarray(cm, dtype=float)
    r = r - cm

    x = r[:, 0]; y = r[:, 1]; z = r[:, 2]
    r2 = x * x + y * y + z * z
    one_third_r2 = (1.0 / 3.0) * r2

    Q_xx = float(np.sum(m * (x * x - one_third_r2)))
    Q_yy = float(np.sum(m * (y * y - one_third_r2)))
    Q_zz = float(np.sum(m * (z * z - one_third_r2)))
    Q_xy = float(np.sum(m * (x * y)))
    Q_xz = float(np.sum(m * (x * z)))
    Q_yz = float(np.sum(m * (y * z)))
    return Q_xx, Q_yy, Q_zz, Q_xy, Q_xz, Q_yz


def finite_diff_second(arr: np.ndarray, dt: float) -> np.ndarray:
    d1 = np.gradient(arr, dt)
    return np.gradient(d1, dt)


def drive_envelope(t: float, p: SimParams) -> float:
    if p.drive_t1 <= 0:
        return 0.0
    u = t / p.drive_t1
    if u < 0.0 or u > 1.0:
        return 0.0
    if p.drive_env == "flat":
        env = 1.0
    elif p.drive_env == "end":
        env = u
    elif p.drive_env == "start":
        env = 1.0 - u
    else:
        raise ValueError(f"Unknown drive_env={p.drive_env!r}")
    if p.drive_env_pow != 1.0:
        env = env ** float(p.drive_env_pow)
    return float(env)


def drive_signal(t: float, p: SimParams) -> float:
    env = drive_envelope(t, p)
    if env == 0.0 or p.drive_type == "none":
        return 0.0
    if p.drive_type == "impulse":
        return float(p.drive_amp * env)
    if p.drive_type == "sine":
        f = float(p.drive_f0_hz)
        return float(p.drive_amp * env * math.sin(2.0 * math.pi * f * t))
    if p.drive_type == "chirp":
        f0 = float(p.drive_f0_hz)
        f1 = float(p.drive_f1_hz)
        T = float(p.drive_t1)
        k = (f1 - f0) / max(T, 1e-30)
        phase = 2.0 * math.pi * (f0 * t + 0.5 * k * t * t)
        return float(p.drive_amp * env * math.sin(phase))
    raise ValueError(f"Unknown drive_type={p.drive_type!r}")


def make_drive_weights(rest_pos: np.ndarray, pattern: str, norm: str) -> np.ndarray:
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


def simulate(p: SimParams, out_csv: Path, plot_png: Optional[Path]) -> None:
    rest = build_lattice_rest_positions(p.nx, p.ny, p.nz, p.spacing)
    N = rest.shape[0]
    neigh = list(iter_neighbors(p.nx, p.ny, p.nz))
    is_edge = edge_mask(p.nx, p.ny, p.nz) if p.pin_edges else np.zeros(N, dtype=bool)

    pos = rest.copy()
    vel = np.zeros_like(pos)

    bub_pos = rest.copy()
    bub_pos[:, 2] += float(p.bubble_offset)
    bub_vel = np.zeros_like(bub_pos)

    w_drive = make_drive_weights(rest, p.drive_pattern, p.drive_weight_norm)

    # Optional readout split (A/B halves of the lattice). This is a *readout* trick
    # to help break "Gate-0" colinearity (template degeneracy) when the global quadrupole
    # collapses to a single dominant mode.
    maskA = None
    maskB = None
    if str(getattr(p, "readout_split", "none")).lower() != "none":
        axis = str(p.readout_split).lower()
        if axis not in ("x", "y"):
            raise ValueError(f"readout_split must be none|x|y, got {p.readout_split!r}")
        idx = np.arange(N, dtype=int)
        ii = idx % p.nx
        jj = (idx // p.nx) % p.ny
        if axis == "x":
            maskA = ii < (p.nx // 2)
        else:
            maskA = jj < (p.ny // 2)
        maskB = ~maskA


    steps = int(round(p.duration / p.dt)) + 1
    t_arr = np.arange(steps, dtype=float) * float(p.dt)
    drive_arr = np.zeros(steps, dtype=float)

    sidx = int(np.clip(p.drive_idx, 0, N - 1))
    cube_x = np.zeros(steps); cube_y = np.zeros(steps); cube_z = np.zeros(steps)
    cube_vx = np.zeros(steps); cube_vy = np.zeros(steps); cube_vz = np.zeros(steps)
    cube_ax = np.zeros(steps); cube_ay = np.zeros(steps); cube_az = np.zeros(steps)
    bub_x = np.zeros(steps); bub_y = np.zeros(steps); bub_z = np.zeros(steps)
    bub_vx = np.zeros(steps); bub_vy = np.zeros(steps); bub_vz = np.zeros(steps)
    bub_ax = np.zeros(steps); bub_ay = np.zeros(steps); bub_az = np.zeros(steps)

    Q_xx = np.zeros(steps); Q_yy = np.zeros(steps); Q_zz = np.zeros(steps)
    Q_xy = np.zeros(steps); Q_xz = np.zeros(steps); Q_yz = np.zeros(steps)

    # A/B split quadrupoles (only used if readout_split != none; otherwise remain zeros)
    Q_xx_A = np.zeros(steps); Q_yy_A = np.zeros(steps); Q_zz_A = np.zeros(steps)
    Q_xy_A = np.zeros(steps); Q_xz_A = np.zeros(steps); Q_yz_A = np.zeros(steps)
    Q_xx_B = np.zeros(steps); Q_yy_B = np.zeros(steps); Q_zz_B = np.zeros(steps)
    Q_xy_B = np.zeros(steps); Q_xz_B = np.zeros(steps); Q_yz_B = np.zeros(steps)


    eps = float(max(p.ct_soft_eps, 1e-12))
    Ttot = float(p.T0) * int(p.n_threads)

    sub = int(max(p.substeps, 1))
    dt_sub = float(p.dt) / sub
    # Optional full-tensor anisotropy (rotated principal axes) + optional gyro term
    K_mat = _tensor_from_diag_rot(p.k_diag, p.k_rot_deg) if p.k_diag is not None else None
    C_mat = _tensor_from_diag_rot(p.c_diag, p.c_rot_deg) if p.c_diag is not None else None
    omega_vec = np.array(p.gyro_omega, dtype=float)

    warned_scale = False

    for n in range(steps):
        t0 = float(t_arr[n])
        drv0 = drive_signal(t0, p)
        drive_arr[n] = drv0

        # substep integration
        for s in range(sub):
            t = t0 + s * dt_sub
            drv = drive_signal(t, p)

            F = np.zeros_like(pos)
            F_b = np.zeros_like(bub_pos)

            # Outer network (linear springs on displacements)
            disp = pos - rest
            for a, b in neigh:
                du = disp[b] - disp[a]
                dv = vel[b] - vel[a]
                # --- ANISO (PHYS+TENSOR): choose stiffness/damping by bond direction ---
                r0_ab = rest[b] - rest[a]  # bond rest-direction
                n0 = float(np.linalg.norm(r0_ab))
                if n0 < 1e-30:
                    e0 = np.array([1.0, 0.0, 0.0], dtype=float)
                else:
                    e0 = (r0_ab / n0).astype(float)

                # stiffness
                if K_mat is not None and p.tensor_mode == "full":
                    f_k = (K_mat @ du).astype(float)
                else:
                    if K_mat is not None:
                        k_use = float(e0 @ K_mat @ e0)
                    else:
                        ax = int(np.argmax(np.abs(r0_ab)))
                        if ax == 0:
                            k_use = p.k_out_x
                        elif ax == 1:
                            k_use = p.k_out_y
                        else:
                            k_use = p.k_out_z
                    f_k = k_use * du

                # damping
                if C_mat is not None and p.tensor_mode == "full":
                    f_c = (C_mat @ dv).astype(float)
                else:
                    if C_mat is not None:
                        c_use = float(e0 @ C_mat @ e0)
                    else:
                        ax = int(np.argmax(np.abs(r0_ab)))
                        if ax == 0:
                            c_use = p.c_out_x
                        elif ax == 1:
                            c_use = p.c_out_y
                        else:
                            c_use = p.c_out_z
                    f_c = c_use * dv

                f_ab = f_k + f_c
                F[a] += f_ab
                F[b] -= f_ab

            # Pin edges
            if p.pin_edges:
                u = pos[is_edge] - rest[is_edge]
                F[is_edge] += -p.k_pin * u - p.c_pin * vel[is_edge]

            # Cube absolute damping
            if p.gamma_cube != 0.0:
                F += -float(p.gamma_cube) * vel

            # Bubble-cube CT + relative damping
            rel = bub_pos - pos
            rel_v = bub_vel - vel
            d = np.linalg.norm(rel, axis=1)
            n_hat = rel / np.maximum(d[:, None], eps)
            mag = Ttot * np.tanh(d / eps)
            F_t = -mag[:, None] * n_hat
            F_d = -p.c_rel * rel_v
            Fbub = F_t + F_d
            F_b += Fbub
            F += -Fbub

            if p.gamma_bubble != 0.0:
                F_b += -float(p.gamma_bubble) * bub_vel

            # Drive
            if p.drive_pattern == "point":
                ax = {"x": 0, "y": 1, "z": 2}[p.drive_axis]
                F[sidx, ax] += drv
            else:
                F += drv * w_drive

            # Optional gyro / Coriolis-like term (can help break plus/cross degeneracy)
            if p.gyro_gain != 0.0 and np.any(omega_vec != 0.0):
                F += p.gyro_gain * p.m_cube * np.cross(omega_vec[None, :], vel)
                F_b += p.gyro_gain * p.m_bubble * np.cross(omega_vec[None, :], bub_vel)

            if p.abort_on_nan:
                if (not np.isfinite(pos).all()) or (not np.isfinite(bub_pos).all()):
                    raise FloatingPointError("NaN/Inf in positions")
                if (not np.isfinite(vel).all()) or (not np.isfinite(bub_vel).all()):
                    raise FloatingPointError("NaN/Inf in velocities")

            acc = F / max(p.m_cube, 1e-30)
            acc_b = F_b / max(p.m_bubble, 1e-30)

            # semi-implicit Euler (stable with substeps)
            vel += acc * dt_sub
            pos += vel * dt_sub
            bub_vel += acc_b * dt_sub
            bub_pos += bub_vel * dt_sub

        # Record (coarse step)
        # Approximate acceleration at the end of the last substep using damping-only + spring-only would be expensive;
        # instead, compute one force evaluation at t0+dt for reporting purposes (cheap enough).
        # This does NOT affect integration.
        t_report = t0 + p.dt
        drv_r = drive_signal(t_report, p)
        F = np.zeros_like(pos)
        F_b = np.zeros_like(bub_pos)

        disp = pos - rest
        for a, b in neigh:
            du = disp[b] - disp[a]
            dv = vel[b] - vel[a]
            # --- ANISO (PHYS+TENSOR): choose stiffness/damping by bond direction ---
            r0_ab = rest[b] - rest[a]  # bond rest-direction
            n0 = float(np.linalg.norm(r0_ab))
            if n0 < 1e-30:
                e0 = np.array([1.0, 0.0, 0.0], dtype=float)
            else:
                e0 = (r0_ab / n0).astype(float)

            # stiffness
            if K_mat is not None and p.tensor_mode == "full":
                f_k = (K_mat @ du).astype(float)
            else:
                if K_mat is not None:
                    k_use = float(e0 @ K_mat @ e0)
                else:
                    ax = int(np.argmax(np.abs(r0_ab)))
                    if ax == 0:
                        k_use = p.k_out_x
                    elif ax == 1:
                        k_use = p.k_out_y
                    else:
                        k_use = p.k_out_z
                f_k = k_use * du

            # damping
            if C_mat is not None and p.tensor_mode == "full":
                f_c = (C_mat @ dv).astype(float)
            else:
                if C_mat is not None:
                    c_use = float(e0 @ C_mat @ e0)
                else:
                    ax = int(np.argmax(np.abs(r0_ab)))
                    if ax == 0:
                        c_use = p.c_out_x
                    elif ax == 1:
                        c_use = p.c_out_y
                    else:
                        c_use = p.c_out_z
                f_c = c_use * dv

            f_ab = f_k + f_c
            F[a] += f_ab
            F[b] -= f_ab
        if p.pin_edges:
            u = pos[is_edge] - rest[is_edge]
            F[is_edge] += -p.k_pin * u - p.c_pin * vel[is_edge]
        if p.gamma_cube != 0.0:
            F += -float(p.gamma_cube) * vel
        rel = bub_pos - pos
        rel_v = bub_vel - vel
        d = np.linalg.norm(rel, axis=1)
        n_hat = rel / np.maximum(d[:, None], eps)
        mag = Ttot * np.tanh(d / eps)
        Fbub = -mag[:, None] * n_hat - p.c_rel * rel_v
        F_b += Fbub
        F += -Fbub
        if p.gamma_bubble != 0.0:
            F_b += -float(p.gamma_bubble) * bub_vel
        if p.drive_pattern == "point":
            ax = {"x": 0, "y": 1, "z": 2}[p.drive_axis]
            F[sidx, ax] += drv_r
        else:
            F += drv_r * w_drive

        acc = F / max(p.m_cube, 1e-30)
        acc_b = F_b / max(p.m_bubble, 1e-30)

        cube_x[n], cube_y[n], cube_z[n] = pos[sidx]
        cube_vx[n], cube_vy[n], cube_vz[n] = vel[sidx]
        cube_ax[n], cube_ay[n], cube_az[n] = acc[sidx]

        bub_x[n], bub_y[n], bub_z[n] = bub_pos[sidx]
        bub_vx[n], bub_vy[n], bub_vz[n] = bub_vel[sidx]
        bub_ax[n], bub_ay[n], bub_az[n] = acc_b[sidx]

        cm = compute_cm(pos, bub_pos, p.m_cube, p.m_bubble)
        qxx, qyy, qzz, qxy, qxz, qyz = reduced_quadrupole_components(pos, bub_pos, p.m_cube, p.m_bubble, cm=cm)
        Q_xx[n], Q_yy[n], Q_zz[n] = qxx, qyy, qzz
        Q_xy[n], Q_xz[n], Q_yz[n] = qxy, qxz, qyz
        if maskA is not None:
            qxxA, qyyA, qzzA, qxyA, qxzA, qyzA = reduced_quadrupole_components(pos[maskA], bub_pos[maskA], p.m_cube, p.m_bubble, cm=cm)
            qxxB, qyyB, qzzB, qxyB, qxzB, qyzB = reduced_quadrupole_components(pos[maskB], bub_pos[maskB], p.m_cube, p.m_bubble, cm=cm)
            Q_xx_A[n], Q_yy_A[n], Q_zz_A[n] = qxxA, qyyA, qzzA
            Q_xy_A[n], Q_xz_A[n], Q_yz_A[n] = qxyA, qxzA, qyzA
            Q_xx_B[n], Q_yy_B[n], Q_zz_B[n] = qxxB, qyyB, qzzB
            Q_xy_B[n], Q_xz_B[n], Q_yz_B[n] = qxyB, qxzB, qyzB


        if (not warned_scale) and (np.max(np.abs(pos - rest)) > 1e3):
            warned_scale = True
            print("[WARN] Large displacements detected (>1e3). Reduce drive_amp and/or increase gamma_cube/substeps.")

    Qdd_xx = finite_diff_second(Q_xx, p.dt)
    Qdd_yy = finite_diff_second(Q_yy, p.dt)
    Qdd_zz = finite_diff_second(Q_zz, p.dt)
    Qdd_xy = finite_diff_second(Q_xy, p.dt)
    Qdd_xz = finite_diff_second(Q_xz, p.dt)
    Qdd_yz = finite_diff_second(Q_yz, p.dt)
    h_plus = Qdd_xx - Qdd_yy
    h_cross = 2.0 * Qdd_xy

    # Split readout channels (A/B halves) + differential AB (only meaningful if maskA is set)
    h_plus_A = np.zeros_like(h_plus)
    h_cross_A = np.zeros_like(h_cross)
    h_plus_B = np.zeros_like(h_plus)
    h_cross_B = np.zeros_like(h_cross)
    h_plus_AB = np.zeros_like(h_plus)
    h_cross_AB = np.zeros_like(h_cross)

    if maskA is not None:
        Qdd_xx_A = finite_diff_second(Q_xx_A, p.dt)
        Qdd_yy_A = finite_diff_second(Q_yy_A, p.dt)
        Qdd_xy_A = finite_diff_second(Q_xy_A, p.dt)
        h_plus_A = Qdd_xx_A - Qdd_yy_A
        h_cross_A = 2.0 * Qdd_xy_A

        Qdd_xx_B = finite_diff_second(Q_xx_B, p.dt)
        Qdd_yy_B = finite_diff_second(Q_yy_B, p.dt)
        Qdd_xy_B = finite_diff_second(Q_xy_B, p.dt)
        h_plus_B = Qdd_xx_B - Qdd_yy_B
        h_cross_B = 2.0 * Qdd_xy_B

        h_plus_AB = h_plus_A - h_plus_B
        h_cross_AB = h_cross_A - h_cross_B


    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "t_s","drive",
        "cube_x","cube_y","cube_z","cube_vx","cube_vy","cube_vz","cube_ax","cube_ay","cube_az",
        "bubble_x","bubble_y","bubble_z","bubble_vx","bubble_vy","bubble_vz","bubble_ax","bubble_ay","bubble_az",
        "Q_xx","Q_yy","Q_zz","Q_xy","Q_xz","Q_yz",
        "Qddot_xx","Qddot_yy","Qddot_zz","Qddot_xy","Qddot_xz","Qddot_yz",
        "h_plus_proxy","h_cross_proxy",
        "h_plus_A","h_cross_A","h_plus_B","h_cross_B","h_plus_AB","h_cross_AB",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for n in range(steps):
            w.writerow({
                "t_s": float(t_arr[n]),
                "drive": float(drive_arr[n]),
                "cube_x": float(cube_x[n]), "cube_y": float(cube_y[n]), "cube_z": float(cube_z[n]),
                "cube_vx": float(cube_vx[n]), "cube_vy": float(cube_vy[n]), "cube_vz": float(cube_vz[n]),
                "cube_ax": float(cube_ax[n]), "cube_ay": float(cube_ay[n]), "cube_az": float(cube_az[n]),
                "bubble_x": float(bub_x[n]), "bubble_y": float(bub_y[n]), "bubble_z": float(bub_z[n]),
                "bubble_vx": float(bub_vx[n]), "bubble_vy": float(bub_vy[n]), "bubble_vz": float(bub_vz[n]),
                "bubble_ax": float(bub_ax[n]), "bubble_ay": float(bub_ay[n]), "bubble_az": float(bub_az[n]),
                "Q_xx": float(Q_xx[n]), "Q_yy": float(Q_yy[n]), "Q_zz": float(Q_zz[n]),
                "Q_xy": float(Q_xy[n]), "Q_xz": float(Q_xz[n]), "Q_yz": float(Q_yz[n]),
                "Qddot_xx": float(Qdd_xx[n]), "Qddot_yy": float(Qdd_yy[n]), "Qddot_zz": float(Qdd_zz[n]),
                "Qddot_xy": float(Qdd_xy[n]), "Qddot_xz": float(Qdd_xz[n]), "Qddot_yz": float(Qdd_yz[n]),
                "h_plus_proxy": float(h_plus[n]),
                "h_cross_proxy": float(h_cross[n]),
                "h_plus_A": float(h_plus_A[n]),
                "h_cross_A": float(h_cross_A[n]),
                "h_plus_B": float(h_plus_B[n]),
                "h_cross_B": float(h_cross_B[n]),
                "h_plus_AB": float(h_plus_AB[n]),
                "h_cross_AB": float(h_cross_AB[n]),
            })

    if plot_png is not None and plt is not None:
        plot_png.parent.mkdir(parents=True, exist_ok=True)
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(t_arr, drive_arr, label="drive")
        ax.plot(t_arr, h_plus / (np.max(np.abs(h_plus)) + 1e-30), label="h_plus_proxy (norm)")
        ax.plot(t_arr, h_cross / (np.max(np.abs(h_cross)) + 1e-30), label="h_cross_proxy (norm)")
        ax.set_xlabel("t [s]")
        ax.legend()
        fig.tight_layout()
        fig.savefig(str(plot_png), dpi=150)
        plt.close(fig)

    print(f"[OK] Wrote {out_csv}")
    if plot_png is not None:
        print(f"[OK] Wrote {plot_png}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_csv", required=True, type=str)
    ap.add_argument("--plot_png", default=None, type=str)

    ap.add_argument("--nx", type=int, default=6)
    ap.add_argument("--ny", type=int, default=6)
    ap.add_argument("--nz", type=int, default=6)
    ap.add_argument("--spacing", type=float, default=1.0)

    ap.add_argument("--dt", type=float, default=1/4096)
    ap.add_argument("--duration", type=float, default=0.30)
    ap.add_argument("--substeps", type=int, default=4)

    ap.add_argument("--m_cube", type=float, default=0.05)
    ap.add_argument("--k_out", type=float, default=5e4)
    
    ap.add_argument("--k_out_x", type=float, default=None,
                    help="Outer neighbor stiffness for x-bonds (defaults to --k_out)")
    ap.add_argument("--k_out_y", type=float, default=None,
                    help="Outer neighbor stiffness for y-bonds (defaults to --k_out)")

    ap.add_argument("--k_out_z", type=float, default=None,
                    help="Outer neighbor stiffness for z-bonds (defaults to --k_out)")
    ap.add_argument("--c_out", type=float, default=40.0)

    ap.add_argument("--c_out_x", type=float, default=None,
                    help="Outer neighbor damping for x-bonds (defaults to --c_out)")
    ap.add_argument("--c_out_y", type=float, default=None,
                    help="Outer neighbor damping for y-bonds (defaults to --c_out)")
    ap.add_argument("--c_out_z", type=float, default=None,
                    help="Outer neighbor damping for z-bonds (defaults to --c_out)")
    ap.add_argument("--k_diag", type=str, default=None,
                    help="Optional tensor stiffness principal values 'k1,k2,k3'. If set: k_use = e0^T K e0.")
    ap.add_argument("--c_diag", type=str, default=None,
                    help="Optional tensor damping principal values 'c1,c2,c3'. If set: c_use = e0^T C e0.")
    ap.add_argument("--k_rot_deg", type=str, default="0,0,0",
                    help="Yaw,Pitch,Roll degrees (ZYX order) for stiffness tensor rotation.")
    ap.add_argument("--c_rot_deg", type=str, default="0,0,0",
                    help="Yaw,Pitch,Roll degrees (ZYX order) for damping tensor rotation.")
    ap.add_argument("--gyro_omega", type=str, default="0,0,0",
                    help="Optional gyro omega vector (rad/s) 'wx,wy,wz' for F += gyro_gain*m*(omega×v).")
    ap.add_argument("--gyro_gain", type=float, default=0.0,
                    help="Scale for gyro term (0 disables).")
    ap.add_argument("--tensor_mode", choices=["projected","full"], default="projected",
                    help="When k_diag/c_diag are set: projected uses k_use=e0^TKe0; full uses vector force f=K@du (mixing).")
    ap.add_argument("--readout_split", choices=["none","x","y"], default="none",
                    help="Optional readout split: compute readout on two halves (A/B) along x or y and output extra channels (h_plus_A/B, h_cross_A/B, h_plus_AB, h_cross_AB).")

    ap.add_argument("--gamma_cube", type=float, default=5.0)

    ap.add_argument("--pin_edges", action="store_true", default=True)
    ap.add_argument("--no_pin_edges", action="store_true", help="Disable edge pinning")
    ap.add_argument("--k_pin", type=float, default=2e5)
    ap.add_argument("--c_pin", type=float, default=200.0)

    ap.add_argument("--m_bubble", type=float, default=0.005)
    ap.add_argument("--T0", type=float, default=1336.0)
    ap.add_argument("--n_threads", type=int, default=8)
    ap.add_argument("--c_rel", type=float, default=50.0)
    ap.add_argument("--gamma_bubble", type=float, default=0.0)
    ap.add_argument("--bubble_offset", type=float, default=0.05, help="Initial bubble z-offset")
    ap.add_argument("--ct_soft_eps", type=float, default=0.05, help="Softening length eps for tanh(d/eps)")
    ap.add_argument("--target_inner_f_hz", type=float, default=None,
                    help="If set, compute T0 (per-thread) to target this inner frequency (CT-consistent).")

    ap.add_argument("--drive_type", type=str, default="impulse", choices=["none", "sine", "chirp", "impulse"])
    ap.add_argument("--drive_amp", type=float, default=1.0)
    ap.add_argument("--drive_f0_hz", type=float, default=35.0)
    ap.add_argument("--drive_f1_hz", type=float, default=250.0)
    ap.add_argument("--drive_t1", type=float, default=0.006)
    ap.add_argument("--drive_env", type=str, default="end", choices=["flat", "start", "end"])
    ap.add_argument("--drive_env_pow", type=float, default=1.0)

    ap.add_argument("--drive_pattern", type=str, default="quad_plus_xy",
                    choices=["point", "quad_plus_xy", "quad_cross_xy"])
    ap.add_argument("--drive_weight_norm", type=str, default="l2",
                    choices=["l2", "max", "none", "rms"])
    ap.add_argument("--drive_idx", type=int, default=0)
    ap.add_argument("--drive_axis", type=str, default="z", choices=["x", "y", "z"])

    ap.add_argument("--abort_on_nan", action="store_true", default=True)

    args = ap.parse_args()
    if args.no_pin_edges:
        args.pin_edges = False

    # CT-consistent T0AUTO: T0 = m (2πf)^2 eps / n_threads
    if args.target_inner_f_hz is not None:
        f = float(args.target_inner_f_hz)
        eps = float(max(args.ct_soft_eps, 1e-12))
        args.T0 = float(args.m_bubble * (2.0 * math.pi * f) ** 2 * eps / max(args.n_threads, 1))

    if args.bubble_offset > 3.0 * float(max(args.ct_soft_eps, 1e-12)):
        print("[WARN] bubble_offset is much larger than ct_soft_eps; CT force may start saturated. "
              "Consider bubble_offset<=ct_soft_eps.")

    p = SimParams(
        nx=args.nx, ny=args.ny, nz=args.nz, spacing=args.spacing,
        dt=args.dt, duration=args.duration, substeps=args.substeps,
        m_cube=args.m_cube, k_out=args.k_out,
        k_out_x=(args.k_out_x if args.k_out_x is not None else args.k_out),
        k_out_y=(args.k_out_y if args.k_out_y is not None else args.k_out),
        k_out_z=(args.k_out_z if args.k_out_z is not None else args.k_out),
        c_out=args.c_out,
        c_out_x=(args.c_out_x if args.c_out_x is not None else args.c_out),
        c_out_y=(args.c_out_y if args.c_out_y is not None else args.c_out),
        c_out_z=(args.c_out_z if args.c_out_z is not None else args.c_out),
        gamma_cube=args.gamma_cube,
        pin_edges=bool(args.pin_edges), k_pin=args.k_pin, c_pin=args.c_pin,
        m_bubble=args.m_bubble, T0=args.T0, n_threads=args.n_threads,
        c_rel=args.c_rel, gamma_bubble=args.gamma_bubble,
        bubble_offset=args.bubble_offset, ct_soft_eps=args.ct_soft_eps,
        drive_type=args.drive_type, drive_amp=args.drive_amp,
        drive_f0_hz=args.drive_f0_hz, drive_f1_hz=args.drive_f1_hz,
        drive_t1=args.drive_t1, drive_env=args.drive_env, drive_env_pow=args.drive_env_pow,
        drive_pattern=args.drive_pattern, drive_weight_norm=args.drive_weight_norm,
        drive_idx=args.drive_idx, drive_axis=args.drive_axis,
        k_diag=_parse_triplet(args.k_diag) if args.k_diag else None,
        c_diag=_parse_triplet(args.c_diag) if args.c_diag else None,
        k_rot_deg=_parse_triplet(args.k_rot_deg),
        c_rot_deg=_parse_triplet(args.c_rot_deg),
        gyro_omega=_parse_triplet(args.gyro_omega),
        gyro_gain=float(args.gyro_gain),
        tensor_mode=str(args.tensor_mode),
        readout_split=str(args.readout_split),
        abort_on_nan=bool(args.abort_on_nan),
    )

    simulate(p, Path(args.out_csv), Path(args.plot_png) if args.plot_png else None)


if __name__ == "__main__":
    main()
