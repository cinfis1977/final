import math
import numpy as np
try:
    from mastereq.gk_sl_solver import build_Hfn_2flavor, build_Dfn_simple, integrate_rho, geometric_delta_m2_2flavor
except Exception:
    from mastereq.gk_sl_solver_clean import build_Hfn_2flavor, build_Dfn_simple, integrate_rho, geometric_delta_m2_2flavor


def base_dphi_dL_kernel(L_km: float, E_GeV: float, A: float, omega: float, phi: float, zeta: float) -> float:
    damp = math.exp(-zeta * abs(omega) * L_km)
    return A * damp * math.sin(omega * L_km + phi)


def test_trace_and_hermitian():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    def extra_dm2_fn(Lk, E_GeV):
        base = base_dphi_dL_kernel(Lk, E_GeV, 0.01, 0.00388, math.pi/2, 0.0)
        return geometric_delta_m2_2flavor(base, E_GeV, scale_factor=1.0)

    Hfn = build_Hfn_2flavor(dm2, theta, extra_dm2_fn)
    Dfn = build_Dfn_simple(0.01, lambda Lk, E_GeV: 1.0)
    rho = integrate_rho(L, E, Hfn, Dfn, steps=200)

    # trace ~1
    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 1e-8

    # hermitian
    assert np.allclose(rho, rho.conj().T, atol=1e-10)


def test_positive_semidef():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    def extra_dm2_fn(Lk, E_GeV):
        base = base_dphi_dL_kernel(Lk, E_GeV, 0.0, 0.0, 0.0, 0.0)
        return geometric_delta_m2_2flavor(base, E_GeV, scale_factor=1.0)

    Hfn = build_Hfn_2flavor(dm2, theta, extra_dm2_fn)
    Dfn = build_Dfn_simple(0.0, lambda Lk, E_GeV: 1.0)
    rho = integrate_rho(L, E, Hfn, Dfn, steps=200)

    eigs = np.linalg.eigvalsh(rho)
    assert np.all(eigs >= -1e-10)


def test_agrees_with_analytic_sm():
    # When extra_dm2=0 and gamma=0 the GKSL evolution reduces to unitary vacuum evolution
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    def extra_dm2_fn(Lk, E_GeV):
        return geometric_delta_m2_2flavor(0.0, E_GeV, scale_factor=1.0)

    Hfn = build_Hfn_2flavor(dm2, theta, extra_dm2_fn)
    Dfn = build_Dfn_simple(0.0, lambda Lk, E_GeV: 1.0)
    rho = integrate_rho(L, E, Hfn, Dfn, steps=400)

    P_gksl = float(np.real(rho[0, 0]))

    # analytic two-flavor appearance prob for given params
    # Correct two-flavor appearance analytic formula:
    # P = sin^2(2 theta) * sin^2(1.267 * dm2 * L / (4 E))
    Delta = 1.267 * dm2 * L / (4.0 * E)
    amp = math.sin(2 * theta) ** 2
    P_analytic = amp * (math.sin(Delta) ** 2)

    assert abs(P_gksl - P_analytic) < 5e-3


if __name__ == '__main__':
    test_trace_and_hermitian()
    test_positive_semidef()
    test_agrees_with_analytic_sm()
    print('All mastereq GKSL basic tests passed')
