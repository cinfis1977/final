import math
import numpy as np

from mastereq.unified_gksl import UnifiedGKSL

from mastereq.microphysics import (
    gamma_km_inv_from_n_sigma_v,
    sigma_weak_nue_e_cm2,
    sigma_em_magnetic_moment_cm2,
    sigma_dm_reference_cm2,
    sigma_gravity_reference_cm2,
    electron_density_from_rho_ye,
)

from mastereq.weak_sector import make_weak_damping_fn
from mastereq.ms_sector import make_msw_damping_fn
from mastereq.em_sector import make_em_damping_from_radiation
from mastereq.dm_sector import make_dm_scattering_damping
from mastereq.ligo_sector import make_ligo_damping


def _rho_with_damping(damping_fn, *, dm2: float, theta: float, L_km: float, E_GeV: float, steps: int) -> np.ndarray:
    ug = UnifiedGKSL(dm2, theta)
    ug.add_damping(damping_fn)
    return ug.integrate(L_km, E_GeV, steps=steps)


def test_microphysics_use_microphysics_matches_explicit_gamma_across_sectors():
    """Proves the microphysics-derived gamma path is actually wired into GKSL evolution.

    For each sector damping builder that supports `use_microphysics=True`, we check that:
    - deriving gamma internally via microphysics yields the same evolution as
      providing the same gamma explicitly.
    """

    dm2 = 2.5e-3
    theta = math.radians(45.0)
    L_km = 295.0
    E_GeV = 1.0
    steps = 320
    v_cm_s = 3.0e10

    # --- Weak sector (simple dephasing) ---
    n_cm3 = 1.0e23
    gamma_weak = gamma_km_inv_from_n_sigma_v(n_cm3, sigma_weak_nue_e_cm2(E_GeV), v_cm_s)

    rho_micro = _rho_with_damping(
        make_weak_damping_fn(use_microphysics=True, n_cm3=n_cm3, E_GeV_ref=E_GeV, v_cm_s=v_cm_s),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    rho_explicit = _rho_with_damping(
        make_weak_damping_fn(gamma=gamma_weak, use_microphysics=False),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    assert np.allclose(rho_micro, rho_explicit, atol=5e-13, rtol=0.0)

    # --- MSW sector (explicit GKSL sigma_z dephasing) ---
    rho_gcm3 = 3.0
    Ye = 0.5
    n_e = electron_density_from_rho_ye(rho_gcm3, Ye)
    gamma_msw = gamma_km_inv_from_n_sigma_v(n_e, sigma_weak_nue_e_cm2(E_GeV), v_cm_s)

    rho_micro = _rho_with_damping(
        make_msw_damping_fn(use_microphysics=True, rho_gcm3=rho_gcm3, Ye=Ye, E_GeV_ref=E_GeV, v_cm_s=v_cm_s),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    rho_explicit = _rho_with_damping(
        make_msw_damping_fn(gamma=gamma_msw, use_microphysics=False),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    assert np.allclose(rho_micro, rho_explicit, atol=5e-13, rtol=0.0)

    # --- EM sector (dephasing with magnetic-moment template) ---
    mu_nu_muB = 1.0e-11
    n_cm3_em = 1.0e23
    gamma_em = gamma_km_inv_from_n_sigma_v(n_cm3_em, sigma_em_magnetic_moment_cm2(mu_nu_muB, E_GeV), v_cm_s)

    rho_micro = _rho_with_damping(
        make_em_damping_from_radiation(use_microphysics=True, mu_nu_muB=mu_nu_muB, n_cm3=n_cm3_em, E_GeV_ref=E_GeV, v_cm_s=v_cm_s),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    rho_explicit = _rho_with_damping(
        make_em_damping_from_radiation(gamma=gamma_em, use_microphysics=False),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    assert np.allclose(rho_micro, rho_explicit, atol=5e-13, rtol=0.0)

    # --- DM sector (population relaxation with template sigma) ---
    n_cm3_dm = 1.0e22
    coupling_g = 1.0e-6
    gamma_dm = gamma_km_inv_from_n_sigma_v(n_cm3_dm, sigma_dm_reference_cm2(E_GeV, coupling_g), v_cm_s)

    rho_micro = _rho_with_damping(
        make_dm_scattering_damping(use_microphysics=True, n_cm3=n_cm3_dm, E_GeV_ref=E_GeV, coupling_g=coupling_g, v_cm_s=v_cm_s),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    rho_explicit = _rho_with_damping(
        make_dm_scattering_damping(gamma_s=gamma_dm, use_microphysics=False),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    assert np.allclose(rho_micro, rho_explicit, atol=5e-13, rtol=0.0)

    # --- LIGO sector (pair Lindblad operators, equilibrium=0.5) ---
    n_cm3_g = 1.0e20
    coupling_h = 1.0
    gamma_g = gamma_km_inv_from_n_sigma_v(n_cm3_g, sigma_gravity_reference_cm2(E_GeV, coupling_h), v_cm_s)

    rho_micro = _rho_with_damping(
        make_ligo_damping(use_microphysics=True, n_cm3=n_cm3_g, E_GeV_ref=E_GeV, coupling_h=coupling_h, v_cm_s=v_cm_s, mode="lindblad", equilibrium=0.5),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    rho_explicit = _rho_with_damping(
        make_ligo_damping(gamma_g=gamma_g, use_microphysics=False, mode="lindblad", equilibrium=0.5),
        dm2=dm2,
        theta=theta,
        L_km=L_km,
        E_GeV=E_GeV,
        steps=steps,
    )
    assert np.allclose(rho_micro, rho_explicit, atol=5e-13, rtol=0.0)
