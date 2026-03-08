import numpy as np

from mastereq.gk_sl_solver_3flavor import (
    integrate_rho_3flavor,
    prob_from_rho,
    vacuum_hamiltonian_3flavor,
)


def test_3flavor_identity_when_no_masses_no_mixing():
    dm21 = 0.0
    dm31 = 0.0
    th12 = 0.0
    th13 = 0.0
    th23 = 0.0
    dcp = 0.0

    def Hfn(_L, E):
        return vacuum_hamiltonian_3flavor(dm21, dm31, th12, th13, th23, dcp, E)

    def Dfn(_L, _E, rho):
        return np.zeros_like(rho, dtype=complex)

    rho = integrate_rho_3flavor(100.0, 2.0, Hfn, Dfn, steps=32, flavor_in="mu")

    # mu should remain mu.
    assert abs(prob_from_rho(rho, "mu") - 1.0) < 1e-8
    assert abs(prob_from_rho(rho, "e") - 0.0) < 1e-8
    assert abs(prob_from_rho(rho, "tau") - 0.0) < 1e-8


def test_3flavor_probabilities_are_bounded_and_trace_one():
    # Roughly standard values
    dm21 = 7.53e-5
    dm31 = 2.45e-3
    th12 = np.deg2rad(33.44)
    th13 = np.deg2rad(8.57)
    th23 = np.deg2rad(49.2)
    dcp = np.deg2rad(195.0)

    def Hfn(_L, E):
        return vacuum_hamiltonian_3flavor(dm21, dm31, th12, th13, th23, dcp, E)

    def Dfn(_L, _E, rho):
        return np.zeros_like(rho, dtype=complex)

    rho = integrate_rho_3flavor(295.0, 0.6, Hfn, Dfn, steps=256, flavor_in="mu")

    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 1e-8
    assert abs(np.imag(tr)) < 1e-8

    probs = np.array([prob_from_rho(rho, "e"), prob_from_rho(rho, "mu"), prob_from_rho(rho, "tau")])
    assert np.all(probs >= -1e-6)
    assert np.all(probs <= 1.0 + 1e-6)
    assert abs(float(probs.sum()) - 1.0) < 5e-4
