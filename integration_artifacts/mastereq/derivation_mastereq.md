**Derivation and unit mappings for Master Equation integration (Weak / Strong / EM)**

Purpose
- Collect mathematical mappings, unit conversions, and coding contracts for
  integrating sector contributions into the master equation
  $$\frac{d\rho}{dL} = -i\,[H(L,E),\rho] + \mathcal{D}[\rho]\,,\qquad L\text{ in km},$$
  where the code represents Hamiltonians in units of $\mathrm{km}^{-1}$.

Common conventions used in the code
- Vacuum Hamiltonian (two-flavor) used by the solver is
  $$H_{\rm vac}(E)=K\,\frac{\Delta m^2}{2E_{\rm GeV}},\qquad K=1.267,$$
  so the usual oscillation phase is $\Phi=K\Delta m^2 L/E$ with $L$ in km,
  $\Delta m^2$ in eV^2 and $E$ in GeV. Therefore every sector-provided term
  must be converted to units of $\mathrm{km}^{-1}$ before being added to $H$.

Conversion constants and useful numbers
- Energy ↔ inverse length:
  $$1\ \mathrm{eV} \approx 5.0677307\times10^{3}\ \mathrm{km}^{-1}.$$ 
- Practical MSW mapping used in neutrino literature: 
  $$V_e[\mathrm{eV}] \approx 7.63\times10^{-14}\;Y_e\;\rho[\mathrm{g/cm^3}].$$

Unified implementation contract (how sectors plug in)
- Sector outputs may be provided as either:
  1. mass-basis $\delta M^2_{\rm mass}(L,E)$ (2×2 real matrix in mass basis). The wrapper converts it to flavor-basis Hamiltonian via
     $$H_{\rm mass\to flav}(L,E)=K\frac{1}{2E}\,U\,\delta M^2_{\rm mass}(L,E)\,U^\dagger,$$
     where $U(\theta)$ is the two-flavor mixing matrix used by the vacuum term.
  2. flavor-basis Hamiltonian $H_{\rm sector}^{\rm flav}(L,E)$ already in $\mathrm{km}^{-1}$.
- Damping contributions should be provided either as an explicit dissipator function
  $\mathcal{D}_{\rm sector}[\rho]$ or (preferably) as a set of Lindblad operators
  $\{L_a\}$ with nonnegative rates $\gamma_a$ such that
  $$\mathcal{D}[\rho]=\sum_a\gamma_a\Big(L_a\rho L_a^\dagger-\tfrac12\{L_a^\dagger L_a,\rho\}\Big).$$

Weak sector (MSW potential) — math and code mapping
- Physics: coherent forward scattering on electrons gives a flavor potential
  $$V_e(L)=\sqrt{2}G_F N_e(L)\quad(\text{energy units}).$$
- Practical coding recipe (used in `weak_sector.py`):
  1. Compute $V_e$ in eV from density and electron fraction using
     $$V_e[\mathrm{eV}] \approx 7.63\times10^{-14}\;Y_e\;\rho[\mathrm{g/cm^3}].$$
  2. Convert to Hamiltonian units $\mathrm{km}^{-1}$:
     $$H_{\rm weak}^{\rm flav}(L) = V_e[\mathrm{eV}] \times 5.0677307\times10^{3}\;\mathrm{km}^{-1}.$$
  3. Add as a flavor-diagonal term $H_{\rm weak}^{\rm flav}(L)=\mathrm{diag}(H_{\rm weak},0)$ or, if desired, convert to mass-basis equivalent
     $$\Delta m^2_{\rm equiv} = \frac{2E_{\rm GeV}}{K}\;H_{\rm weak}^{\rm flav}(L) \quad(\mathrm{eV}^2)$$
     so it can be registered as a mass-basis contribution.
- Damping: a simple, commonly-used approximation is pure dephasing of off-diagonals
  $$\mathcal{D}_{\rm weak}[\rho]_{ij} = -\gamma_{\rm weak}(L)\rho_{ij}\ (i\ne j),$$
  which preserves populations and trace. For strict complete-positivity prefer explicit Lindblad operators.

Strong sector (toy mapping) — math and code mapping
- Idea used in integration artifacts: model strong-sector corrections as a mass-basis
  diagonal modulation (toy):
  $$\delta M^2_{\rm strong,mass}(L) = A(L)\;\sigma_z^{(\rm mass)}$$
  (or other basis-structures depending on physics). The wrapper converts via the usual $K/(2E)$ factor.
- Population damping toy:
  $$\mathcal{D}_{\rm strong}[\rho] = -\gamma_{\rm pop}\big(\rho - \tfrac12\mathrm{Tr}(\rho)I\big),$$
  which relaxes populations toward an equal mixture while preserving trace.
- Conversion helpers (code):
  - mass-amplitude (eV^2) to Hamiltonian $H$ (1/km):
    $$H = K\frac{\mathrm{amp\ (eV^2)}}{2E_{\rm GeV}}.$$ 
  - inverse: given $H$ (1/km), derive equivalent mass amplitude
    $$\mathrm{amp\ (eV^2)} = \frac{2E_{\rm GeV}}{K}\,H.$$

EM sector (toy magnetic coupling) — math and code mapping
- Toy physics: neutrino magnetic moment $\mu_\nu$ couples to an external magnetic field $B(L)$, producing an off-diagonal transition term.
- Energy scale (toy): $\delta E \sim \mu_\nu B$ (with $\mu_\nu$ expressed in eV/T if given in Bohr magnetons multiply by $\mu_B$).
- Implementation recipe used in `em_sector.py`:
  1. Provide $\mu_\nu$ in units of $\mu_B$ (Bohr magneton) or directly in eV/T.
  2. Compute $\delta E[\mathrm{eV}] = \mu_\nu[\mu_B]\times\mu_B[\mathrm{eV/T}]\times B(L)[\mathrm{T}]$.
  3. Convert to Hamiltonian units $\mathrm{km}^{-1}$: multiply by $5.0677307\times10^3$.
  4. Place the term as off-diagonal coupling e.g. $H_{\rm EM}^{\rm flav}(L)=H_{\rm val}(L)\,\sigma_x^{(\rm flav)}$.
- EM damping: small off-diagonal damping can be modeled similarly to weak dephasing, or derived from explicit radiative Lindblad operators if available.

Master-equation assembly procedure (practical algorithm)
1. Initialize $H_{\rm vac}(E)$ using $K\Delta m^2/(2E)$.  
2. For each mass-basis sector function $\delta M^2_{\rm mass}(L,E)$, compute flavor-basis $H$ via $K/(2E)$ and rotate with $U(\theta)$.  
3. For each flavor-basis $H_{\rm sector}^{\rm flav}(L,E)$, add directly to $H$.  
4. Construct total dissipator $\mathcal{D}[\rho]=\sum_{\rm sectors}\mathcal{D}_{\rm sector}[\rho]$ (prefer Lindblad form when possible).  
5. Integrate $d\rho/dL=-i[H,\rho]+\mathcal{D}[\rho]$ with a stable integrator (we use RK4 with small step size), enforcing Hermiticity and trace normalization after integration to reduce numerical drift.

Sanity checks and diagnostics
- After integration, verify:
  - $|\mathrm{Tr}(\rho)-1|<\epsilon$ (renormalize if necessary)
  - $\rho=\rho^\dagger$ (symmetrize to reduce numerical error)
  - Eigenvalues $\lambda_i(\rho)\ge-\delta$ (small negative values tolerated due to numerics; if large negativity appears, investigate dissipator construction)
- Compare special-case limits: turning off sector terms should reduce to unitary vacuum evolution and reproduce analytic two-flavor formulas within numerical tolerance.

Suggestions
- Keep sector mappings modular (mass-basis vs flavor-basis) as implemented by `UnifiedGKSL`.  
- Prefer explicit Lindblad operators for any sector where physical dissipation rates and jump operators are known; otherwise parametric dephasing/population-damping is a controllable approximation.  
- After implementing DM/LIGO/MS sectors, add per-sector derivation subsections to this file and unit tests mirroring the weak/strong/em tests.

References
- Practical MSW constant and conversions are standard in neutrino literature; use the numbers collected here to keep consistency with existing code that uses $K=1.267$.

**DM sector (Dark Matter) — math and code mapping**

- Physics motivation: a coherent background scalar (or axion-like) field or a localized dark-matter density can modulate neutrino effective masses or induce scattering. In the simplest toy model one may treat the DM background as producing a spatially-varying mass-squared modulation in the mass basis together with a slow scattering-induced population relaxation.

- Mass-modulation model (used in `dm_sector.py`):
  - Mass-basis modulation amplitude (eV^2) with optional spatial oscillation:
    $$\delta M^2_{\rm DM,mass}(L,E) = A_{\rm amp}(E)\,\cos(\omega L + \phi)\;\sigma_z^{({\rm mass})},$$
    where $\sigma_z^{(\rm mass)}=\mathrm{diag}(1,-1)$ is used as a simple two-flavor generator and $A_{\rm amp}(E)$ is an amplitude with units eV^2.
  - The wrapper converts this to a flavor-basis Hamiltonian via the standard factor
    $$H_{\rm DM}^{\rm flav}(L,E)=K\frac{1}{2E_{\rm GeV}}\;U\,\delta M^2_{\rm DM,mass}(L,E)\,U^\dagger,$$
    with $K=1.267$ and $U(\theta)$ the two-flavor mixing matrix.

- Mapping local DM density to amplitude (code contract):
  - We adopt a simple linear toy mapping implemented in `dm_density_to_amplitude(rho_{\rm DM},g,E)`:
    $$A_{\rm amp}(E)\equiv g\;\frac{\rho_{\rm DM}[\mathrm{GeV/cm^3}]\times(1\ \mathrm{GeV/cm^3}\to\mathrm{eV}^4)}{E_{\rm GeV}},$$
    where the code uses the numeric conversion $1\ \mathrm{GeV/cm^3}\approx1.7827\times10^{-6}\ \mathrm{eV}^4$.
  - Thus the implemented mapping is
    $$A_{\rm amp}(E)=g\;\frac{\rho_{\rm DM}\times1.7827\times10^{-6}}{E_{\rm GeV}}\quad(\mathrm{eV}^2\;\text{units}).$$
  - Rationale: this keeps amplitudes physically small for plausible couplings $g$ and avoids numerical overflows when those couplings are not astrophysically large.

- Scattering-induced damping (toy population relaxation):
  - A simple dissipator implemented in `dm_sector.py` relaxes populations toward an equal-split target at rate $\gamma_s$ (units 1/km):
    $$\mathcal{D}_{\rm DM}[\rho]_{ii} = -\gamma_s\big(\rho_{ii}-\tfrac12\mathrm{Tr}(\rho)\big),\qquad \mathcal{D}_{\rm DM}[\rho]_{i\ne j}=0.$$ 
  - This preserves trace while damping population differences; it is a parametric, positivity-preserving approximation for weak scattering. For strict Lindblad form one would derive appropriate jump operators and rates from microphysics.

- Implementation notes / sanity checks:
  - Use small, physically motivated couplings (or an environment variable `DM_TEST_COUPLING` in tests) when exercising the mapping numerically to avoid overflow in the integrator.
  - The `UnifiedGKSL` wrapper will rotate the mass-basis matrix into flavor basis and apply the $K/(2E)$ factor automatically; sector authors should therefore return a mass-basis matrix in eV^2 units.
  - If the sector produces rapidly varying spatial structure (large $\omega$), ensure integrator step size is small enough to resolve the modulation or prefer an adaptive integrator.

- Addendum: the current toy implementation in `integration_artifacts/mastereq/dm_sector.py` follows these conventions exactly — see `dm_density_to_amplitude`, `make_dm_mass_modulation`, and `make_dm_scattering_damping` for the concrete code mapping.
