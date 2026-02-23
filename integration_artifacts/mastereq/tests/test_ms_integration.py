import math
import numpy as np
from mastereq.unified_gksl import UnifiedGKSL
from mastereq.ms_sector import make_msw_flavor_H_fn, make_msw_damping_fn


def test_msw_preserves_trace_and_positivity():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    # add a modest Earth-like density ~ 3 g/cm^3
    ug.add_flavor_sector(make_msw_flavor_H_fn(rho_gcm3=3.0, Ye=0.5))
    ug.add_damping(make_msw_damping_fn(gamma=1e-4))

    rho = ug.integrate(L, E, steps=200)

    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 1e-8
    assert np.allclose(rho, rho.conj().T, atol=1e-10)
    eigs = np.linalg.eigvalsh(rho)
    assert np.all(eigs >= -1e-8)


def test_msw_zero_density_reduces_to_vacuum():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    # zero density -> no additional potential
    rho = ug.integrate(L, E, steps=400)
    P_gksl = float(np.real(rho[0, 0]))

    Delta = 1.267 * dm2 * L / (4.0 * E)
    amp = math.sin(2 * theta) ** 2
    P_analytic = amp * (math.sin(Delta) ** 2)
    assert abs(P_gksl - P_analytic) < 5e-3


if __name__ == '__main__':
    test_msw_preserves_trace_and_positivity()
    test_msw_zero_density_reduces_to_vacuum()
    print('MS-sector unified integration tests passed')
