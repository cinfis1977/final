import math
import numpy as np
from mastereq.unified_gksl import UnifiedGKSL
from mastereq.weak_sector import make_weak_flavor_H_fn, make_weak_damping_fn


def test_weak_adds_potential_but_preserves_trace():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    # add weak sector with a small density
    ug.add_flavor_sector(make_weak_flavor_H_fn(ne_cm3=1e20, scale=1.0))
    ug.add_damping(make_weak_damping_fn(gamma=1e-3))

    rho = ug.integrate(L, E, steps=200)

    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 1e-8
    # hermitian and positive semidef
    assert np.allclose(rho, rho.conj().T, atol=1e-10)
    eigs = np.linalg.eigvalsh(rho)
    assert np.all(eigs >= -1e-8)


def test_with_zero_weak_reduces_to_vacuum():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    # no sectors -> unitary vacuum evolution
    rho = ug.integrate(L, E, steps=400)
    P_gksl = float(np.real(rho[0, 0]))

    # analytic two-flavor appearance probability (same normalization as solver)
    Delta = 1.267 * dm2 * L / (4.0 * E)
    amp = math.sin(2 * theta) ** 2
    P_analytic = amp * (math.sin(Delta) ** 2)
    assert abs(P_gksl - P_analytic) < 5e-3


if __name__ == '__main__':
    test_weak_adds_potential_but_preserves_trace()
    test_with_zero_weak_reduces_to_vacuum()
    print('Weak-sector unified integration tests passed')
