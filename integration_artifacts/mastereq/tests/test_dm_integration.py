import math
import os
import numpy as np
from mastereq.unified_gksl import UnifiedGKSL
from mastereq.dm_sector import make_dm_mass_modulation, make_dm_scattering_damping, dm_density_to_amplitude


def test_dm_modulation_and_damping_preserve_trace():
    dm2 = 2.5e-3
    theta = math.radians(45.0)
    E = 1.0
    L = 295.0

    ug = UnifiedGKSL(dm2, theta)
    # Allow overriding the test coupling via env `DM_TEST_COUPLING` for safe runs.
    # Default uses a small coupling that avoids numerical overflow while still
    # exercising the DM-sector code.
    coupling_env = os.environ.get("DM_TEST_COUPLING")
    if coupling_env is None:
        coupling_val = 1e-12
    else:
        coupling_val = float(coupling_env)
    amp = dm_density_to_amplitude(0.4, coupling_g=coupling_val, E_GeV=E)  # toy mapping
    ug.add_mass_sector(make_dm_mass_modulation(amplitude_eV2=amp, omega_km_inv=0.005))
    ug.add_damping(make_dm_scattering_damping(gamma_s=1e-4))

    rho = ug.integrate(L, E, steps=300)
    tr = np.trace(rho)
    assert abs(np.real(tr) - 1.0) < 1e-8
    assert np.allclose(rho, rho.conj().T, atol=1e-10)
    eigs = np.linalg.eigvalsh(rho)
    assert np.all(eigs >= -1e-8)


def test_zero_dm_reduces_to_vacuum():
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
    test_dm_modulation_and_damping_preserve_trace()
    test_zero_dm_reduces_to_vacuum()
    print('DM-sector unified integration tests passed')
