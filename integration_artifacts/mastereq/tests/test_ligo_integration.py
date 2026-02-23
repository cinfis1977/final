import math
import numpy as np
from mastereq.unified_gksl import UnifiedGKSL
from mastereq.ligo_sector import make_ligo_mass_modulation, make_ligo_damping


def test_ligo_modulation_and_damping_preserve_trace():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    ug.add_mass_sector(make_ligo_mass_modulation(amplitude_eV2=1e-6, omega_km_inv=0.01))
    ug.add_damping(make_ligo_damping(gamma_g=1e-6))

    rho = ug.integrate(L, E, steps=300)
    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 1e-8
    assert np.allclose(rho, rho.conj().T, atol=1e-10)
    eigs = np.linalg.eigvalsh(rho)
    assert np.all(eigs >= -1e-8)


def test_zero_ligo_reduces_to_vacuum():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    rho = ug.integrate(L, E, steps=400)
    P_gksl = float(np.real(rho[0, 0]))

    Delta = 1.267 * dm2 * L / (4.0 * E)
    amp = math.sin(2 * theta) ** 2
    P_analytic = amp * (math.sin(Delta) ** 2)
    assert abs(P_gksl - P_analytic) < 5e-3


if __name__ == '__main__':
    test_ligo_modulation_and_damping_preserve_trace()
    test_zero_ligo_reduces_to_vacuum()
    print('LIGO-sector unified integration tests passed')
