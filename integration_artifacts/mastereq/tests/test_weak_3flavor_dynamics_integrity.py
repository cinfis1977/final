import numpy as np

from mastereq.unified_gksl_3flavor import UnifiedGKSL3
from mastereq.gk_sl_solver_3flavor import lindblad_dephasing_offdiag


def _purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def _assert_density_matrix_sane(rho: np.ndarray, *, eps_eig: float = 5e-8) -> None:
    # Hermitian
    assert np.max(np.abs(rho - rho.conj().T)) < 5e-8

    # Trace 1
    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 5e-8
    assert abs(np.imag(tr)) < 5e-8

    # Positivity (allow tiny negative eigenvalues from RK4 drift)
    evals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    assert float(evals.min()) >= -float(eps_eig), f"min_eig={float(evals.min())}"


def _prob(rho: np.ndarray, flavor_out: str) -> float:
    idx = {"e": 0, "mu": 1, "tau": 2}[flavor_out]
    return float(np.real(rho[idx, idx]))


def test_3flavor_unitary_limit_preserves_purity_and_positivity():
    """Dynamics test: D=0 (unitary) should preserve purity for pure initial state."""

    ug = UnifiedGKSL3(
        dm21=7.53e-5,
        dm31=2.45e-3,
        theta12=np.deg2rad(33.44),
        theta13=np.deg2rad(8.57),
        theta23=np.deg2rad(49.2),
        delta_cp=np.deg2rad(195.0),
        flavor_in="mu",
    )

    rho = ug.integrate(295.0, 0.6, steps=600)

    _assert_density_matrix_sane(rho)

    # Unitarity limit: purity stays ~1
    assert abs(_purity(rho) - 1.0) < 3e-4

    # Probability simplex
    pe, pmu, ptau = _prob(rho, "e"), _prob(rho, "mu"), _prob(rho, "tau")
    assert pe >= -1e-6 and pmu >= -1e-6 and ptau >= -1e-6
    assert pe <= 1.0 + 1e-6 and pmu <= 1.0 + 1e-6 and ptau <= 1.0 + 1e-6
    assert abs((pe + pmu + ptau) - 1.0) < 5e-4


def test_3flavor_dephasing_reduces_purity_but_keeps_positivity():
    """Dynamics test: with dephasing, purity should drop below 1 but rho remains PSD."""

    ug = UnifiedGKSL3(
        dm21=7.53e-5,
        dm31=2.45e-3,
        theta12=np.deg2rad(33.44),
        theta13=np.deg2rad(8.57),
        theta23=np.deg2rad(49.2),
        delta_cp=np.deg2rad(195.0),
        flavor_in="mu",
    )

    gamma = 2e-3  # 1/km, intentionally noticeable

    def Dfn(_L, _E, rho, g=gamma):
        return lindblad_dephasing_offdiag(rho, g)

    ug.add_damping(Dfn)

    rho = ug.integrate(295.0, 0.6, steps=800)

    _assert_density_matrix_sane(rho, eps_eig=1e-6)

    assert _purity(rho) < 0.999


def test_3flavor_T_symmetry_in_vacuum_when_delta_cp_zero():
    """In vacuum with delta_cp=0, H is real ⇒ T symmetry: P(a→b)=P(b→a)."""

    common = dict(
        dm21=7.53e-5,
        dm31=2.45e-3,
        theta12=np.deg2rad(33.44),
        theta13=np.deg2rad(8.57),
        theta23=np.deg2rad(49.2),
        delta_cp=0.0,
    )

    ug_mu = UnifiedGKSL3(**common, flavor_in="mu")
    ug_e = UnifiedGKSL3(**common, flavor_in="e")

    rho_mu = ug_mu.integrate(295.0, 0.6, steps=700)
    rho_e = ug_e.integrate(295.0, 0.6, steps=700)

    p_mu_to_e = _prob(rho_mu, "e")
    p_e_to_mu = _prob(rho_e, "mu")

    assert abs(p_mu_to_e - p_e_to_mu) < 2e-3


def test_3flavor_CPT_relation_in_vacuum_via_antineutrino_mapping():
    """CPT in vacuum: P(να→νβ; δ) = P(ν̄β→ν̄α; δ).

    For antineutrinos in vacuum, mapping is equivalent to δ → -δ (complex conjugation).
    So we check: P(ν_mu→ν_e; δ) ≈ P(ν_e→ν_mu; -δ).

    This is a dynamics test (state evolved in both cases).
    """

    dcp = np.deg2rad(195.0)

    common = dict(
        dm21=7.53e-5,
        dm31=2.45e-3,
        theta12=np.deg2rad(33.44),
        theta13=np.deg2rad(8.57),
        theta23=np.deg2rad(49.2),
    )

    ug_nu = UnifiedGKSL3(**common, delta_cp=dcp, flavor_in="mu")
    ug_anu = UnifiedGKSL3(**common, delta_cp=-dcp, flavor_in="e")

    rho_mu = ug_nu.integrate(295.0, 0.6, steps=800)
    rho_e = ug_anu.integrate(295.0, 0.6, steps=800)

    p_mu_to_e = _prob(rho_mu, "e")
    p_anu_e_to_anu_mu = _prob(rho_e, "mu")

    assert abs(p_mu_to_e - p_anu_e_to_anu_mu) < 2e-3
