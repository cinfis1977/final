"""Global default constants and microphysical helper utilities.

These defaults are placeholders chosen to be numerically stable and consistent
across all sectors. They are NOT model-accurate unless you tie them to a
specific medium and interaction model. Replace as needed.
"""
from __future__ import annotations

# Universal speed of light in km/s
C_KM_S = 2.99792458e5

# Fixed default dissipator rate (1/km) used when a sector does not specify
# a microphysical rate. Keep small to avoid stiff dynamics in the RK4 solver.
DEFAULT_GAMMA_KM_INV = 1.0e-6

# Nominal placeholders for deriving gamma from density and cross-section
# (values are demonstrative only).
DEFAULT_N_CM3 = 1.0e23   # number density in cm^-3
DEFAULT_SIGMA_CM2 = 1.0e-44  # weak-scale cross-section in cm^2
DEFAULT_V_CM_S = 3.0e10  # ~c in cm/s


def gamma_from_n_sigma_v(n_cm3: float = DEFAULT_N_CM3,
                         sigma_cm2: float = DEFAULT_SIGMA_CM2,
                         v_cm_s: float = DEFAULT_V_CM_S) -> float:
    """Compute a GKSL rate gamma [1/km] from n, sigma, v.

    Uses the collision-rate estimate Gamma = n * sigma * v (1/s), then converts
    to per-length using gamma = Gamma / c (1/km) with c in km/s.
    """
    Gamma_s_inv = float(n_cm3) * float(sigma_cm2) * float(v_cm_s)
    return Gamma_s_inv / C_KM_S


__all__ = [
    "C_KM_S",
    "DEFAULT_GAMMA_KM_INV",
    "DEFAULT_N_CM3",
    "DEFAULT_SIGMA_CM2",
    "DEFAULT_V_CM_S",
    "gamma_from_n_sigma_v",
]
