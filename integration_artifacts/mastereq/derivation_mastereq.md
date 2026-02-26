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

**LIGO / Gravitational sector (added)**

- Motivation: gravitational waves or local variations in the metric can be represented in toy models as tiny, spatially dependent modifications to the effective neutrino mass-squared matrix. The code provides a minimal mapping so that gravitational-sector contributions can be registered as mass-basis or flavor-basis terms.

- Toy mass-basis modulation (eV^2 units):
  $$\delta M^2_{\rm LIGO,mass}(L,E)=A_{\rm LIGO}(E)\,\cos(\omega_g L+\phi)\;\sigma_z^{(\rm mass)}$$
  where $A_{\rm LIGO}(E)$ is the small amplitude (eV^2), $\omega_g$ is spatial frequency (1/km), and $\sigma_z^{(\rm mass)}=\mathrm{diag}(1,-1)$.

- Flavor-basis Hamiltonian (1/km units):
  $$H_{\rm LIGO}^{\rm flav}(L,E)=K\frac{1}{2E_{\rm GeV}}\,U\,\delta M^2_{\rm LIGO,mass}(L,E)\,U^{\dagger},\qquad K=1.267.$$ 

- Example mapping guidance:
  - Choose $A_{\rm LIGO}$ many orders of magnitude below vacuum splittings for conservative tests (e.g. $A_{\rm LIGO}\lesssim10^{-12}\text{--}10^{-6}\,$eV^2 depending on physics assumptions).
  - If a strain-based model supplies a dimensionless strain $h(L)$ and a coupling $g_h$, a simple model is
    $$A_{\rm LIGO}(E)\sim g_h\,h(L)\,M_0^2,$$
    where $M_0^2$ is a characteristic model mass-squared scale; document these choices when registering a sector.

- Toy dissipator: population relaxation at rate $\gamma_g$ (1/km)
  $$\mathcal{D}_{\rm LIGO}[\rho]_{ii}=-\gamma_g\big(\rho_{ii}-\tfrac12\mathrm{Tr}(\rho)\big),\qquad \mathcal{D}_{\rm LIGO}[\rho]_{i\ne j}=0.$$ 

- Implementation notes:
  - Return mass-basis matrices in eV^2 via the `add_mass_sector(...)` API; `UnifiedGKSL` handles conversion to 1/km and rotation.
  - If the model naturally provides flavor-basis Hamiltonians in physical units, register them with `add_flavor_sector(...)` already in 1/km.
  - For rapid spatial variation use smaller integrator steps or an adaptive integrator.

This LIGO subsection is intentionally minimal and mirrors the DM toy approach; extend with model-specific derivations and Lindblad jump operators when available.

**Compact master-equation (GKSL) one-liner**

Add this concise GKSL form when referencing the overall master-equation in papers or summaries:

$$\frac{d\rho}{dL} = -i\,[H(L,E),\rho] + \sum_a \gamma_a\Big(L_a\,\rho\,L_a^{\dagger} - \tfrac{1}{2}\{L_a^{\dagger}L_a,\rho\}\Big)$$

Short note: here $L$ is distance (km), $H(L,E)$ is the total Hamiltonian in $\mathrm{km}^{-1}$, and $\{L_a\}$ are Lindblad jump operators with nonnegative rates $\gamma_a$. The first term is Hamiltonian (coherent) evolution and the second term encodes dissipative (GKSL) effects.

**MSW sector — Lindblad (GKSL) dissipator derivation**

- Objective: replace ad-hoc off-diagonal damping by an explicit GKSL Lindblad operator that implements pure dephasing while preserving complete positivity.

- Start from the GKSL form for a single jump operator $L$ with rate already absorbed into $L$:
  $$\mathcal{D}[\rho]=L\rho L^{\dagger}-\tfrac12\{L^{\dagger}L,\rho\}.$$ 

- Choose a Hermitian operator proportional to $\sigma_z$ in flavor basis:
  $$L=\sqrt{\frac{\gamma}{2}}\,\sigma_z,\qquad \sigma_z=\begin{pmatrix}1&0\\0&-1\end{pmatrix}.$$ 

- Compute $L^{\dagger}L=(\gamma/2)\,\sigma_z^2=(\gamma/2)I$. Therefore
  \begin{align*}
  \mathcal{D}[\rho]&=\frac{\gamma}{2}\left(\sigma_z\rho\sigma_z-\tfrac12\{I,\rho\}\right)
  =\frac{\gamma}{2}(\sigma_z\rho\sigma_z-\rho)\\
  &\Rightarrow (\mathcal{D}[\rho])_{ij}=\begin{cases}0,& i=j,\\ -\gamma\,\rho_{ij},& i\ne j,\end{cases}
  \end{align*}
  which damps off-diagonal coherences at rate $\gamma$ while leaving populations and trace unchanged.

- Code mapping: implement the GKSL formula directly in `ms_sector.py` using
  ```python
  L = np.sqrt(gamma/2) * np.array([[1,0],[0,-1]], dtype=complex)
  D = L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)
  ```

**LIGO sector — master-equation completion notes**

- To complete the mathematical integration on the LIGO side, document how toy population-relaxation dissipators map to GKSL operators and provide a Lindblad alternative where appropriate.

- Population relaxation toward the maximally mixed state at rate $\gamma_g$ (toy model)
  $$\mathcal{D}_{\rm pop}[\rho]_{ii}=-\gamma_g(\rho_{ii}-\tfrac12\mathrm{Tr}\rho)$$
  can be generated by a pair of jump operators that move population between the two flavor states. One convenient GKSL construction is to use raising/lowering-type operators
  $$L_1=\sqrt{\frac{\gamma_g}{2}}\,|0\rangle\langle1|,\qquad L_2=\sqrt{\frac{\gamma_g}{2}}\,|1\rangle\langle0|,$$
  which produce both population exchange and additional dephasing terms. Explicitly,
  $$\mathcal{D}[\rho]=\sum_{k=1}^2\Big(L_k\rho L_k^\dag-\tfrac12\{L_k^\dag L_k,\rho\}\Big)$$
  yields relaxation of populations toward equal populations while preserving trace and complete positivity. Tune coefficients if a different equilibrium is desired.

- Implementation guidance:
  - If you prefer the simpler toy relaxation used in code, it is acceptable for exploratory tests; document its assumptions and limitations in the sector README.
  - For strict GKSL fidelity, replace the toy population-relaxation with the pair of jump operators above (or other operators derived from microphysics), and implement the GKSL formula in `make_ligo_damping`.

Add these derivations to the MS and LIGO subsections in the file and ensure the code implements the GKSL formula as shown.

**Relation to the Standard Model and other frameworks (per-sector)**

This section summarizes where the sector mappings implemented in the code align with Standard-Model (SM) physics, where they represent beyond-SM (BSM) hypotheses, and what additional derivations or math would be required to move from the present toy/Lindblad implementations to fully microphysical descriptions.

- **Weak / MSW:**
  - SM relation: direct — MSW potential arises from coherent forward charged-current scattering on electrons within the SM. The usual expression $V_e\simeq\sqrt{2}G_F N_e$ is derived from SM Feynman amplitudes in the low-momentum-transfer limit.
  - What we implement: the flavor-diagonal potential and its unit conversions are SM-consistent; the GKSL dephasing operator we use is a phenomenological choice and must be derived from microphysics (collision integrals) if a SM-based dissipator is desired.
  - To rigorously match SM: derive dissipative kernels from finite-temperature field theory or Boltzmann/QKE limits (compute scattering rates $\gamma\sim n\sigma v$ and, if necessary, Lindblad operators from system–bath couplings using Born–Markov approximations).

- **Strong sector:**
  - SM relation: partial — strong-interaction effects (coherent forward scattering on nucleons, nuclear medium modifications) can modify effective mass terms; these are in-principle derivable from SM QCD matrix elements, but usually treated via nuclear/phenomenological models.
  - What we implement: a toy mass-basis modulation and a population-relaxation term; these are phenomenological placeholders.
  - To connect to SM: compute coherent forward-scattering amplitudes in the relevant medium (nuclear response functions) or map hadronic physics into effective potentials used in the master equation.

- **EM (magnetic-moment) sector:**
  - SM relation: neutrino magnetic moments are extremely small in minimal SM with massive neutrinos (loop-suppressed). Large magnetic moments imply BSM physics.
  - What we implement: an off-diagonal coupling proportional to $\mu_\nu B$ (toy); damping is phenomenological.
  - To make microphysical: if a BSM model predicts an enhanced $\mu_\nu$, compute radiative corrections and scattering-induced dissipators from photon/neutrino interactions to derive Lindblad rates.

- **DM (Dark Matter) sector:**
  - SM relation: none (BSM) — DM-induced mass-modulation or scattering is outside SM and must be motivated by a specific DM model (scalar background, axion-like coupling, vector mediator, etc.).
  - What we implement: a simple mapping from local DM density to a mass-squared modulation and a toy scattering-induced relaxation. This is explicitly model-dependent and meant for exploratory comparisons.
  - To be microphysical: choose a DM model, derive the effective Hamiltonian and collision terms (from the DM–neutrino interaction Lagrangian), and compute jump operators and rates from the S-matrix or effective interaction potential.

- **MS (Matter-sector / Earth-like density):**
  - SM relation: identical to Weak sector for the coherent potential; the GKSL Lindblad dephasing we added is phenomenological and should be derived using SM scattering rates to ensure quantitative match.
  - What we implemented: MSW potential + GKSL dephasing (sigma_z) as the minimal CP-preserving dephasing channel.
  - To improve: compute electron scattering cross-sections and in-medium correlators to derive $\gamma$ and possible non-Markovian corrections.

- **LIGO / gravitational-sector:**
  - SM relation: none (BSM/gravitational) — metric perturbations and gravitational-wave backgrounds lie in the gravity sector; how they couple to neutrino flavor/mass depends on the gravity–neutrino coupling model.
  - What we implement: toy mass-basis modulation and a GKSL pair of jump operators for population exchange (now implemented with tunable equilibrium). This is a phenomenological mapping to assess sensitivity.
  - To be microphysical: specify the coupling (e.g., minimal-coupling metric perturbation, nonminimal couplings, or new scalar degrees of freedom), compute induced effective potential or transition amplitudes, and derive dissipative terms from interaction with a stochastic gravitational bath if applicable.

**Where new physics, new mathematics, or new approaches appear**

- New physics (BSM) areas in the code:
  - DM sector (explicit beyond-SM interactions mapping to mass modulation or scattering).
  - EM sector if neutrino magnetic moments are taken larger than SM predictions.
  - LIGO sector (gravitationally induced modifications) — requires hypothesis about gravity–neutrino coupling beyond minimal GR.

- New mathematics / numerical approaches used here (relative to standard oscillation calculations):
  - GKSL master-equation framework: retains coherence and open-system dissipation; needs Lindblad operators and rates consistent with microphysics.
  - Lindblad operator construction vs. direct dissipator parametrization: we favor explicit GKSL when possible to guarantee complete positivity; constructing these from first principles requires Born–Markov derivations or projection-operator techniques (Nakajima–Zwanzig).
  - Unit conversions and basis rotations: mapping mass-basis amplitudes (eV^2) to Hamiltonian units (1/km) with the $K/(2E)$ factor is an essential numeric step that couples particle-physics parameters to solver units.
  - Numerical stability and step-size constraints: rapidly varying mass modulations or large amplitudes require smaller integration steps or adaptive solvers to avoid numerical artifacts (we use RK4 with step control via `steps` argument).

- New methodological steps you may want to pursue for rigor:
  1. For any dissipative channel intended to represent SM physics, derive Lindblad operators and rates from the microscopic interaction Lagrangian using standard open-quantum-system derivations (Born–Markov, secular approximations), and validate the Markovian assumption.
  2. For regimes where memory effects matter, use non-Markovian master equations (Nakajima–Zwanzig) or full quantum kinetic equations (Kadanoff–Baym) rather than GKSL.
  3. When mapping BSM hypotheses (DM, enhanced $\mu_\nu$, gravitational couplings), clearly document the assumed Lagrangian and the approximations used to produce the effective Hamiltonian and dissipator.

If you want, I can now:
- insert explicit example formulas connecting scattering cross section $\sigma$ and density $n$ to a GKSL rate $\gamma\sim n\sigma v$ (with unit conversion to 1/km), and
- add references (e.g., reviews on open quantum systems, MSW derivations, QKE/Nakajima–Zwanzig papers) to the derivation file.

**Microphysical scaffolding now implemented in code**

To continue from the previous “placeholder/default” status, the integration code now provides an explicit shared microphysics layer in `mastereq/microphysics.py` and optional per-sector `use_microphysics=True` switches.

- Shared rate conversion:
  $$\Gamma = n\sigma v\quad [\mathrm{s}^{-1}],\qquad \gamma = \Gamma/c\quad [\mathrm{km}^{-1}]$$
  implemented as `gamma_km_inv_from_n_sigma_v(...)`.

- Weak/MS approximations:
  - $\sigma(\nu_e e)\approx 9.2\times 10^{-45} E_{\rm GeV}\,\mathrm{cm}^2$
  - $\sigma(\nu_\mu e)\approx 1.57\times 10^{-45} E_{\rm GeV}\,\mathrm{cm}^2$
  - $n_e\approx \rho\,Y_e\,N_A$ for medium conversion in MS.

- EM approximation:
  - template scaling for magnetic-moment induced scattering
    $$\sigma_{\rm EM}\sim 10^{-45}\left(\frac{\mu_\nu}{10^{-11}\mu_B}\right)^2 E_{\rm GeV}\,\mathrm{cm}^2.$$

- DM approximation:
  - reference template
    $$\sigma_{\rm DM}\sim 10^{-46}\left(\frac{g}{10^{-6}}\right)^2 E_{\rm GeV}\,\mathrm{cm}^2.$$

- LIGO/gravity approximation:
  - reference effective template
    $$\sigma_{g}\sim 10^{-50} h^2 E_{\rm GeV}\,\mathrm{cm}^2.$$

These are now wired into the sector APIs as optional paths. If `use_microphysics=False`, the code keeps fixed defaults for backward compatibility and stable regression tests.

Important: these are still controlled approximations/templates, not full first-principles QFT derivations for each model. Full microphysical closure still requires model-specific amplitudes, medium response functions, and (where needed) non-Markovian analysis.

Validation note:
- The WEAK “golden CSV” equivalence checks validate the runner’s exported **unitary phase-map** ($H$-side) against GKSL (see `integration_artifacts/EQUIVALENCE_CHECKS.md`).
- Microphysics-derived $\,n\sigma v\to\gamma\,$ wiring is validated separately by GKSL-side unit tests that show `use_microphysics=True` produces identical evolution to supplying the same $
  \gamma$ explicitly (this is distinct from runner equivalence, since the runners typically do not export a $
  \gamma$-sensitive observable).

**Fixed defaults used in code (global placeholders)**

To keep all sectors consistent when parameters are not provided, the code now uses
a fixed global default rate and a helper for turning $n,\sigma,v$ into a GKSL rate:

- Collision-rate estimate (in s$^{-1}$):
  $$\Gamma = n\,[\mathrm{cm^{-3}}]\;\sigma\,[\mathrm{cm^{2}}]\;v\,[\mathrm{cm\,s^{-1}}].$$

- Convert to per-length units for the solver ($L$ in km):
  $$\gamma\,[\mathrm{km^{-1}}] = \frac{\Gamma}{c_{\rm km/s}},\qquad c_{\rm km/s}=2.99792458\times10^{5}.$$

- Default placeholders (documented in `mastereq/defaults.py`):
  - $\gamma_{\rm default}=10^{-6}\,\mathrm{km^{-1}}$
  - $n=10^{23}\,\mathrm{cm^{-3}}$,
  - $\sigma=10^{-44}\,\mathrm{cm^{2}}$,
  - $v=3\times10^{10}\,\mathrm{cm\,s^{-1}}$.

These are **placeholders for numerical stability**, not microphysical predictions. Replace them with model-specific values as needed.

---

## Complete hook-to-master-equation map (code ↔ math)

This section is the “no-ambiguity” mapping for every currently integrated sector hook.

### Core wrapper contract (`unified_gksl.py`)

- Total equation solved:
  $$
  \frac{d\rho}{dL}=-i[H_{\rm vac}+\sum_s H_s,\rho] + \sum_s \mathcal D_s[\rho].
  $$
- `add_mass_sector(fn)` expects `fn(L,E)` returning 2×2 mass-basis $\delta M_s^2$ in eV$^2$.
  Wrapper applies
  $$
  H_s=K\frac{1}{2E}U\,\delta M_s^2\,U^\dagger\quad (\mathrm{km}^{-1}).
  $$
- `add_flavor_sector(fn)` expects `fn(L,E)` already in flavor basis and in km$^{-1}$.
- `add_damping(fn)` expects `fn(L,E,\rho)` returning additive dissipator matrix.

### Sector-by-sector technical mapping

1. **Weak (`weak_sector.py`)**
   - Coherent term: flavor-diagonal matter potential $\mathrm{diag}(V_e,0)$ in km$^{-1}$.
   - Optional damping: off-diagonal dephasing
     $$D_{01}=-\gamma\rho_{01},\;D_{10}=-\gamma\rho_{10}.$$
   - Microphysics switch: `use_microphysics=True` derives $\gamma$ from $n\sigma v$ using weak $\nu e$ templates.

2. **MS (`ms_sector.py`)**
   - Coherent term: MSW-like flavor potential.
   - Dissipator: explicit Lindblad dephasing using $L\propto\sigma_z$ (CP-safe pure dephasing channel).
   - Microphysics switch: derives $\gamma$ from medium density conversion + weak template cross section.

3. **EM (`em_sector.py`)**
   - Coherent term: off-diagonal magnetic coupling $H\propto\mu_\nu B\,\sigma_x$.
   - Dissipator: dephasing template (or explicit fixed gamma).
   - Microphysics switch: derives $\gamma$ via magnetic-moment template cross section.

4. **Strong (`strong_sector.py`)**
   - Coherent term: toy mass-basis modulation (typically $\sigma_z$-like structure in mass basis).
   - Dissipator: toy population-relaxation/decoherence channel (trace-preserving by construction).

5. **DM (`dm_sector.py`)**
   - Coherent term: density/coupling-driven $\delta M^2_{\rm DM}(L,E)$ in mass basis.
   - Dissipator: population-relaxation style scattering approximation.
   - Microphysics switch: derives scattering-rate gamma from DM template cross section.

6. **LIGO / gravity (`ligo_sector.py`)**
   - Coherent term: tiny oscillatory mass-basis modulation.
   - Dissipator: Lindblad pair (exchange/relaxation form) or equivalent toy mode.
   - Microphysics switch: effective gravity-bath template cross section to gamma.

7. **Entanglement (`entanglement_sector.py`)**
   - Dissipator hook: off-diagonal dephasing template (GKSL-compatible approximation path).
   - Diagnostic bridge map: CHSH visibility template
     $$|S|(L)=S_0\,e^{-\gamma L}$$
     used as a controlled phenomenological link between decoherence and Bell-violation magnitude.
   - Microphysics switch: `sigma_entanglement_reference_cm2(E,visibility)` + $n\sigma v\to\gamma$.

8. **Photon/birefringence (`photon_sector.py`)**
   - Dissipator hook: off-diagonal dephasing template.
   - Added deterministic math mirrors for prereg runners:
     - CMB lock test (single-point locked-$C_\beta$ z-score rule),
     - FRW accumulation integral
       $$I(z)=\int_0^z\frac{dz'}{(1+z')E(z')}$$
       and locked prediction transfer to holdout.
   - Microphysics switch: `sigma_photon_birefringence_reference_cm2(E,coupling_x)` + $n\sigma v\to\gamma$.

---

## What is exact vs what is scaffold (strict boundary)

To prevent interpretational drift:

- **Exact in this repo (deterministic):**
  - code-path contracts and unit conversions,
  - GKSL numerical integration behavior,
  - runner declared-math equivalence tests (golden/independent reimplementation checks),
  - reproducible command outputs for the checked panels.

- **Not yet exact (still scaffold/template):**
  - full first-principles microphysical derivation of all sector dissipators,
  - sector-specific QFT amplitudes + medium response + Markov/secular justification end-to-end,
  - non-Markovian closure where required by physics regime.

In other words: current `microphysics.py` gives consistent and testable $n\sigma v\to\gamma$ wiring, but does **not** claim universal first-principles completion.

---

## Exact-derivation completion recipe (implementation-grade)

For any target sector, the required closure chain is:

1. Fix interaction model (SM or explicit BSM Lagrangian).
2. Derive matrix element $\mathcal M$ and cross section/rate kernels.
3. Compute medium averages (distribution-weighted rates and correlation times).
4. Derive reduced dynamics (Born-Markov + secular checks explicitly documented).
5. Express resulting generator in Lindblad form (or justify non-GKSL form if needed).
6. Map coefficients to km$^{-1}$ solver units and add numerical regression tests.
7. Validate physical limits:
   - positivity,
   - trace conservation,
   - SM/no-new-physics limit,
   - stability under step-size refinement.

No sector should be labeled “microphysical exact derivation complete” unless all seven are satisfied and evidenced by tests/docs.

---

## Reproducibility checklist (current repo state)

- Full integration tests:
  - `python -m pytest -q integration_artifacts/mastereq/tests`
- Current validated snapshot in this branch/session: **37 passed**.
- New bridge equivalence tests included in this count:
  - entanglement runner equivalence,
  - photon/birefringence runner equivalence.

This checklist is intentionally duplicated in high-level docs so readers can verify status without searching through commit history.

---

## Appendix: sector-by-sector runner reference map

This derivation file focuses on equation-level mapping. For reproducible runner paths,
use this quick index (canonical source remains `tools/verdict_commands.txt`):

- EM (Bhabha): `em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py`
- EM (mu-mu): `em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.py`
- Weak/oscillation: `nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py`, `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py`
- Strong: `strong_sigma_tot_energy_scan_v2.py`, `strong_rho_energy_scan_v3.py`
- DM: `dm_holdout_cv_thread_STIFFGATE.py`, `dm_holdout_cv_thread.py`
- LIGO/GW: `improved_simulation_STABLE_v17_xy_quadrupole_drive_ANISO_PHYS_TENSOR_PHYS_FIXED4.py`
- Entanglement/Photon bridge:
  - `integration_artifacts/entanglement_photon_bridge/audit_nist_coinc_csv_bridgeE0_v1_DROPIN.py`
  - `integration_artifacts/entanglement_photon_bridge/run_prereg_cmb_birefringence_v1_DROPIN_SELFCONTAINED.ps1`
  - `integration_artifacts/entanglement_photon_bridge/run_prereg_birefringence_accumulation_v1_DROPIN_SELFCONTAINED_FIX.ps1`

Cross-check files:
- equivalence scope and evidence: `integration_artifacts/EQUIVALENCE_CHECKS.md`
- golden rerun orchestration: `integration_artifacts/scripts/verdict_golden_harness.py`
