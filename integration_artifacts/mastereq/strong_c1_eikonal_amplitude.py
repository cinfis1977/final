r"""STRONG C1: amplitude-level internal state core (toy eikonal).

This module is intentionally *not* a PDG/COMPETE baseline reproduction.
It provides an explicit internal state (complex eikonal \chi(b, t)) that evolves
along energy-like time t = ln(s/s0), and computes observables from that state.

Observables from state
----------------------
Define the (impact-parameter) S-matrix and profile:
  S(b) = exp(i \chi(b))
  \Gamma(b) = 1 - S(b)

A forward amplitude proxy is constructed as:
  I(t) = 2\pi \int_0^\infty b db \Gamma(b,t)
  F(t) = i * I(t)

Then we expose:
  sigma_tot_mb(t) = sigma_norm_mb * Im F(t)
  rho(t)          = Re F(t) / Im F(t)

Unitarity / absorptivity sanity for this toy eikonal is enforced by requiring
Im \chi(b,t) >= 0, which ensures |S(b)| = exp(-Im \chi) <= 1.

Evolution law
-------------
Not QCD. A minimal, deterministic, stable evolution is used:
  d\chi_I/dt = -lambda_I * \chi_I + g_I(t) * exp(-b^2/(2 R(t)^2))
  d\chi_R/dt = -lambda_R * \chi_R + kappa_R * g_I(t) * exp(-b^2/(2 R(t)^2))

with R(t)^2 = R0^2 + v_R * (t - t0) and g_I(t) = g0 + g_slope*(t - t0), clipped >=0.

This is designed to:
  - evolve an internal state (no closed-form baseline injection)
  - keep Im \chi nonnegative (absorptive)
  - avoid numerical blowups

"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def t_from_sqrts(sqrts_GeV: np.ndarray, *, s0_GeV2: float) -> np.ndarray:
    """Compute t = ln(s/s0) with s = (sqrt(s))^2."""
    s = np.asarray(sqrts_GeV, dtype=float) ** 2
    s0 = float(s0_GeV2)
    if s0 <= 0:
        raise ValueError("s0_GeV2 must be > 0")
    return np.log(np.maximum(s / s0, 1e-300))


@dataclass(frozen=True)
class EikonalC1Params:
    """Parameter block for the toy C1 amplitude-core."""

    # energy/time reference
    s0_GeV2: float = 1.0

    # b-grid
    b_max: float = 12.0
    nb: int = 600

    # evolution grid control
    dt_max: float = 0.05

    # gaussian source + diffusion
    t0: float = 0.0
    R0: float = 2.0
    v_R: float = 0.30

    # source strength
    g0: float = 0.8
    g_slope: float = 0.08

    # GEO-in-evolution (C3 hook): modulates the source strength inside the evolution law.
    # This is intentionally simple: a bounded multiplicative modulation of g(t).
    # Setting geo_A=0.0 reproduces the C1 evolution exactly.
    geo_A: float = 0.0
    geo_template: str = "cos"  # cos|sin
    geo_phi0: float = 0.0
    geo_omega: float = 1.0  # phase accumulation rate in t

    # damping / relaxation
    lambda_I: float = 0.6
    lambda_R: float = 1.2

    # real-part coupling (generates rho != 0)
    kappa_R: float = 0.15

    # normalization to convert Im F into mb
    sigma_norm_mb: float = 0.45

    # safety clamps
    chiI_floor: float = 0.0
    chiI_cap: float = 40.0


@dataclass
class EikonalC1State:
    """Internal state for the STRONG C1 amplitude core."""

    t: float
    b: np.ndarray
    chi_R: np.ndarray
    chi_I: np.ndarray

    @staticmethod
    def initialize(pars: EikonalC1Params, *, t0: float | None = None) -> "EikonalC1State":
        t_init = float(pars.t0 if t0 is None else t0)
        b = np.linspace(0.0, float(pars.b_max), int(pars.nb), dtype=float)
        chi_R = np.zeros_like(b)
        chi_I = np.zeros_like(b)
        return EikonalC1State(t=t_init, b=b, chi_R=chi_R, chi_I=chi_I)

    def copy(self) -> "EikonalC1State":
        return EikonalC1State(t=float(self.t), b=self.b.copy(), chi_R=self.chi_R.copy(), chi_I=self.chi_I.copy())

    def _R_of_t(self, pars: EikonalC1Params, t: float) -> float:
        x = float(pars.R0) ** 2 + float(pars.v_R) * (float(t) - float(pars.t0))
        return math.sqrt(max(x, 1e-12))

    def _g_of_t(self, pars: EikonalC1Params, t: float) -> float:
        g = float(pars.g0) + float(pars.g_slope) * (float(t) - float(pars.t0))
        g = max(g, 0.0)

        A = float(getattr(pars, "geo_A", 0.0))
        if A != 0.0:
            phi = float(getattr(pars, "geo_phi0", 0.0)) + float(getattr(pars, "geo_omega", 1.0)) * (float(t) - float(pars.t0))
            tmpl = str(getattr(pars, "geo_template", "cos")).lower()
            u = math.cos(phi) if tmpl == "cos" else math.sin(phi)
            # bounded multiplicative modulation, clipped to keep g>=0
            g = g * max(0.0, 1.0 + A * u)

        return g

    def _source_profile(self, pars: EikonalC1Params, t: float) -> np.ndarray:
        R = self._R_of_t(pars, t)
        g = self._g_of_t(pars, t)
        # exp(-b^2/(2 R^2))
        return g * np.exp(-(self.b * self.b) / (2.0 * R * R))

    def advance_to(self, t_target: float, pars: EikonalC1Params) -> None:
        """Advance the internal state to t_target with stable substepping."""

        t0 = float(self.t)
        t1 = float(t_target)
        if t1 == t0:
            return

        dt_max = max(float(pars.dt_max), 1e-6)
        n = int(math.ceil(abs(t1 - t0) / dt_max))
        dt = (t1 - t0) / float(n)

        lamI = max(float(pars.lambda_I), 0.0)
        lamR = max(float(pars.lambda_R), 0.0)

        for k in range(n):
            t_mid = t0 + (k + 0.5) * dt
            src = self._source_profile(pars, t_mid)

            # Exponential integrator for linear damping + mid-point source.
            if lamI > 0:
                eI = math.exp(-lamI * dt)
                self.chi_I = self.chi_I * eI + (1.0 - eI) * (src / lamI)
            else:
                self.chi_I = self.chi_I + dt * src

            if lamR > 0:
                eR = math.exp(-lamR * dt)
                self.chi_R = self.chi_R * eR + (1.0 - eR) * (float(pars.kappa_R) * src / lamR)
            else:
                self.chi_R = self.chi_R + dt * float(pars.kappa_R) * src

            # enforce absorptivity
            self.chi_I = np.clip(self.chi_I, float(pars.chiI_floor), float(pars.chiI_cap))

        self.t = t1


def forward_amplitude_from_state(state: EikonalC1State) -> complex:
    """Compute forward amplitude proxy F(t) from the eikonal state."""

    chiR = np.asarray(state.chi_R, dtype=float)
    chiI = np.asarray(state.chi_I, dtype=float)

    # S = exp(i chi) = exp(-chiI) (cos chiR + i sin chiR)
    expm = np.exp(-chiI)
    S = expm * (np.cos(chiR) + 1j * np.sin(chiR))
    Gamma = 1.0 - S

    # I = 2pi ∫ b db Gamma(b)
    b = np.asarray(state.b, dtype=float)
    integrand = b * Gamma
    # np.trapezoid returns a scalar for 1D integrands, but keep typing strict.
    I = complex(2.0 * math.pi * np.trapezoid(integrand, b))

    # F = i * I
    return 1j * I


def sigma_tot_rho_from_state(state: EikonalC1State, pars: EikonalC1Params) -> tuple[float, float]:
    """Return (sigma_tot_mb, rho) from the current state."""

    F = forward_amplitude_from_state(state)
    im = float(np.imag(F))
    re = float(np.real(F))

    # sigma_tot >= 0 for physical absorptive configurations
    sigma = float(pars.sigma_norm_mb) * im

    im_safe = im if abs(im) > 1e-30 else (1e-30 if im >= 0 else -1e-30)
    rho = re / im_safe
    return sigma, rho


def profile_imag_from_state(state: EikonalC1State) -> np.ndarray:
    """Return Im Γ(b) profile, useful for unitarity/black-disk sanity checks."""

    chiR = np.asarray(state.chi_R, dtype=float)
    chiI = np.asarray(state.chi_I, dtype=float)
    expm = np.exp(-chiI)
    S = expm * (np.cos(chiR) + 1j * np.sin(chiR))
    Gamma = 1.0 - S
    return np.imag(Gamma)


__all__ = [
    "EikonalC1Params",
    "EikonalC1State",
    "t_from_sqrts",
    "forward_amplitude_from_state",
    "sigma_tot_rho_from_state",
    "profile_imag_from_state",
]