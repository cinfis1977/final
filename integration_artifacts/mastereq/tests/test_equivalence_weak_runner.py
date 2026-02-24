from __future__ import annotations

import math
from pathlib import Path
import importlib.util
import sys

import numpy as np

from mastereq.unified_gksl import UnifiedGKSL


def _load_module_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create module spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    # Needed for dataclasses/type resolution when the loaded module uses
    # `from __future__ import annotations` (string annotations).
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _repo_root() -> Path:
    # .../integration_artifacts/mastereq/tests/test_*.py -> repo root
    return Path(__file__).resolve().parents[3]


def _runner_module():
    root = _repo_root()
    runner_path = root / "nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py"
    if not runner_path.exists():
        raise RuntimeError(f"Runner file not found: {runner_path}")
    return _load_module_from_path("nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude", runner_path)


def _theta_for_amplitude(amp: float) -> float:
    # Want sin^2(2theta) = amp.
    amp = float(np.clip(amp, 0.0, 1.0))
    return 0.5 * math.asin(math.sqrt(amp))


def _prob_from_unified_gksl(*, dm2: float, theta: float, L_km: float, E_GeV: float, dphi: float = 0.0, steps: int = 300, appearance: bool = True) -> float:
    """Compute a probability via the GKSL integrator.

    If dphi != 0, implement it as a constant-in-L delta(dm2) term such that
    the accumulated extra phase at baseline L_km equals dphi:

      dphi = 1.267 * delta_dm2 * L / (4E)   =>   delta_dm2 = dphi * 4E / (1.267 L)

    This matches the runner's phase convention after mapping dm2_gksl = 4*dm2_runner.
    """
    ug = UnifiedGKSL(dm2, theta)

    if dphi != 0.0:
        delta_dm2 = float(dphi) * (4.0 * float(E_GeV)) / (1.267 * max(float(L_km), 1e-12))

        def extra_mass(_L: float, _E: float) -> np.ndarray:
            return np.array([[0.0, 0.0], [0.0, delta_dm2]], dtype=float)

        ug.add_mass_sector(extra_mass)

    rho = ug.integrate(float(L_km), float(E_GeV), steps=int(steps))
    if appearance:
        return float(np.real(rho[0, 0]))
    return float(np.real(rho[1, 1]))


def test_equivalence_weak_runner_sm_probabilities():
    """GKSL unitary evolution reproduces the runner's SM probabilities.

    The runner uses Delta = 1.267*dm2*L/E (no /4). The GKSL solver uses the
    standard two-flavor phase convention with /4, so we map:
      dm2_gksl = 4 * dm2_runner
    and choose theta so sin^2(2theta) matches the runner's amplitude.
    """
    r = _runner_module()

    dm2_runner = 2.50e-3
    dm2_gksl = 4.0 * dm2_runner

    # Appearance amplitude in the runner
    theta23 = math.radians(45.0)
    theta13 = math.radians(8.6)
    amp_app = (math.sin(theta23) ** 2) * (math.sin(2 * theta13) ** 2)
    theta_app = _theta_for_amplitude(amp_app)

    theta_dis = math.radians(45.0)  # maximal mixing => survival amplitude 1

    test_points = [
        # (L_km, E_GeV)
        (810.0, 1.25),
        (810.0, 2.25),
        (295.0, 0.60),
        (295.0, 0.90),
    ]

    for L_km, E_GeV in test_points:
        p_app_runner = float(r.prob_appearance_sm(E_GeV, L_km))
        p_app_gksl = _prob_from_unified_gksl(dm2=dm2_gksl, theta=theta_app, L_km=L_km, E_GeV=E_GeV, steps=350, appearance=True)
        assert abs(p_app_gksl - p_app_runner) < 2.5e-4

        p_surv_runner = float(r.prob_disappearance_sm(E_GeV, L_km))
        p_surv_gksl = _prob_from_unified_gksl(dm2=dm2_gksl, theta=theta_dis, L_km=L_km, E_GeV=E_GeV, steps=350, appearance=False)
        assert abs(p_surv_gksl - p_surv_runner) < 2.5e-4


def test_equivalence_weak_runner_phase_shift_matches_mass_sector():
    """Runner's Δ->Δ+dphi trick matches a constant delta(dm2) GKSL term."""
    r = _runner_module()

    dm2_runner = 2.50e-3
    dm2_gksl = 4.0 * dm2_runner

    # Match runner's appearance amplitude
    theta23 = math.radians(45.0)
    theta13 = math.radians(8.6)
    amp_app = (math.sin(theta23) ** 2) * (math.sin(2 * theta13) ** 2)
    theta_app = _theta_for_amplitude(amp_app)

    # Use canonical prereg-like params from verdict_commands.txt (NOvA/T2K):
    # A=-0.002 alpha=0.7 n=0 E0=1 omega0_geom=fixed phi=pi/2 zeta=0.05 k_rt=180
    def make_kp(L0_km: float, omega: float) -> object:
        kp = r.KernelParams(
            L0_km=float(L0_km),
            E0_GeV=1.0,
            A=-0.002,
            alpha=0.7,
            n=0.0,
            omega_1_per_km=float(omega),
            phi=1.57079632679,
            zeta=0.05,
            breath_B=0.3,
            breath_omega0_1_per_km=float(omega),
            breath_gamma=0.2,
            thread_C=1.0,
            thread_omega0_1_per_km=float(omega),
            thread_gamma=0.2,
            thread_weight_app=0.0,
            thread_weight_dis=1.0,
            kappa_gate=0.0,
            T0=1.0,
            mu=0.0,
            eta=0.0,
            k_rt=180.0,
            k_rt_ref=180.0,
            kernel="rt",
        )
        return kp

    # Two baselines used in verdict: 810 km (NOvA) and 295 km (T2K)
    cases = [
        (810.0, 1.25),
        (810.0, 2.25),
        (295.0, 0.60),
        (295.0, 0.90),
    ]

    for L_km, E_GeV in cases:
        omega = r.omega0_geom_fixed(L_km)  # fixed omega0_geom convention
        kp = make_kp(L_km, omega)
        dphi = float(r.kernel_phase_dphi(L_km, E_GeV, kp))

        p_sm = float(r.prob_appearance_sm(E_GeV, L_km))
        p_geo_runner = float(r.apply_phase_shift_to_prob(np.array([p_sm]), np.array([dphi]), mode="appearance")[0])

        p_geo_gksl = _prob_from_unified_gksl(dm2=dm2_gksl, theta=theta_app, L_km=L_km, E_GeV=E_GeV, dphi=dphi, steps=400, appearance=True)

        assert abs(p_geo_gksl - p_geo_runner) < 5.0e-4
