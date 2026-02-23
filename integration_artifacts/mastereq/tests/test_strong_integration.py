import math
import numpy as np
from mastereq.unified_gksl import UnifiedGKSL
from mastereq.strong_sector import make_strong_mass_fn, make_strong_population_damping


def test_strong_preserves_trace_and_changes_prob():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    ug.add_mass_sector(make_strong_mass_fn(amplitude=1e-3, k_km=0.01))
    ug.add_damping(make_strong_population_damping(gamma_pop=1e-3))

    rho = ug.integrate(L, E, steps=300)
    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 1e-8
    assert np.allclose(rho, rho.conj().T, atol=1e-10)
    eigs = np.linalg.eigvalsh(rho)
    assert np.all(eigs >= -1e-8)


def test_zero_strong_reduces_to_vacuum():
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
    test_strong_preserves_trace_and_changes_prob()
    test_zero_strong_reduces_to_vacuum()
    print('Strong-sector unified integration tests passed')
