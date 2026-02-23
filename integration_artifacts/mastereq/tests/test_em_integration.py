import math
import numpy as np
from mastereq.unified_gksl import UnifiedGKSL
from mastereq.em_sector import make_em_flavor_H_fn, make_em_damping_from_radiation


def small_B(L):
    return 1e-9  # Tesla (toy: tiny field)


def test_em_adds_offdiagonal_coupling_and_preserves_trace():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    ug.add_flavor_sector(make_em_flavor_H_fn(mu_nu_muB=1e-11, B_field_T_fn=small_B))
    ug.add_damping(make_em_damping_from_radiation(gamma=1e-6))

    rho = ug.integrate(L, E, steps=300)
    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 1e-8
    assert np.allclose(rho, rho.conj().T, atol=1e-10)
    eigs = np.linalg.eigvalsh(rho)
    assert np.all(eigs >= -1e-8)


def test_zero_em_reduces_to_vacuum():
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
    test_em_adds_offdiagonal_coupling_and_preserves_trace()
    test_zero_em_reduces_to_vacuum()
    print('EM-sector unified integration tests passed')
