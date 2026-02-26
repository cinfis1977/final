"""Microphysical helper formulas used to derive GKSL rates.

These helpers provide simple, documented approximations that can be used
consistently across sectors. They are deterministic and numerically stable,
but still approximate unless replaced by model-specific calculations.
"""
from __future__ import annotations

from .defaults import C_KM_S

# Constants for medium conversions
N_A = 6.02214076e23  # Avogadro constant [1/mol]


def gamma_km_inv_from_n_sigma_v(n_cm3: float, sigma_cm2: float, v_cm_s: float) -> float:
    """Return gamma [1/km] from number density, cross section, and speed.

    Gamma[s^-1] = n[cm^-3] * sigma[cm^2] * v[cm/s]
    gamma[km^-1] = Gamma / c[km/s]
    """
    Gamma_s_inv = float(n_cm3) * float(sigma_cm2) * float(v_cm_s)
    return Gamma_s_inv / float(C_KM_S)


def electron_density_from_rho_ye(rho_gcm3: float, Ye: float) -> float:
    """Approximate electron density n_e [cm^-3] from mass density and Ye.

    Uses n_e ≈ rho[g/cm^3] * Ye * N_A (assuming ~1 g/mol per nucleon unit).
    """
    return float(rho_gcm3) * float(Ye) * float(N_A)


def sigma_weak_nue_e_cm2(E_GeV: float) -> float:
    """Approximate SM-like ν_e e cross section in cm^2 (linear in E).

    Rule-of-thumb: sigma(ν_e e) ~ 9.2e-45 * E[GeV] cm^2.
    """
    return 9.2e-45 * max(0.0, float(E_GeV))


def sigma_weak_numu_e_cm2(E_GeV: float) -> float:
    """Approximate SM-like ν_μ e cross section in cm^2 (linear in E).

    Rule-of-thumb: sigma(ν_μ e) ~ 1.57e-45 * E[GeV] cm^2.
    """
    return 1.57e-45 * max(0.0, float(E_GeV))


def sigma_em_magnetic_moment_cm2(mu_nu_muB: float, E_GeV: float) -> float:
    """Toy EM scattering cross section from neutrino magnetic moment.

    Placeholder scaling used for consistent defaults:
      sigma_em ~ 1e-45 * (mu_nu/1e-11 muB)^2 * E[GeV]  [cm^2]
    """
    x = float(mu_nu_muB) / 1.0e-11
    return 1.0e-45 * (x * x) * max(0.0, float(E_GeV))


def sigma_dm_reference_cm2(E_GeV: float, coupling_g: float = 1.0e-6) -> float:
    """Reference DM scattering cross section template in cm^2.

    Placeholder scaling:
      sigma_dm ~ 1e-46 * (g/1e-6)^2 * E[GeV]
    """
    x = float(coupling_g) / 1.0e-6
    return 1.0e-46 * (x * x) * max(0.0, float(E_GeV))


def sigma_gravity_reference_cm2(E_GeV: float, coupling_h: float = 1.0) -> float:
    """Reference gravity-sector effective cross section template in cm^2.

    Placeholder scaling for stochastic-bath style effective interactions:
      sigma_g ~ 1e-50 * h^2 * E[GeV]
    """
    h = float(coupling_h)
    return 1.0e-50 * (h * h) * max(0.0, float(E_GeV))


def sigma_entanglement_reference_cm2(E_GeV: float, visibility: float = 1.0) -> float:
        """Reference effective cross section for entanglement decoherence templates.

        Deterministic placeholder scaling used for GKSL wiring checks:
            sigma_ent ~ 1e-47 * visibility^2 * E[GeV]
        """
        v = float(visibility)
        return 1.0e-47 * (v * v) * max(0.0, float(E_GeV))


def sigma_photon_birefringence_reference_cm2(E_GeV: float, coupling_x: float = 1.0) -> float:
        """Reference effective cross section for photon/birefringence templates.

        Deterministic placeholder scaling used for GKSL wiring checks:
            sigma_ph ~ 1e-49 * coupling_x^2 * E[GeV]
        """
        x = float(coupling_x)
        return 1.0e-49 * (x * x) * max(0.0, float(E_GeV))


__all__ = [
    "N_A",
    "gamma_km_inv_from_n_sigma_v",
    "electron_density_from_rho_ye",
    "sigma_weak_nue_e_cm2",
    "sigma_weak_numu_e_cm2",
    "sigma_em_magnetic_moment_cm2",
    "sigma_dm_reference_cm2",
    "sigma_gravity_reference_cm2",
    "sigma_entanglement_reference_cm2",
    "sigma_photon_birefringence_reference_cm2",
]
