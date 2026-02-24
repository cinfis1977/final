import math
import numpy as np

from mastereq.microphysics import (
    gamma_km_inv_from_n_sigma_v,
    electron_density_from_rho_ye,
    sigma_weak_nue_e_cm2,
)
from mastereq.unified_gksl import UnifiedGKSL
from mastereq.weak_sector import make_weak_damping_fn


def test_gamma_conversion_positive():
    g = gamma_km_inv_from_n_sigma_v(1.0e23, 1.0e-44, 3.0e10)
    assert g > 0.0


def test_electron_density_from_rho_ye_positive():
    ne = electron_density_from_rho_ye(3.0, 0.5)
    assert ne > 0.0


def test_microphysics_weak_damping_integration_stable():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    # derive gamma via microphysics switch from n*sigma*v
    sigma = sigma_weak_nue_e_cm2(E)
    ug.add_damping(make_weak_damping_fn(use_microphysics=True, n_cm3=1.0e23, E_GeV_ref=E, v_cm_s=3.0e10))

    rho = ug.integrate(L, E, steps=300)
    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 1e-8
    assert np.allclose(rho, rho.conj().T, atol=1e-10)
    eigs = np.linalg.eigvalsh(rho)
    assert np.all(eigs >= -1e-8)


if __name__ == "__main__":
    test_gamma_conversion_positive()
    test_electron_density_from_rho_ye_positive()
    test_microphysics_weak_damping_integration_stable()
    print("Microphysics scaffold tests passed")
