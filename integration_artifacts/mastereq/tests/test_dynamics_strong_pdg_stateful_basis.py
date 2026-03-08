import math

import numpy as np

from integration_artifacts.mastereq.strong_pdg_stateful_dynamics import (
    PDGBasisState,
    PDGParamsSigmaTot,
    PDGParamsRho,
    dsigma_dt_from_state,
    sigma_from_state,
    t_from_sqrts,
)


def test_dynamics_strong_pdg_basis_exact_step_reproduces_closed_form_sigma():
    pars = PDGParamsSigmaTot()
    channel = "pp"

    sqrts = np.array([7.0, 20.0, 100.0, 13000.0], dtype=float)
    t = t_from_sqrts(sqrts, sM_GeV2=pars.sM_GeV2)

    state = PDGBasisState.from_t0(float(t[0]), pars.eta1, pars.eta2)

    sig_from_state = []
    for ti in t:
        state.advance_to(float(ti), pars.eta1, pars.eta2)
        sig_from_state.append(
            sigma_from_state(
                state,
                channel,  # type: ignore[arg-type]
                P_mb=pars.P_mb,
                H_mb=pars.H_mb,
                R1_mb=pars.R1_mb,
                eta1=pars.eta1,
                R2_mb=pars.R2_mb,
                eta2=pars.eta2,
            )
        )

    sig_from_state = np.array(sig_from_state, dtype=float)

    # Closed-form reference (same as in original runner)
    x = np.maximum((sqrts**2) / pars.sM_GeV2, 1e-30)
    logx = np.log(x)
    base = pars.P_mb + pars.H_mb * (logx**2) + pars.R1_mb * (x ** (-pars.eta1))
    odd = pars.R2_mb * (x ** (-pars.eta2))
    sig_ref = base - odd

    assert np.allclose(sig_from_state, sig_ref, atol=0.0, rtol=1e-14)


def test_dynamics_strong_pdg_state_derivative_matches_analytic_dsigma_dlns():
    pars = PDGParamsRho()
    channel = "pbarp"

    sqrts = np.array([10.0, 100.0, 1000.0], dtype=float)
    t = t_from_sqrts(sqrts, sM_GeV2=pars.sM_GeV2)

    state = PDGBasisState.from_t0(float(t[0]), pars.eta1, pars.eta2)
    ds_from_state = []
    for ti in t:
        state.advance_to(float(ti), pars.eta1, pars.eta2)
        ds_from_state.append(
            dsigma_dt_from_state(
                state,
                channel,  # type: ignore[arg-type]
                H_mb=pars.H_mb,
                R1_mb=pars.R1_mb,
                eta1=pars.eta1,
                R2_mb=pars.R2_mb,
                eta2=pars.eta2,
            )
        )
    ds_from_state = np.array(ds_from_state, dtype=float)

    x = np.maximum((sqrts**2) / pars.sM_GeV2, 1e-30)
    logx = np.log(x)
    term_log = 2.0 * pars.H_mb * logx
    term_r1 = -pars.eta1 * pars.R1_mb * (x ** (-pars.eta1))
    term_r2 = -pars.eta2 * pars.R2_mb * (x ** (-pars.eta2))
    ds_ref = term_log + term_r1 + term_r2

    assert np.allclose(ds_from_state, ds_ref, atol=0.0, rtol=1e-14)
