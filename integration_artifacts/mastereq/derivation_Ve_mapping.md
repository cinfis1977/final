Derivation: mapping the weak-sector potential V_e into code units (1/km) and an
equivalent Δm^2 when needed

Purpose
- Provide a compact, reproducible conversion between the physical MSW potential
  V_e = √2 G_F N_e and the units used by the integration code in
  `integration_artifacts/mastereq/` where Hamiltonian entries are represented
  in 1/km (so they add directly to the solver's `H(L,E)` returned by the
  `UnifiedGKSL` builder).

Conventions used by the code
- The code constructs the vacuum Hamiltonian for two flavors as (see `gk_sl_solver_clean.py`):

  H_vac(L,E) = K * (Δm^2) / (2 E_GeV)

  where K = 1.267 and E_GeV is the neutrino energy in GeV. With this choice
  the standard oscillation phase used elsewhere in this repo is

  Φ_vac = K * Δm^2 [eV^2] * L[km] / E[GeV]

  so H_vac has units 1/km (consistent with dρ/dL = −i[H,ρ]).

Step 1 — compute V_e (energy units)
- In natural units (ħ = c = 1) the MSW potential is

  V_e = √2 G_F N_e

  where G_F is the Fermi constant. A convenient practical form often used
  in the neutrino literature maps matter density ρ (g/cm^3) and electron
  fraction Y_e to V_e (in eV):

  V_e [eV] ≈ 7.63×10^(−14) × Y_e × ρ [g/cm^3]

  This numerical relation implicitly incorporates the necessary factors of
  ħc when converting number density units into energy units and is
  therefore recommended for practical coding. Example: for Earth-like rock
  (ρ≈3 g/cm^3, Y_e≈0.5) we get V_e ≈ 1.14×10^(−13) eV.

Step 2 — convert V_e (eV) into inverse-kilometers (1/km)
- Use the conversion between energy and inverse length from ħc:

  1 eV  ⇄  (ħc) / (1 eV)  ⇒  1 eV = 5.0677307×10^3 km^(−1)

  Therefore

  H_from_V(L,E) [1/km] = V_e [eV] × 5.0677307×10^3

  Example (Earth rock):

  H_from_V ≈ 1.14×10^(−13) eV × 5.0677×10^3 km^(−1) ≈ 5.8×10^(−10) km^(−1).

Step 3 — (optional) express V_e as an equivalent Δm^2 contribution
- Sometimes it is convenient to interpret a flavor-diagonal potential as an
effective mass-squared splitting so it can be added via the mass-basis
registration API. Starting from the code vacuum mapping

  H_vac = K × Δm^2 / (2 E_GeV)

  if we want H_from_V to match this contribution, solve for Δm^2_equiv:

  Δm^2_equiv [eV^2] = (2 E_GeV / K) × H_from_V [1/km]

  Substituting H_from_V = V_e[eV] × 5.0677307×10^3 gives a one-line
  conversion:

  Δm^2_equiv = (2 E_GeV / K) × (V_e[eV] × 5.0677307×10^3)

  Example numeric constant (collapse physical constants): combining the
  numerical factors for the common V_e ≈ 7.63×10^(−14)×Y_e×ρ[g/cm^3]:

  Δm^2_equiv [eV^2] ≈ 6.10×10^(−10) × E_GeV × Y_e × ρ[g/cm^3]

  (Derivation: 2 / K × 7.63e-14 × 5.0677e3 ≈ 6.10e-10.) For E=1 GeV,
  Y_e=0.5, ρ=3 g/cm^3 → Δm^2_equiv ≈ 9.15×10^(−10) eV^2, which is many orders
  of magnitude smaller than atmospheric Δm^2≈2.5×10^(−3) eV^2 (so the MSW
  potential is a small correction in that parameter regime).

Implementation recommendations
- Use the `V_e[eV] ≈ 7.63e-14 × Y_e × ρ[g/cm^3]` relation to compute the
  potential from conventional geophysical inputs (ρ, Y_e). This avoids
  explicit low-level ħc bookkeeping and matches standard neutrino practice.
- To add a weak-sector flavor potential in the unified API, either:
  - provide `H_weak^{flav}(L,E)` directly with
    `H_from_V = V_e[eV] * 5.0677307e3` (units 1/km), or
  - provide a mass-basis Δm^2 function computed with
    `Δm2_equiv = (2*E_GeV/K) * H_from_V` and register it via
    `UnifiedGKSL.add_mass_sector(...)` (the wrapper will rotate and add it).
- If you prefer positivity-by-construction for damping, supply Lindblad
  operators L_a and nonnegative rates γ_a (the wrapper currently accepts
  a pre-built dissipator function D(L,E,ρ) and sums them). We can add a
  small helper that converts simple dephasing/population-relaxation
  parametric forms into explicit Lindblad operators if you want.

References and constants
- ħ c = 197.3269804 MeV·fm (useful to reproduce the 1 eV ↔ 5.0677×10^3 km^(−1) number)
- Practical MSW mapping reference number: V_e[eV] ≈ 7.63×10^(−14) × Y_e × ρ[g/cm^3]
- Code constant: K = 1.267 (used in `gk_sl_solver_clean.py`)

Contact
- If you want, I can add a tiny helper function implementing these conversions
  (e.g. `weak_sector.ve_from_rho(rho_gcm3, Ye)` and
  `weak_sector.delta_m2_equiv_from_Ve(Ve_eV, E_GeV)`) and update the tests
  to use physically consistent numbers.
