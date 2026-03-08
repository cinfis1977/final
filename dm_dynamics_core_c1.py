from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Optional, TypeAlias

import numpy as np


OrderMode = Literal["forward", "reverse", "shuffle"]

State: TypeAlias = tuple[float, float, float, float, float, float]
Deriv: TypeAlias = tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class DMDynamicsC1Params:
    # DM amplitude-level knob
    A_dm: float = 0.05

    # Texture: 1 + C*sin(theta + w_r*r)
    texture_C: float = 0.25
    texture_wr: float = 0.35

    # Radial envelope: 1/(1 + (r/r0)^p)
    env_r0: float = 2.0
    env_p: float = 2.0

    # Gate coupling and epsilon suppression
    eps_decay: float = 0.5

    # Circularization relaxation (keeps v near v_circ)
    k_circ: float = 0.8

    # omega damping + driving
    k_omega: float = 0.25
    drive_strength: float = 0.4

    # epsilon dynamics
    k_eps: float = 0.15
    gamma_eps: float = 0.2

    # gate dynamics
    k_g: float = 0.8
    S0: float = 1.0
    eps_w: float = 0.6
    m_w: float = 0.8


def _sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    # Numerically stable logistic to avoid overflow for large |x|.
    xa = np.asarray(x, dtype=float)
    out = np.empty_like(xa, dtype=float)

    pos = xa >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-xa[pos]))

    expx = np.exp(xa[~pos])
    out[~pos] = expx / (1.0 + expx)

    if np.isscalar(x):
        return float(out)
    return out


def _clamp01(x: np.ndarray | float) -> np.ndarray | float:
    return np.minimum(1.0, np.maximum(0.0, x))


def _clamp_nonneg(x: np.ndarray | float) -> np.ndarray | float:
    return np.maximum(0.0, x)


def dm_accel(
    r: float,
    *,
    theta: float,
    g: float,
    epsilon: float,
    p: DMDynamicsC1Params,
) -> float:
    """Amplitude-level DM acceleration a_dm(r; X)."""
    if not np.isfinite(r):
        return float("nan")

    # Gate / coherence
    gate = float(_clamp01(g)) * float(np.exp(-p.eps_decay * float(_clamp_nonneg(epsilon))))

    # Texture
    texture = 1.0 + p.texture_C * float(np.sin(theta + p.texture_wr * r))

    # Envelope
    if p.env_r0 <= 0:
        envelope = 1.0
    else:
        envelope = 1.0 / (1.0 + (max(r, 0.0) / p.env_r0) ** p.env_p)

    return float(p.A_dm * gate * texture * envelope)


def _interp1(x: float, xp: np.ndarray, fp: np.ndarray) -> float:
    # np.interp requires increasing xp
    return float(np.interp(x, xp, fp, left=fp[0], right=fp[-1]))


def simulate_profile(
    *,
    n_steps: int,
    dt: float,
    r0: float,
    v0: float,
    theta0: float,
    omega0: float,
    epsilon0: float,
    g0: float,
    a_bary_fn: Callable[[float], float],
    v_target_fn: Optional[Callable[[float], float]] = None,
    sigma_v_fn: Optional[Callable[[float], float]] = None,
    params: DMDynamicsC1Params,
    order_mode: OrderMode = "forward",
    shuffle_seed: int = 0,
    enforce_circular_velocity: bool = True,
) -> dict[str, np.ndarray]:
    """Simulate DM-C1 internal state and derived observable.

    Returns arrays for r, v_state, v_pred, a_bary, a_dm, a_tot, theta, omega, epsilon, g, mismatch.
    """
    if n_steps <= 1:
        raise ValueError("n_steps must be > 1")
    if dt <= 0:
        raise ValueError("dt must be > 0")

    r = float(r0)
    v = float(v0)
    theta = float(theta0)
    omega = float(omega0)
    epsilon = float(epsilon0)
    g = float(g0)

    # Precompute drive signs for shuffle mode.
    if order_mode == "shuffle":
        rng = np.random.default_rng(int(shuffle_seed))
        drive = rng.choice([-1.0, 1.0], size=int(n_steps), replace=True).astype(float)
    elif order_mode == "reverse":
        drive = -np.ones(int(n_steps), dtype=float)
    else:
        drive = np.ones(int(n_steps), dtype=float)

    out_r = np.zeros(int(n_steps), dtype=float)
    out_v_state = np.zeros(int(n_steps), dtype=float)
    out_theta = np.zeros(int(n_steps), dtype=float)
    out_omega = np.zeros(int(n_steps), dtype=float)
    out_eps = np.zeros(int(n_steps), dtype=float)
    out_g = np.zeros(int(n_steps), dtype=float)
    out_a_bary = np.zeros(int(n_steps), dtype=float)
    out_a_dm = np.zeros(int(n_steps), dtype=float)
    out_a_tot = np.zeros(int(n_steps), dtype=float)
    out_v_pred = np.zeros(int(n_steps), dtype=float)
    out_mismatch = np.zeros(int(n_steps), dtype=float)

    def mismatch_of_state(r_s: float, theta_s: float, g_s: float, eps_s: float) -> float:
        if v_target_fn is None or sigma_v_fn is None:
            return 0.0
        a_b = float(a_bary_fn(float(r_s)))
        a_d = dm_accel(float(r_s), theta=float(theta_s), g=float(g_s), epsilon=float(eps_s), p=params)
        a_t = a_b + a_d
        v_pred_s = float(np.sqrt(max(float(r_s) * float(a_t), 0.0)))
        v_t = float(v_target_fn(float(r_s)))
        sig = float(sigma_v_fn(float(r_s)))
        sig = max(sig, 1e-12)
        return float(((v_pred_s - v_t) / sig) ** 2)

    def rhs(step_i: int, state: State) -> Deriv:
        r_s, v_s, theta_s, omega_s, eps_s, g_s = state

        a_b = float(a_bary_fn(float(r_s)))
        a_d = dm_accel(float(r_s), theta=float(theta_s), g=float(g_s), epsilon=float(eps_s), p=params)
        a_t = a_b + a_d

        v_circ = float(np.sqrt(max(float(r_s) * float(a_t), 0.0)))
        mismatch = mismatch_of_state(float(r_s), float(theta_s), float(g_s), float(eps_s))

        dr = float(v_s)
        dv = float(a_t - params.k_circ * (float(v_s) - v_circ))
        dtheta = float(omega_s)
        domega = float(-params.k_omega * float(omega_s) + params.drive_strength * float(drive[int(step_i)]))

        deps = float(params.k_eps * mismatch - params.gamma_eps * float(eps_s))
        g_target = float(_sigmoid(params.S0 - params.eps_w * float(eps_s) - params.m_w * mismatch))
        dg = float(params.k_g * (g_target - float(g_s)))

        return dr, dv, dtheta, domega, deps, dg

    def project_state(state: State) -> State:
        r_s, v_s, theta_s, omega_s, eps_s, g_s = state
        g_s = float(_clamp01(float(g_s)))
        eps_s = float(_clamp_nonneg(float(eps_s)))
        return float(r_s), float(v_s), float(theta_s), float(omega_s), float(eps_s), float(g_s)

    def add_scaled(s: State, k: Deriv, scale: float) -> State:
        return (
            float(s[0] + scale * k[0]),
            float(s[1] + scale * k[1]),
            float(s[2] + scale * k[2]),
            float(s[3] + scale * k[3]),
            float(s[4] + scale * k[4]),
            float(s[5] + scale * k[5]),
        )

    def rk4_step(step_i: int, s0: State) -> State:
        k1 = rhs(step_i, s0)
        k2 = rhs(step_i, project_state(add_scaled(s0, k1, 0.5 * dt)))
        k3 = rhs(step_i, project_state(add_scaled(s0, k2, 0.5 * dt)))
        k4 = rhs(step_i, project_state(add_scaled(s0, k3, 1.0 * dt)))

        return (
            float(s0[0] + (dt / 6.0) * (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0])),
            float(s0[1] + (dt / 6.0) * (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1])),
            float(s0[2] + (dt / 6.0) * (k1[2] + 2.0 * k2[2] + 2.0 * k3[2] + k4[2])),
            float(s0[3] + (dt / 6.0) * (k1[3] + 2.0 * k2[3] + 2.0 * k3[3] + k4[3])),
            float(s0[4] + (dt / 6.0) * (k1[4] + 2.0 * k2[4] + 2.0 * k3[4] + k4[4])),
            float(s0[5] + (dt / 6.0) * (k1[5] + 2.0 * k2[5] + 2.0 * k3[5] + k4[5])),
        )

    for i in range(int(n_steps)):
        # record
        out_r[i] = r
        out_v_state[i] = v
        out_theta[i] = theta
        out_omega[i] = omega
        out_eps[i] = epsilon
        out_g[i] = g

        a_b = float(a_bary_fn(float(r)))
        a_d = dm_accel(float(r), theta=float(theta), g=float(g), epsilon=float(epsilon), p=params)
        a_t = a_b + a_d
        v_pred = float(np.sqrt(max(float(r) * float(a_t), 0.0)))
        out_a_bary[i] = a_b
        out_a_dm[i] = a_d
        out_a_tot[i] = a_t
        out_v_pred[i] = v_pred
        out_mismatch[i] = mismatch_of_state(float(r), float(theta), float(g), float(epsilon))

        if i == int(n_steps) - 1:
            break

        # RK4 step
        s0: State = (r, v, theta, omega, epsilon, g)
        r, v, theta, omega, epsilon, g = project_state(rk4_step(i, s0))

        if enforce_circular_velocity:
            a_b = float(a_bary_fn(float(r)))
            a_d = dm_accel(float(r), theta=float(theta), g=float(g), epsilon=float(epsilon), p=params)
            a_t = a_b + a_d
            v = float(np.sqrt(max(float(r) * float(a_t), 0.0)))

        if not (
            np.isfinite(r)
            and np.isfinite(v)
            and np.isfinite(theta)
            and np.isfinite(omega)
            and np.isfinite(epsilon)
            and np.isfinite(g)
        ):
            raise RuntimeError("Non-finite state encountered in DM-C1 dynamics")

    return {
        "r": out_r,
        "v_state": out_v_state,
        "v_pred": out_v_pred,
        "a_bary": out_a_bary,
        "a_dm": out_a_dm,
        "a_tot": out_a_tot,
        "theta": out_theta,
        "omega": out_omega,
        "epsilon": out_eps,
        "g": out_g,
        "mismatch": out_mismatch,
    }
