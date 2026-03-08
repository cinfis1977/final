# Unified Equation (GKSL) Geometric Modulation (one-for-all implementation) - Ahmet Özbalık - research notes and current performance runbook - Weak, EM, Strong, Dark Matter, GW (LIGO), Mass Spectrometry, Entanglement (CHSH), Photon (birefringence/decay) - current performance scoreboard: WEAK / STRONG / DM / MS / LIGO = performance pass; EM = not established

**One-for-all implementation (what this means):** this draft uses a single **locked** base parameterization (a small set of “physical” knobs) plus a **deterministic sector map** that generates each sector’s runner parameters from that same base. The intent is to avoid per-sector tuning and make cross-sector checks auditable: if the base and map are fixed, each sector run is a reproducible consequence of the same upstream choices.

> This is a falsification-first, preregistered working-paper draft: the pipeline and artifacts are provided end-to-end, and the strongest results are clearly separated from follow-up tests.

> **Scope / status (read carefully).**
> This document is a **falsification-first, preregistered** research synthesis for the unified-equation / gauge-geometry program. In the current revision, the explicit **performance-scored sectors** are weak, strong, dark matter, gravitational-wave (LIGO), and mass spectrometry; **EM is included as a tested but currently non-passing branch**. The **entanglement** and **photon-decay / propagation** lines remain bridge/audit tracks and are **not part of the current performance scoreboard**.
> 
> **Real-data mass-spectrometry (new):** we include a **fit-free, preregistered** analysis of **real Bruker/CompassXport-exported mzML** full-scan runs to test **setting-conditioned separation** and a **multi-target target-specific signature** under a locked success threshold (`good_ppm=3`) with holdout + third-arm consistency.

> **Headlines (mass-spectrometry sector).**
> **A) real Bruker mzML (target-specific; fit-free prereg performance pass):** Using CompassXport-exported, full-scan mzML runs, a scan-resolved pipeline produces per-scan mass estimates and a normalized ion-load proxy $g$. A multi-target “target-specific” test with a locked success threshold **`good_ppm=3`** yields a preregistered **performance pass** with strong holdout + third-arm stability (see §4.9.10 and the signed artefacts under `out/particle_specific_final_goodppm3_lock/`).

> **Important scope note (data provenance).** The Mass Spectrometer section below is based on **real instrument exports (mzML)** and is evaluated under a **preregistered lock**; earlier toy demonstrations are intentionally omitted in this version to keep the write-up fully aligned with the current, real-data pipeline.
> - **real mzML addendum:** Bruker/CompassXport‑exported, full‑scan mzML runs analyzed fit‑free under a locked prereg gate (good_ppm=3) to test setting-conditioned separation and target‑dependent “target-specific” structure.
>
> In several evaluation tables, “SM” is a **legacy label for a frozen baseline/no‑correction reference** (it does **not** refer to the particle‑physics Standard Model).
>

>
> The broader program also includes **GW/LIGO ringdown** and **DM/SPARC** modules implemented under the same preregistered discipline, but those sectors are **only summarized** here (the detailed write-ups/log bundles are not embedded in this draft).
>
> Throughout, the paper-level labels are now **performance-facing**: **performance pass** means the declared preregistered performance criterion is met on the stated real-data branch; **not established** means the tested branch does not clear that criterion; **not scored here** means the line is kept for context but is outside the current performance scoreboard. **TENSION** still flags sensitivity to conditioning / baseline / covariance choices that motivates the next preregistered checks.

> **Revision note (entanglement + photon integration into the unified-equation program).**  
> In this revision, the entanglement (CHSH/NIST audit) and photon (decay/birefringence) analyses are treated not as isolated add-ons but as sectors of the same cross-sector open-system program used elsewhere in the project. The paper now records the project-level integration chain explicitly: (i) a shared GKSL-style **unified-equation** sector insertion contract, (ii) an optional microphysics bridge $n\,\sigma\,v \rightarrow \gamma$, and (iii) independent equivalence tests confirming that the declared mathematics is wired consistently into the runner implementations. A new **Sector Hook Map** subsection further lists the sector-level observables, $H_s/\mathcal D_s$ roles, microphysics candidates, runner/test anchors, and validation status (validated vs scaffolding) so the integration can be checked sector by sector.


## Performance scoreboard and criteria (current)

This paper uses **performance pass** only for sectors where a **preregistered, quantitative** performance criterion is satisfied on the stated real-data branch (against a frozen baseline / null). All other tracks are labeled **not established** or **not scored here**.

**Performance-scored sectors (current revision)**

- **WEAK (NOvA + MINOS + T2K penalty):** performance score is  
  `TOTAL = dχ²_NOvA + dχ²_MINOS − (T2K penalty)` and must be **> 0** at the locked point.  
  Current locked run: `dχ²_NOvA = −0.123`, `dχ²_MINOS = +1.005`, `T2K penalty = 0.392623` → **TOTAL = 0.489377** (**performance pass**).

- **STRONG (PDG σ_tot + ρ):** performance score is `Δχ²_total = Δχ²(σ_tot, pp+p̄p) + Δχ²(ρ, both)` and must be **> 0** at the locked point.  
  Current locked run: `Δχ²(σ_tot) = +3.235630 + 0.209162`, `Δχ²(ρ) = −0.655891` → **Δχ²_total ≈ +2.788901** (**performance pass**).

- **DM (SPARC/RAR):** performance criterion is cross-validated improvement stability: `telemetry.all_folds_delta_test_positive = true` under locked `A, α, kfold, seed` (**performance pass**).

- **MS (real mzML target-specific):** preregistered **locked gate** `good_ppm=3` with holdout + third-arm stability criteria **C1–C3** (see §4.9.10/§4.9.14). When all criteria are true, verdict is **performance pass**.

- **LIGO (GW170814 ringdown-only null):** performance criterion is **small offsource probability** for the declared correlation statistic (the canonical “EXACT” branch uses `p_abs_corr` and `p_min_abs_corr` with joint statistic `p_joint_abs_and_minabs`). The recorded canonical reference run has `p_joint_abs_and_minabs = 0.0`, `p_abs_corr ≈ 0.0295`, `p_min_abs_corr ≈ 0.0435` (**performance pass**).

**Not established (performance)**

- **EM (LEP Bhabha, LEP μμ):** tested branches yield `Δχ² = 0` at the locked runs (no measured performance advantage over the declared baseline), so **performance is not established** in this revision.

**Not scored here (kept for context / audits)**

- **Entanglement (CHSH/NIST audit)** and **photon/birefringence** remain bridge/audit tracks in this revision and are **not part of the current performance scoreboard**.


## Project brief and current claim boundary (reader-facing)

This project is a falsification-first, cross-sector open-system program. A single locked mathematical skeleton (the unified GKSL-style equation plus a deterministic sector map) is reused across weak, EM, strong, dark matter, gravitational-wave, mass-spectrometry, entanglement, and photon bridge tests. The practical goal is not to declare a universal proof from one dataset family, but to carry forward only the submodules that survive locked, fit-free, real-data tests under explicitly stated limits.

**Current status boundary (important):**

- This draft does **not** claim that the full model is physically proven.
- It **does** claim that several sector-level components survive the current internal falsification tests under locked conditions.
- Broader physical claims, cross-domain claims, or direct-observable claims require additional independent real data and, in some sectors, more direct observables than the present proxy layers.

**Mass-spectrometry addendum status in this revision:**

- The canonical real-mzML target-specific preregistered test remains the primary Mass Spectrometer result in this paper.
- In addition, a single-center occupancy-gate extension and a two-center diagnostic-boundary extension now survive current locked internal checks on the same real-data family.
- These are carried below as constrained working components of the unified-equation framework, not as proof-complete physical claims.

### Scope and interpretation note (reviewer-facing)

This revision intentionally uses **unified equation** terminology (formerly “master equation”) and keeps the claims conservative:

- The **geometric substrate → sector operator** step is currently a **structured bridge map** (declared and tested), **not** a first-principles derivation from substrate coordinates.
- The **CT/RT dual-tension split** is a working geometric rule used across sectors; a full dimensional-limit derivation (e.g., Coulomb/Newtonian limits) is future work.
- The **microphysics hook** $\Gamma=n\sigma v$, $\gamma=\Gamma/c$ is a shared wiring/scaffolding layer. It is validated as code-to-math plumbing, but not claimed as a completed universal derivation.
- The **entanglement line** is a **Bell-audit / pipeline validation** on a known Bell-violating dataset (plus unified-equation hooks), not a first-principles Bell-violation derivation from the substrate.
- The **photon/birefringence line** is a preregistered **scaffolding/falsification testbed** (accumulation law + bridge wiring), not a final calibrated cosmic birefringence parameter extraction.
- Status labels in this paper are **performance-facing**: **performance pass** means the declared preregistered performance criterion was met on the stated real-data branch; **not established** means the tested branch did not clear that criterion; **not scored here** means the line is retained for context but is outside the current performance scoreboard.

## Physical picture of the model (read this first)

This section is deliberately **visual**. The goal is that a reader can “play the model like an animation” in their head before seeing any equations.

> **Not metaphor, mechanism (“engine-room” rule).** Throughout this draft, words like *thread*, *junction*, *jitter*, *lock plane*, *gate*, and *route–register* are used as **literal elements of a discrete substrate protocol**, not as poetic stand-ins for continuum fields. “Jitter” is not an externally injected random noise term; it refers to a reproducible timing/phase mismatch produced by distinct transport paths on the lattice.

### Project-level integration status (unified equation → microphysics → tested runners)

This paper now reflects a repository-level milestone: the entanglement and photon sectors are integrated into the same *sector-pluggable* unified-equation workflow that is used for weak, EM, strong, DM, and LIGO analyses. In practical terms, the project now has a **three-layer bridge** from concept to code. To remove ambiguity for readers, a **sector-by-sector hook map** (including microphysics candidates and validation status) is also included below in the mathematical framework section:

1. **Common cross-sector unified equation (shared contract).**  
   Sector contributions are inserted into one open-system evolution skeleton,
$$
   \frac{d\rho}{dL}
   =-i\!\left[H_{\mathrm{vac}}+\sum_s H_s,\rho\right]
   +\sum_s \mathcal{D}_s[\rho],
$$
   where each sector $s$ contributes a coherent piece $H_s$ and/or a dissipative/Lindblad piece $\mathcal{D}_s$.  
   In the codebase, this is the common interface carried by the unified GKSL layer (e.g. `unified_gksl.py`, `gk_sl_solver_clean.py`, and the derivation notes in `derivation_mastereq.md`), with sector modules following the same insertion logic (`weak_sector.py`, `ms_sector.py`, `em_sector.py`, `strong_sector.py`, `dm_sector.py`, `ligo_sector.py`, `entanglement_sector.py`, `photon_sector.py`).

2. **Microphysics bridge (optional, auditable scaling).**  
   Instead of treating damping rates as only fixed toy constants, the project now supports an optional *microphysics scaffolding*:
$$
   \Gamma_s = n_s\,\sigma_s\,v_s,
   \qquad
   \gamma_s = \Gamma_s/c.
$$
   This is implemented as a controlled conversion layer (`microphysics.py`, `defaults.py`) and can be switched on sector-by-sector via `use_microphysics=True`.  
   Importantly, this paper does **not** claim that a complete first-principles derivation is finished for every sector. The claim is narrower and stronger: the bridge is a **consistent, inspectable, and test-validated wiring layer** from microphysical scales to the unified-equation damping channel.

3. **Equivalence verification (declared math ↔ runner code).**  
   The project now includes explicit equivalence tests to answer the crucial question: *Was the mathematics transferred to the runners correctly?*  
   Two classes of tests are used:

   - **Declared-math runner equivalence tests:** independent reimplementations reproduce runner outputs (golden/equivalence checks).
   - **Microphysics wiring equivalence tests:** `use_microphysics=True` must match the evolution obtained by injecting the same $\gamma$ explicitly from outside.

   This is the key quality-control step for the entanglement + photon additions: the new sectors are not only described mathematically, but also checked against the actual executable runners.

A practical implication for the entanglement sector is that the **canonical evidence path** remains the NIST run4 HDF5-export coincidence workflow (the one that yields the CHSH violation result used in this paper), while the prescreen CSV “Bridge-E0” slot-fix audit is documented as a format/mapping incompatibility case (producing the trivial $S=-2$ artifact) and is therefore excluded from final evidence claims. This prevents over-claiming and keeps the entanglement conclusion tied to the validated data chain.

On the photon side, the same integration logic now covers both the photon-decay-style dissipative interpretation and the birefringence/redshift-accumulation prereg pathway: the formulas are locked, the sector plugs into the same unified-equation architecture, and the runner-level equivalence checks confirm consistency with the declared mathematics.

### Visual summary (what the “unit cell” and the “junction” literally are)

> These are **schematic** drawings used to communicate the substrate protocol. They are not fits, not inferred geometry, and they are not meant to be scale-accurate.

![Single cube unit cell: threaded edges, inner bubble threads, and a central amorphous bubble.](figs/Fig-0_single_cube.png)

**Figure V0 (Single cell).** One cube (“unit cell”) as used throughout the model. The cube edges are tensioned threads. Inside, additional threads connect the boundary to the **central amorphous bubble** (a localized excitation of an **auxiliary field / extra DOF layer**). These internal threads represent multiple transport channels (edge-fast vs bulk-slow) and allow partial reflection/backflow at junctions.

![Dual-cube junction: two adjacent unit cells with 16 inter-cube junction threads (corner↔corner bus) between the bubbles.](figs/Fig-1_dual_cube_junction.png)

**Figure V1 (Dual cube junction).** Two adjacent cubes (nearly-touching faces) with **16 inter-cube junction threads** connecting the two bubbles (a **4×4 corner↔corner bus** across the face). This is the minimal physical object behind “one RT crossing”: information/phase can traverse multiple routes through repeated cube-to-cube steps; there is no “message sent to one neighbor” primitive—multi-path behavior arises from linear propagation on the fixed sparse graph.

![Dual-cube junction with gauge-plane stack (oblique view).](figs/Fig-2_dual_cube_gauge_stack_iso.png)

![Dual-cube junction with gauge-plane stack (front view).](figs/Fig-2b_dual_cube_gauge_stack_front.png)

**Figure V2 (Dual cube with gauge-plane stack at the interface).** The same dual-cube junction, now with a **stack of parallel, translucent gauge planes** placed at the cube↔cube interface. These planes do **not** add new wires; they are **local conditioning layers** sampled at each RT crossing (plane-cell addressing).

### Data flow, jittering, and how planes participate

The model is **not** “cube A sends a message to cube B”. A propagation step is an *amplitude* moving on a local graph with **many possible routes** (including paths that step across multiple neighboring cubes). Which routes effectively contribute is decided **on-the-fly** by local conditioning at each RT crossing (plane-cell state + junction state), not by a pre-baked global path list.

**Two transport channels (edge vs bulk/bubble).**
At each cube, a crossing splits transport into:

- **Edge threads** (along cube edges): comparatively *fast* propagation.
- **Bulk/bubble threads** (via the central bubble + inner threads): comparatively *slower* and typically more damped.

Because the two channels have different travel times, $\Delta t_e$ and $\Delta t_b$, recombination produces a phase/attenuation factor
$$
e^{-\Gamma\Delta t}\,e^{i(\Omega\Delta t+\phi)} ,
$$
so fluctuations in the local route-history show up as **jittering** (effective phase noise) in the readout.

**Inter-cube transport and “curved fabric”.**
Adjacent cubes share a face-to-face junction with **16 RT threads** (corner$\leftrightarrow$corner, $4\times4$). These are the *physical* inter-cell links that carry amplitude and also define local “metric” information (effective lengths/tensions that set $\Delta t$). A **GW-like strain** is modeled as a deformation of this RT skeleton (edge lengths / junction tensions), indirectly changing $\Delta t$, damping, and (through junction state) the effective conditioning seen by EM/QED readouts. GW is therefore **not a routing plane**; it is a deformation of the underlying threaded geometry.

**Roles of the parallel gauge-plane stack at an RT crossing.**
The planes are *conditioning layers* applied when a link crosses a slice:

- **LP (lock / ordering)**: provides a global reference stamp $\tau$ used for ordering/consistency at the crossing. Because flow can reverse, LP is treated as **two-sided / direction-symmetric**: the same constraint applies for either crossing direction.
- **RL (route / localization)**: maps the crossing (ports + face) to the addressed plane cell $(u,v)$ (and micro index $(u_\mu,v_\mu)$ when needed).
- **TT2 ($\phi$-gate)**: supplies a multiplicative gate factor $g(\phi_{\text{cell}})$ that modulates which crossings/routes contribute.
- **EM/QED ($\kappa$-conditioning)**: sets junction stiffness/weighting $\kappa_{\text{cell}}$ (and the edge-vs-bulk mixing weights) that shape $|U_{\text{eff}}(u,v)|$ patterns.

### Unified equation one-liner + minimal glossary (quick reader entry)

The cross-sector propagation/response core is expressed in this paper as a GKSL-style **unified equation** with sector hooks:

$$
\boxed{
\frac{d\rho}{d\lambda}
=
-i\,[\,H_0(\lambda)+\sum_s H_s(\lambda),\,\rho\,]
\;+
\sum_s \mathcal D_s[\rho;\,\gamma_s(\lambda)]
}
$$

This is the project’s “one-for-all” mathematical contract: each sector contributes through a coherent term $H_s$, an optional dissipative term $\mathcal D_s$, and (when enabled) a microphysics bridge $\gamma_s \leftarrow n_s\sigma_s v_s/c$.

**Glossary (minimum needed to parse the rest of the paper):**

- $\rho$: effective state object being propagated/evolved (density matrix or sector-equivalent state representation).  
- $\lambda$: sector-specific evolution coordinate (e.g., baseline $L$ in weak oscillations, redshift/path variable for photon transport, or another sector-defined path parameter).  
- $H_0$: baseline/reference coherent generator for the sector under study.  
- $H_s$: sector hook (geometric modulation, medium coupling, analyzer-phase convention, propagation kernel deformation, etc.).  
- $\mathcal D_s$: dissipative/decoherence hook written in unified-equation (GKSL-style) language.  
- $\gamma_s$: sector damping/decoherence rate parameter (explicit or microphysics-derived).  
- $n_s,\sigma_s,v_s$: optional microphysics ingredients used to build $\gamma_s$ through the repository bridge $n\sigma v\to\gamma$.  

**Weak-sector specialization (used in NOvA/MINOS/T2K runners).** In the weak propagation code, the same unified equation reduces to the familiar baseline-form statement with $\lambda=L$, $H_0\equiv K(E)[H_{\mathrm{vac}}+H_{\mathrm{mat}}]$, and $H_s\equiv K(E)H_{\mathrm{geo}}$, plus optional Lindblad dephasing/damping.

**No fundamental arrow of time.** The model’s “time/order” is implemented as a **junction update schedule** (LP/RL ordering variable $\tau$) on the graph. Any apparent arrow arises **emergently** from (i) ordering constraints, (ii) relaxation of mismatch energy into queued degrees, and (iii) boundary/absorber conditions in a given test.

### The “medium”: a cube lattice of cubes, each containing a bubble and tensioned threads

Picture space as a **dense lattice of nearly-touching cubes**. Each cube carries:

- a **bubble node** at its center (a localized coherent excitation of an auxiliary field / extra DOF layer),
- **threads** (tensioned links) that connect the bubble to the cube boundary and also connect neighboring cubes.

#### Dual‑tension rule (Gravity vs Gauge separation; mechanism, not metaphor)

A key constitutive choice of the substrate is that **not all threads respond to distance the same way**:

- **Intra‑cube threads (CT: bubble↔corner, edge/internal links): invariant / quantized tension.** 
 The force magnitude is set by the link type (e.g. $T_{\mathrm{cb}},T_{\mathrm{edge}},T_{\mathrm{face}},T_{\mathrm{body}}$) and **does not scale with instantaneous length**; only the direction changes. Mechanically this is the “creep/spool” picture: length can change while tension stays fixed.

- **Inter‑cube threads (RT: cube↔cube, face bus): distance‑dependent tension.** 
 These behave like real cables/springs: tension is produced by extension (and can go slack under compression in the pull‑only version), encoding **metric/strain information**.

This **dual‑tension** rule is what lets a single substrate host both:
(i) **metric distortion** (gravity/GW) through RT stretch, and 
(ii) **local gauge dynamics** (weak/strong/EM) through CT‑rigid internal transport that is protected against large‑scale stretching.

> Status (honest): CT/RT are explicit in the mechanistic simulation layer (Sec. 2.5). The likelihood-facing sector tests use the CurvedCube kernel and inherit this rule through the bridge operators; a full first‑principles derivation is not claimed.

#### Bubble material model (conceptual; motivates damping)

In this WEAK-sector draft we treat each bubble as a **single effective internal degree of freedom**. The intended micro-picture, however, is that the bubble is an **amorphous, elastic (viscoelastic) region** of the auxiliary field: it can store strain energy and also dissipate it internally. This is why an effective damping ratio $\zeta$ is physically allowed.

A minimal caricature is a damped oscillator for a bubble amplitude $q$ (time-domain) or an along-path profile $u(s)$ (propagation-domain):
$$
\ddot q + 2\zeta\,\omega_0\,\dot q + \omega_0^2 q = F_{\mathrm{drive}}(t),
$$
with $\zeta>0$ representing internal “friction” of the amorphous bubble material.

Even in a nominal “rest” state the bubble is assumed to carry a small residual fluctuation energy (thermal/zero‑point–like **baseline jitter**), so the substrate is not an ideal rigid vacuum. This draft does **not** fit that jitter; it is a physical motivation for including damping/relaxation without adding an ad‑hoc statistical knob.

#### Early‑universe composite formation (physical origin mechanism; not a scanned fit input)

A speculative but concrete picture consistent with the substrate is that at very high energy density (early universe) many bubble skeletons can transiently interlock through the corner mesh and settle into long‑lived bound patterns. In this story, what we call “particles” are stable composite excitations of the bubble+thread network (a **new‑physics substrate** rather than a parameter inserted into the SM).

This is a motivation for the multi‑sector program, but none of the WEAK-sector $\chi^2$ tests below require this assumption.

#### Gauge plane and “lock” (auxiliary field layer; global sheet)

The auxiliary field is represented as a **gauge plane**: a global sheet/field layer spanning many cubes (in principle across the lattice). Neighboring cubes sample the same plane, so it can transmit a common phase reference across long distances without tuning individual threads.

Operationally the plane supplies a gate $g(\phi)\in[0,1]$ that modulates RT links (and therefore the strength of oriented loop transport). This admits “lock” regimes:

- **physical phase‑lock:** when $g(\phi)$ saturates near 0 or 1, long‑range couplings are either suppressed or coherently enabled, stabilizing loop phases;
- **procedural locked runs:** in the validation protocol, “locked” also means *preset, preregistered parameter points* (no scan / no tuning).

Finally, note that internal (bubble→corner) vs face (corner→corner) threads may carry different characteristic frequencies in a more detailed model. Earlier discussions introduced a two‑mode ansatz (fundamental + harmonic); **the CurvedCube $\delta_{CP}$ predictor reported here uses a single effective profile** and treats multi‑mode structure as future work.

We use two thread families (fixed in the CurvedCube tests reported here):

1) **Internal (bubble-centered) threads** 
 Bubble → each of the 8 corners: 
 $$
N_{\mathrm{in}}=8.
$$
 Think: a local “breathing reservoir” coupled to the bubble node, capable of damping / phase-lag (controlled by $\zeta$).

2) **Face-to-face corner mesh between neighboring cubes** 
 Adjacent cube faces are treated as *almost glued*. Each corner on face A connects to each corner on face B, giving a symmetric **4×4 corner-to-corner mesh**:
 $$
N_{\mathrm{face}}=4\times4=16.
$$
 Think: a transport network across cube–cube junctions that naturally supports **oriented loops** (holonomy).

#### Thread classes and data paths (edge skeleton vs bulk vs junction mesh)

The thread network has **distinct roles** that become important when interpreting why different sectors respond differently:

- **Edge (skeletal) threads**: the 12 cube edges form a mechanically stiff “frame”. In the mechanistic versions of the program these may be modeled with spring-like constraints (rest-length) or with high-tension links. Their primary role is to carry **metric-like constraints** (shape preservation / rigidity).

- **Internal (bulk) threads**: optional diagonals (face/body diagonals) connect corners through the cube interior. They provide **bulk transport / mixing channels** for the auxiliary field DOF and can be damped differently from the edges.

- **Surface junction mesh (RT)**: across a cube–cube contact, the **$4\times4=16$** corner-to-corner threads act as a junction “bus” that supports multiple simultaneous paths between neighboring cubes.

- **Bubble spokes (CT)**: the 8 constant-tension bubble–corner threads couple the bubble reservoir to the boundary (and indirectly into RT junctions).

In words: **edge** threads constrain geometry, **bulk** threads carry internal auxiliary-field transport, and **junction** meshes implement inter-cube routing.

**Force address map (tri-partition hypothesis; used throughout this draft).** 
To avoid “floating parameters”, we explicitly commit to a *geometric address* for where each interaction primarily couples to the CurvedCube substrate:

| Sector | Primary lattice locus (address) | Dominant effect in the bridge operator |
|---|---|---|
| **Weak** (neutrino oscillations) | **Edge threads** (skeletal frame transport; **edge-addressed**) | Mostly **phase/holonomy**: CP-odd orientation effects in the geometric phase proxy, with only mild amplitude damping (unless extra decoherence is explicitly turned on). |
| **Strong** (high-energy hadronic forward amplitudes) | **Bulk/internal threads** (interior mixing + edge/bulk mismatch) | **Complex amplitude**: dispersion/absorption encoded as $A_R+iA_I$ from jitter-induced delay and bulk damping. |
| **EM** (Bhabha forward region) | **Junction mesh** (the 16-port face bus) | **Regularization / conditioning**: junction filter $J(\tau;\kappa_{\mathrm{junc}})$ suppresses non-causal / out-of-order configurations that would otherwise mimic singular forward behavior. |
| **Gravity/GW** (ringdown/strain) | **Inter‑cube RT threads** (distance‑dependent skeleton strain) | **Metric distortion / strain response**: junction geometry and transport maps are modulated by RT stretch, driving GW readout modes. |
| **DM** (SPARC/RAR) | **Global lock plane** (galactic‑scale cumulative stress) | **Effective metric modification** without new particles: lock‑plane stress shifts $g_{\mathrm{eff}}$ and can reproduce the RAR mapping if validated. |

*Notes.* (i) Gravity/GW and DM are treated as **projections** of the same substrate (RT‑strain and lock‑plane stress) rather than introducing a separate new interaction locus; this is enabled by the **dual‑tension** rule above. Importantly, this implies **mechanical cross‑coupling**: a GW strain that stretches RT links can deform junction geometry and thus induce a small, time‑dependent modulation of EM transport/phase (a falsifiable prediction once EM–GW joint observables are defined). (ii) This tri-partition is **falsifiable**: if a sector requires its dominant effect to live on a different locus (e.g. Weak needing bulk absorption to match data, or Strong needing only junction filtering), the unified addressing claim fails.

#### Global planes in 3D: slicing, anchors, and the “signal journey” (how to visualize the gauge structure)

This subsection exists to remove a common visualization failure: **“planes” are not decorative.** They are global reference sheets that **slice** the lattice and are *queried at every cube–cube junction*.

**(A) What the global planes are (“the slicers”).**  
Think of a family of global planes aligned with the cube lattice axes (e.g. vertical/horizontal stacks). A cube–cube face contact is therefore also a **plane–slice event**: the 16‑thread face bus is evaluated *with respect to* the plane reference at that slice.

**(B) Plane ↔ cube exists (“the anchor”).**  
Yes: the bubble node (and its internal/bulk threads) couples to the global plane reference. This is the **locking/localization** mechanism: a local excitation is stable when its internal phase coheres with the plane’s reference phase. In other words, a “particle” is a **phase‑locked state** of the bubble/bulk relative to the plane. The same global reference also supplies the **ordering / time-order convention** used at junction assembly: updates are composed in the plane-slice frame, and “out-of-order” configurations are penalized by the junction stiffness operator.

**(C) Plane ↔ plane does *not* bypass cubes (“no direct wires”).**  
There are **no direct plane‑to‑plane links skipping the cube lattice**. Any plane‑to‑plane stress/phase propagation is **mediated by the inter‑cube RT skeleton** (cube↔cube external threads). This keeps the model closed (no hidden broadcast channel) while still allowing global stress/curvature to propagate across large distances (Gravity/DM sector).

**(D) The interference pattern comes from split paths (geometry), not from the threshold.**  
When information propagates from cube $i$ to cube $j$, it naturally splits:

- **Fast path (edge/skeleton):** transport along rigid edge threads, tightly referenced to the plane slice.  
- **Slow path (bulk/interior):** transport through the amorphous bulk where chirality $\phi$ and damping $\zeta$ introduce delay/scatter.

At the next interface (plane slice / junction), these components recombine and produce a *deterministic* phase–amplitude response
$$
\text{recombine:}\qquad e^{-\Gamma\Delta t}\,e^{i\Omega\Delta t},
$$
where $\Delta t$ is the edge–bulk timing mismatch. This is the operational origin of the strong‑sector complex response $A=A_R+iA_I$:  
$A_I$ tracks bulk loss/delay (absorption‑like), $A_R$ tracks the phase rotation (dispersion‑like).

**(E) The “threshold / gate” is a separate filter (junction stiffness).**  
After the interference pattern exists, the junction applies an additional filter governed by stiffness $\kappa_{\mathrm{junc}}$ (and when enabled, $\kappa_{\mathrm{m\,gate}}$). This filter penalizes out‑of‑order / non‑causal configurations and conditions forward singular behavior in EM. So:  
**pattern = split‑path geometry; success probability = stiffness/gating filter.**

**Mental movie (one step).**
1. Bubble in cube $i$ emits a state update.  
2. State splits into **edge** and **bulk** components inside the cube.  
3. At the face contact, the 16‑thread bus is compared against the **plane slice** (ordered junction, stiffness).  
4. Into cube $j$: the update proceeds, carrying the recombined phase and any gate penalty.

A placeholder schematic for the **global-plane story** (to be replaced by final illustrator-grade figures) is included below in two alternative styles. The intent is to separate **wiring** (CT/RT threads) from **conditioning** (plane-slice operators):

- **Style-2 (cinematic)**: stacked global slices + conditioned RT crossings (good for “film” reading).
- **Style-1 (technical)**: grid + operator blocks that emphasize *conditioning, not plane wiring*.

In the “hardware” mental model referenced throughout the logs, each cube-face contact is intersected by a member of a **global plane family** (aligned with the lattice $x/y/z$ axes). Each plane carries an **algorithmic junction-pattern map** that assigns local slice-cell values (ordering / phase / stiffness). Conceptually, cube internal/anchor threads (bubble↔plane, distributed to corner/port readouts) provide *data exchange / reference* with the plane map for localization and ordering; **but the face-to-face 16-thread bus is not wired into the planes**. Instead, when an RT crossing passes through a slice, the plane acts as a local operator on that crossing—applying ordering/time reference (LP), route/localization readout (RL), and junction conditioning with stiffness $\kappa$ (EM/QEM), with additional multiplicative gating by the auxiliary $\phi$-gate (TT2). GW enters as metric strain on the RT skeleton, indirectly shifting effective crossings/phases (no “GW routing plane”).

#### Gauge-plane path structure: where “patterns” live (implemented vs. explicit maps)

The framework uses “planes” in two **equivalent but different** representations:

**What exists even “before patterns”: the transport graph and ordered schedule.**  
Independent of whether we explicitly *draw* a 2D junction-pattern map, the allowed data-flow routes are already fixed by the **transport graph** (CT intra-cube edges + RT face↔face links) and by the **LP time-order / connection-order** rule (global lock). A “pattern map” does *not* create new routes; it only assigns **local weights/phases** to crossings that already exist.

Concretely, every RT crossing samples a slice-cell index $c$ (an **addressing** map from a crossing to a cell), and the effective transport across that interface is written as
$$
U_{ij}^{\mathrm{eff}}(c)=\mathcal{O}_{\mathrm{slice}}(c)\,s_{ij}(c)\,U_{ij},
$$
where $s_{ij}(c)=g(\phi_c)$ is the TT2/$\phi$-gate factor and $\mathcal{O}_{\mathrm{slice}}(c)$ bundles the sector-readout operators (LP ordering, RL localization readout, EM/QEM conditioning with $\kappa(c)$, etc.).  

**“Plane input points / ports” (for visualization):** the set of all RT crossings $\{(i\!\leftrightarrow\!j)\}$ defines a *discrete* set of sampling points on the plane. In figures we can draw these as dots on a 2D slice grid, colored by $g(\phi_c)$ and/or $\kappa(c)$. This preserves the rule: **no wires from the 16-thread bus to the plane**, only **conditioning at the slice**.

- **Plane-map view (global slice maps).** Each global plane family carries an *algorithmic junction-pattern map* over its 2D slice cells. When an RT (face↔face) transport crosses a slice at cell $c$, the crossing is locally conditioned by slice-cell values:
$$
  \text{(conditioning at crossing)}\qquad U_{ij}\ \mapsto\ \mathcal{O}_{\mathrm{slice}}(c)\,U_{ij},
$$
  where $\mathcal{O}_{\mathrm{slice}}$ bundles: **LP** ordering/time-reference, **RL** route/localization readout, and **EM/QEM** junction conditioning with stiffness $\kappa(c)$. The auxiliary **$\phi$-gate (TT2)** enters as a *multiplicative* factor on the same crossing, e.g.
$$
  s_{ij}(c)=g(\phi_c)\quad\text{applied only to RT crossings that intersect the slice.}
$$

- **Face-transfer view (what the cube “sees”).** The same information can be pushed onto the contacted faces as an **effective face transport tensor**. The 16 corner↔corner threads form a $4\times4$ face bus $U_{ij}$; after slice conditioning, the face observes an effective pattern of per-port weights/phases (i.e., a structured $U_{ij}^{\mathrm{eff}}$) even if no literal wires run from the bus into the plane.

**Where does the “interference / EM pattern” actually show up?**  
Operationally it is an *interface observable*: the pattern appears as **relative phases/attenuations across the port set** (entries of $U_{ij}^{\mathrm{eff}}$) and as the resulting sector readouts (weak holonomy phase, EM/QEM channel interference, strong complex amplitude $A_R+iA_I$). Conceptually you may picture the same structure as living on the plane-map (a 2D junction pattern) or on the face (a conditioned 16-port tensor). Both are the same book-keeping.

**What is implemented in the current code path?**  
The preregistered runs reported here use the **operator/gate view**: plane effects enter through **effective per-crossing factors** (global parameters + deterministic generators such as `geo_structure/geo_gen`, plus $\kappa$ where applicable). A fully explicit stored 2D “junction-pattern map” per plane family is *not required* for the current falsification runs; it is a visualization-friendly representation of the same operators and can be added later without changing the already-tested unified-equation core.

**Are plane families different?**  
Yes, by *role* (not necessarily by being separate “physical slabs”): LP provides global ordering/time-reference + localization lock; RL is the route/localization **readout** defined on LP slices; EM/QEM provides junction conditioning + stiffness $\kappa$; TT2/$\phi$-gate is a multiplicative crossing operator; GW is **metric strain on the RT skeleton** that shifts effective crossings/phases indirectly (no GW “routing plane”).

**Metric note (Ansatz alignment; not a derivation).**  
The 16‑thread face bus can be packaged as a $4\times4$ transport tensor. We adopted “16” as a structural Ansatz; it *aligns* with the component count of a 4D **Metric Tensor** $g_{\mu\nu}$ (4×4=16), making the interface a natural discrete carrier for metric information in the Gravity/GW sector. This alignment is empirical within this program: it is accepted because it survives falsification tests, not because it is proven necessary.

**Port/Thread protocol (quantized connectivity).** 
At a cube–cube contact the junction is not a single “edge”; it is a **16‑port bus**. The *count* of ports is fixed (quantized connectivity), while each port can carry a graded throughput/activation weight. Inter-cube transport is only allowed through these ports (no hidden long-range broadcast). In a coarse‑grained representation, the four corners on a contacting face form a 4‑component boundary state, and the 16 threads realize an explicit **4×4 transport tensor**.

Let the contacting face corners be ordered as $F_i=\{a_1,a_2,a_3,a_4\}$ on cube $i$ and $F_j=\{b_1,b_2,b_3,b_4\}$ on cube $j$. Define the face state vectors
$$
\psi_i^{\mathrm{face}}\equiv(\psi_{a_1},\psi_{a_2},\psi_{a_3},\psi_{a_4})^\top,\qquad
\psi_j^{\mathrm{face}}\equiv(\psi_{b_1},\psi_{b_2},\psi_{b_3},\psi_{b_4})^\top.
$$
The 16 corner↔corner threads can be packaged as a matrix $U_{ij}\in\mathbb C^{4\times4}$ with entries
$$
(U_{ij})_{mn}\ \equiv\ u_{ij,(a_n,b_m)}\in[0,1],
$$
so that the junction update is simply
$$
\psi_j^{\mathrm{face}}=U_{ij}\,\psi_i^{\mathrm{face}}.
$$
This is the precise sense in which “**16 threads are a 4×4 tensor in hardware**”: the discrete bus implements the full set of matrix elements of an inter-face transport map (metric‑like in role, protocol‑like in implementation).
> Implementation status (honest): the *counting/topology* above is fixed and used throughout the project; the exact mechanical constitutive law (spring vs constant-tension vs viscoelastic) is treated as a modeling choice and is not required for the sector tests in this draft (which use the CurvedCube kernel as the observable-facing object).

**Why 16? (structural Ansatz + 4D transport alignment).** 
The choice “16 surface threads per face contact” is introduced as a **structural Ansatz**: the boundary state on a face is treated as a 4‑component object, and the most general linear transport map between two such face states is a $4\times4$ matrix $U_{ij}$, i.e. **16 independent couplings**. This is *not* a derivation from GR; it is the **minimal hardware needed** to realize a fully general 4‑component transport protocol.

That said, there is a natural bridge to gravity language:

- In 4D relativity, a **frame field / tetrad** $e^{a}{}_{\mu}\in\mathbb{R}^{4\times4}$ also carries **16 components**, and the metric is built as 
$$
 g_{\mu\nu}=e^{a}{}_{\mu}\,\eta_{ab}\,e^{b}{}_{\nu}.
$$

- Our $U_{ij}$ is **not** identified with $g_{\mu\nu}$ (which is symmetric with 10 independent components). Instead, $U_{ij}$ is a **discrete transport object** (protocol/parallel‑transport‑like) whose component count matches the natural 4D “frame transport” bookkeeping. A metric‑like quantity can be *constructed* from transport objects if a specific reduction is imposed, but this draft does **not** assume that reduction.

This framing matters for referees: “16” is justified as the dof count of a general 4‑component transport, while the gravity connection is an **alignment** (useful for interpretation), not a claim of derivation.

**Multiplicity scaling (why 4, 16, 4 shows up mechanically).** 
When the “full‑physics” network picture is used (4 input corners + bubble + 4 output corners), simple symmetry arguments explain the recurring integer factors that appear in logs:

- bubble ↔ face‑corner couplings occur in **4 parallel links** on a face, so the symmetric‑mode effective stiffness scales as 
$$
 k_1 = 4k_{\mathrm{in}},\qquad k_3 = 4k_{\mathrm{in}}.
$$

- the face‑to‑face bus contains **16 parallel links**, so 
$$
 k_2 = 16k_{\mathrm{face}}.
$$
In the simplest “series network” reduction (symmetric normal‑mode sector), the effective neighbor–bubble coupling is
$$
k_{\mathrm{eff}}=\Big(\frac{1}{k_1}+\frac{1}{k_2}+\frac{1}{k_3}\Big)^{-1}.
$$
This is not used as a fit device in the sector likelihoods, but it provides a **mechanical** explanation for why the integers (4,16) repeatedly matter: they are the parallel‑path multiplicities of the underlying 4+4+bubble topology.

**Implementation note (what is actually in the current tested runs).** In the *code-faithful* configuration used for the preregistered sector tests, $\mathcal{O}_{\mathrm{slice}}(c)$ is **not** an externally scanned “map”. Operationally it is represented by **a small set of fixed operators / scalars** (per run / per channel) applied at crossings:

- $\phi$-gate $s_{ij}=g(\phi)$ is evaluated as a fixed (or preregistered) function of the crossing context; the paper does **not** claim a fitted free 2D texture.
- EM/QEM conditioning uses a stiffness / ordering filter (e.g. $\kappa_{\mathrm{junc}}$) as a *gate/threshold* acting at junction composition.
- LP/RL act as a **global reference + ordering/time-order rule** for whether a junction composition is admissible (localization/ordering), not as a separate “wire network”.

This keeps the **Unified Equation and the tested likelihoods unchanged**: we are clarifying *where a pattern would live* if one later chooses to visualize (or explicitly discretize) it.

**So where do “patterns” show up? (plane vs. cube face)**  
Think of two different *readouts* of the same mechanism:

1) **On the plane (map view):** a 2D junction-cell field $c\mapsto(\kappa(c),\,\phi(c),\,\zeta(c),\,\dots)$.  

   - A “pattern” here is simply the spatial arrangement of these cell values on the slice.
   - Different plane roles correspond to different fields/readouts: LP/RL (ordering + route memory), EM/QEM ($\kappa$ conditioning), and $\phi$-gate (phase/scale factor).

2) **On the cube face (transport view):** the plane does **not** receive the 16-thread bus as wires; instead, at the face interface the plane-slice operator *acts on* the transport object:
$$
   U_{ij}\ \longrightarrow\ \mathcal{O}_{\mathrm{slice}}(c)\,U_{ij}.
$$
   Here the “pattern” manifests as **which ports/phases** of the 4-component face state $\psi_i^{\mathrm{face}}$ are favored/suppressed after conditioning. Concretely: you observe the pattern as structured amplitude/phase differences across the 4 ports and across successive crossings (a “film” in steps).

**Are plane patterns different for each plane?**  
Yes in *role*, not necessarily in “separate physical sheets”. The paper’s conservative ontology is:

- LP (Global Lock) = one global reference/ordering layer.
- RL = the **routing/localization readout** of LP (not a separate physical slab unless you choose to depict it that way).
- EM/QEM = the junction-conditioning readout (with $\kappa$-type stiffness).
- $\phi$-gate / TT2 = an auxiliary **conditioning operator** evaluated on the crossing context.

Visually, you *may* draw these as parallel layers (for intuition), but in the tested model they are **operators on crossings**, not extra wired planes.

**“Film strip” (how split-path becomes an interference/pattern object)**  
At each cube-to-cube handoff, the boundary contribution can be decomposed into two components (already used conceptually in the strong/weak discussion):

- **Edge-fast path:** near-skeletal transport (arrives early / closer to LP reference).
- **Bulk-slow path:** amorphous bulk transport (delayed / scattered).

At recombination, the local contribution at the receiver is of the schematic form
$$
\psi_{\mathrm{recv}}\ \propto\ \psi_{\mathrm{edge}} \;+\; e^{-\Gamma\Delta t}\,e^{i\Omega\Delta t}\,\psi_{\mathrm{bulk}},
$$
and the plane-slice conditioning then applies:
$$
\psi_{\mathrm{recv}}\ \longrightarrow\ \mathcal{O}_{\mathrm{slice}}(c)\,\psi_{\mathrm{recv}}.
$$
Across successive crossings, this *stepwise* update produces the observed “pattern” in the sector readouts: complex response in strong (phase + absorption), holonomy-like phase memory in weak, and $\kappa$-filtered junction composition in EM/QEM.

#### Junctions, ordering, and “global lock” as a localization mechanism (conceptual layer)

A repeated theme in the logs is that “time” is **not** a fundamental parameter but can emerge from **ordered update** of junction events. The minimal abstract form is a two-stage update:

1. a **global/synchronous** step that enforces a shared reference frame (“global lock”), and
2. a **local** scattering/interaction step that uses the localized state.

A compact representation (discrete-time or discrete-path index $k$) is:
$$
X_{k+1} = \mathcal S_{\mathrm{local}}\circ\mathcal L_{\mathrm{lock}}\,[X_k],
$$
where $\mathcal L_{\mathrm{lock}}$ is the global-lock/localization map and $\mathcal S_{\mathrm{local}}$ is a local interaction map.

**Ordered junction composition (why “time = ordering” is nontrivial).** 
A junction update is an operator $\mathcal J_{ij}$ acting on the local register/state. A whole propagation/scattering episode is an **ordered composition**
$$
\mathcal P\ \equiv\ \mathcal J_{e_N}\circ\mathcal J_{e_{N-1}}\circ\cdots\circ\mathcal J_{e_1},
\qquad e_k\in E.
$$
Because the update is applied as a schedule (route–register viewpoint), compositions are generally **noncommutative**:
$$
\mathcal J_{e_{k+1}}\circ\mathcal J_{e_k}\ 
eq\ \mathcal J_{e_k}\circ\mathcal J_{e_{k+1}}
\quad\text{(in general).}
$$
The “time arrow” in this framework is exactly the **choice of schedule/order** for applying these discrete junction operations. In the same geometric picture, the schedule can be viewed as being evaluated relative to **lock‑plane slicing events**: the lattice’s “clock” is the sequence of cube↔plane‑slice handshakes that define which junction updates occurred **before/after**. Thus, **localization (locking)** and **time ordering (schedule)** share the same global reference (explicit in the theory; implemented today as an update‑ordering convention).

**Thread‑by‑thread handshake and junction stiffness $\kappa_{\mathrm{junc}}$.** 
A single junction $i\leftrightarrow j$ can be viewed as 16 micro‑handshakes (the 16 ports of the bus). Let $u_{ij,p}\in[0,1]$ denote the activation/throughput of port $p\in\{1,\dots,16\}$ during the update. A simple scalar mismatch score is
$$
m_{ij}\ \equiv\ \frac{1}{16}\sum_{p=1}^{16}\bigl(1-u_{ij,p}\bigr)^2,
$$
and the **junction stiffness** $\kappa_{\mathrm{junc}}\ge0$ penalizes out‑of‑order / misaligned / incomplete handshakes through an effective cost $E_{\mathrm{junc}}\propto \kappa_{\mathrm{junc}}\,m_{ij}$. 
In the observable‑facing bridges this appears as the bounded **junction filter** $J(\tau;\kappa_{\mathrm{junc}})$ used to damp junction transport when the forwardness proxy $\tau\to 0$ (Sec. 2.5.6; EM Sec. 4). 
(Do not confuse $\kappa_{\mathrm{junc}}$ with $\kappa_{\mathrm{gate}}$, which is a binary invariance check knob in weak runs.)

**Locking score (localization diagnostic).** 
To make “localization = locking” explicit, one can define a scalar alignment score between internal phases on the cube boundary and the Global Lock Plane reference. Let $\varphi_{i,\alpha}^{\mathrm{bulk}}$ be the phase carried by internal/bulk transport on port $p\in\{1,\dots,16\}$, and $\varphi_{\alpha}^{\mathrm{lock}}$ the corresponding lock-plane reference. A simple misalignment functional is
$$
\Lambda_i\equiv \frac{1}{16}\sum_{p=1}^{16}\bigl[1-\cos(\varphi_{i,\alpha}^{\mathrm{bulk}}-\varphi_{\alpha}^{\mathrm{lock}})\bigr],
$$
and an indicator of “being locked” is
$$
\Psi_{\mathrm{lock}}(i)\equiv \exp\bigl(-\Lambda_i/\lambda_{\mathrm{lock}}\bigr)\in(0,1].
$$
A localized object corresponds to a connected region where $\Psi_{\mathrm{lock}}$ stays high; the “locking radius” is the scale of that region. (This is presented as a diagnostic definition; the preregistered sector runners do not yet compute $\Psi_{\mathrm{lock}}$ explicitly.)

- **Why a “lock plane”?** In the geometric language used elsewhere in this program, the “lock” is naturally expressed as a *reference manifold/plane* in the auxiliary-field layer against which phases are measured. Localization occurs when the internal transport over a window produces phase alignment relative to this reference, after which the local update becomes well-defined.

- **What is implemented today?** The current sector tests do **not** require a full localization operator; instead, localization enters effectively via decoherence terms (optional GKSL dissipators in the weak unified equation) and via gate functions in the CurvedCube kernel. The “global lock plane” is therefore treated as a **global reference/clock field** in the theoretical picture; in the current code it is realized implicitly via the fixed gating/phase reference and the update schedule (an explicit dynamic plane field is future work).

#### Auxiliary planes and component choices (sector-dependent projections)

This project uses the term “gauge plane” as shorthand for an **auxiliary field / extra DOF layer** that can host additional components beyond ordinary 3D displacement. Different applications use different component subsets:

- **Lock/reference component** (localization): provides a phase reference (the “lock plane” idea above).
- **TT-like components** (GW): a two-component transverse-traceless basis ($h_+,h_\times$) projected to detectors.
- **Scalar/phase components** (weak/EM/strong): scalar phase profiles and their holonomy-derived summaries $(|c_1|,\delta_{\mathrm{geo}})$.

**Plane / layer roles that appear in the logs (terminology consistency).**  
The conversations and code sometimes describe these as separate “planes”, but in the paper we keep the ontology minimal:

- There is a **global family of reference slices** (aligned with the lattice faces; one can think of parallel slices along each axis).  
- When an RT face-to-face transport event crosses a slice, the state is **conditioned by operators defined on that slice**.  
- We do **not** assume a rigid stack of distinct physical sheets (“Lock → GW → EM/QEM”) in the preregistered tests; instead, **multiple operators can act at the same slice** (same intersection event), and they are separable by *role*.

Roles used in this draft:

- **Global Lock Plane (LP)** *(global reference + ordering)*: supplies the global phase/orientation reference **and the time-order/connection-order convention** used in ordered junction updates.  
  When emphasizing localization/routing, we refer to the same role as the **RL reference** (routing/localization); RL is **not** an additional plane.

- **Chirality / φ-gate field (TT2 auxiliary layer)**: an effective **cell-local gate** $g(\phi_{\mathrm{cell}})\in[0,1]$ applied to RT links **at the slice-crossing event** (e.g. scaling an RT transport weight $s_{ij}(\phi)=g(\phi_{\mathrm{cell}})$).  
  This is an auxiliary *field/operator layer*, not a separate “wire plane”.

- **EM/QEM junction conditioning (κ stiffness regulator)**: the κ-controlled penalty/filter acting **at junctions / face contacts**; it suppresses out-of-order / non-causal configurations.  
  (Again: not a plane-to-plane wiring claim; it is a junction operator.)

- **GW / metric strain**: gravitational waves are modeled as **metric distortion of external RT links** (distance-dependent tension/strain on the lattice skeleton).  
  Their influence on EM/QEM enters mechanically by **deforming the skeleton that anchors gauge structure**, not by introducing a new GW “plane”.

- **TT2 readout basis**: the two-component $(h_+,h_\times)$ projection used for detector-facing GW readout; implemented as a readout operator/basis choice on the auxiliary layer.

In principle the auxiliary architecture could be expanded to a **multi-role / multi-layer network** (e.g. dot-nodes, explicit plane↔plane couplers). The current preregistered sector tests in this draft intentionally stay in the **single-slice / nearest-neighbor** regime to avoid adding untested degrees of freedom.
The unifying point is not that every sector uses identical ingredients, but that all sectors consume the **same kernel object** (Sec. 2.5) through sector-specific bridge operators.

#### Phase-match gates and physical “jitter” (edge/bulk mismatch as a source of dispersion)

Many runs introduce smooth gating (e.g., $\kappa_{\mathrm{gate}}$ in weak, phase gates in GW readout) to enforce that only *phase-consistent* transport contributes coherently. A generic gate can be written as a logistic or Gaussian window acting on a phase mismatch variable $\Delta\theta$:
$$
g(\Delta\theta) = \frac{1}{1+\exp\big[\beta(\Delta\theta-\theta_0)\big]}\quad \text{or}\quad
g(\Delta\theta)=\exp\big(-\beta\,\Delta\theta^2\big).
$$

A minimal way to tie “jitter” to a concrete phase mechanism is to treat edge and bulk channels as having distinct effective group velocities $v_{\mathrm{edge}}$ and $v_{\mathrm{bulk}}$ across a characteristic length $\ell$ inside or across a junction. The arrival-time mismatch is
$$
\Delta t\ \equiv\ \ell\left(\frac{1}{v_{\mathrm{bulk}}}-\frac{1}{v_{\mathrm{edge}}}\right)\ \approx\ \ell\,\frac{\Delta v}{v^2},
$$
which produces a deterministic phase slip $\Delta\theta=\Omega\,\Delta t$ for an effective angular frequency $\Omega$. If the bulk channel is additionally lossy with rate $\Gamma$, the combined response factor is
$$
e^{-\Gamma\Delta t}\,e^{i\Omega\Delta t},
$$
i.e. a **complex** contribution whose real/imaginary parts naturally separate “dispersive” (phase) and “absorptive” (loss) effects.
In the mechanistic reading, **edge vs bulk** transport channels can have different damping/relaxation, producing small micro-oscillations (“jitter”) in the junction phase. More concretely: when a state propagates from cube A to cube B, its components can **split across fast edge routes and slower bulk routes**; the receiver recombines them with a microscopic arrival-time mismatch $\Delta t$, yielding an interference factor $e^{-\Gamma\Delta t}e^{i\Omega\Delta t}$. This provides a physically motivated interpretation for why the strong sector prefers a **complex** effective amplitude (Sec. 5):

- an absorptive component tied to dissipative bulk transport ($A_I$, optical-theorem–like sensitivity), and
- a dispersive component tied to phase jitter / coherent routing mismatch ($A_R$, $\rho$ and CNI sensitivity).

This should be read as a **mechanistic hypothesis consistent with the split-amplitude necessity**, not as a finished derivation.

A minimal mental sketch for a single cube (2D cross‑section; not to scale):

```text
corner o-----o corner
        \   /
         \ /
          B    (bubble node, cube center)
         / \
        /   \
corner o-----o corner
```

**Bubble size (status).** 
In this draft the bubble is treated as an *effective internal degree of freedom* located at the cube center; its physical radius is not yet inferred from first principles or data. Any size dependence is currently absorbed into effective parameters (e.g. $A,\zeta,\omega_0$). A dedicated scaling analysis (Strong/EM re-runs + cross-sector consistency) is planned before claiming a physical length scale.

A minimal sketch for two neighboring faces (each face has 4 corners; the RT bus is a **4×4** full corner↔corner mesh):

```text
Face A corners:  a1  a2
                 a3  a4

Face B corners:  b1  b2
                 b3  b4

RT full mesh (16 links):  (a_m) connects to every (b_n), m,n in {1..4}
```

> In all preregistered CurvedCube runs used below, geometry is fixed: `Nin=8`, `Nface=16`.

### What the model claims (plain language)

Standard neutrino oscillations are described by an SM Hamiltonian (mass splittings + matter potential). This framework adds a **geometric auxiliary layer**: the cube/bubble/thread network contributes an additional action during propagation.

The intended discipline is:

- **few knobs** (amplitude $A$, damping $\zeta$, chirality/twist phase $\phi$, discretization $k_{\mathrm{rt}}$, gate $\kappa_{\mathrm{gate}}$),
- **no parameter fishing** (single-shot or preregistered point sets),
- **falsifiable outputs** (in the strongest variant: predict $\delta_{\mathrm{CP}}$, not fit it).

In the **EM/QED plane**, the junction-addressed auxiliary-layer mechanism is used to build **predictive, scan-free bridges**: (i) LEP Bhabha *shape-only* modulation under locked knobs, and (ii) **real Bruker mzML mass spectrometry** where a scan-resolved pipeline defines an ion-load proxy $g$ and a preregistered, fit-free multi-target test (locked `good_ppm=3`) yields a stable, target-dependent separation signature (see §4.9.10).
### “Play it like an animation”: a 6-frame storyboard

Below is the intended mental animation along a baseline $L$ (e.g. 295 km for T2K-like baselines, 735 km, 810 km, etc.):

### Frame 1 — A neutrino enters the lattice.
The neutrino’s state evolves under the SM Hamiltonian $H_{\mathrm{SM}}$. At the same time, it is *coupled* (weakly) to the auxiliary geometric layer.

### Frame 2 — Each cube has an inner bubble.
The bubble is a localized auxiliary-field excitation. As the neutrino progresses, the bubble can respond (a “breathing-like” response), and this response can be damped:
$$
\text{bubble response} \sim e^{-\zeta s},\qquad s\equiv L/L_0.
$$

### Frame 3 — At a cube–cube junction, the face mesh activates.
Crossing from one cube to the next means passing through a nearly-glued face. The 16 face threads provide multiple parallel paths (corner-to-corner) for transport. This is the first place where *orientation* matters: loops exist.

### Frame 4 — The path builds a transport profile $u(s)$.
As the neutrino progresses, the auxiliary layer produces a path-dependent readout profile $u(s)$ (think: net response from the two thread families, with a phase lag $\phi$ and damping $\zeta$). Conceptually:
$$
u(s) = A\,e^{-\zeta s}\big[w_{\mathrm{in}}\,u_{\mathrm{in}}(s;N_{\mathrm{in}}) + w_{\mathrm{face}}\,u_{\mathrm{face}}(s;N_{\mathrm{face}},k_{\mathrm{rt}})\big],
$$
where $k_{\mathrm{rt}}$ is the discrete resolution (number of transport segments). In the *fixed-geometry* CurvedCube tests, the effective weights are determined by geometry counts ($N_{\mathrm{in}},N_{\mathrm{face}}$) rather than being freely fitted knobs.

### Frame 5 — CP phase must come from a connection, not displacement.
A CP-odd phase is a *holonomy-like* object (Berry/Wilson-loop spirit): it arises from oriented transport under a **connection**. A displacement $u$ is not a connection; its gradient is. The minimal 1D connection proxy is “strain”:
$$
a(s)\ \propto\ \frac{du}{ds}(s).
$$

### Frame 6 — The geometric prediction $\delta_{\mathrm{CP}}^{\mathrm{geo}}$.
We define a Wilson-like oriented projection:

$$
W_{\mathrm{geo}}\ \equiv\ \frac{1}{N}\sum_{i=1}^{N} a(s_i)\,e^{-i\,2\pi s_i},
\qquad s_i\in[0,1)\ \text{is the normalized path coordinate (often }s_i=i/N\text{).}
\qquad
\delta_{\mathrm{CP}}^{\mathrm{geo}}\ \equiv\ \arg\big(W_{\mathrm{geo}}\big)\in[-\pi,\pi].

$$

Here $s_i\in[0,1]$ is the **normalized fractional position** of junction $i$ along the ordered traversal. The weight $e^{i\,2\pi s_i}$ maps the path position to a **unit‑circle phase** (one full $0\to2\pi$ turn over the path), so $W_{\mathrm{geo}}$ is simply the **first Fourier harmonic** of the oriented strain profile. This is the discrete analog of a **holonomy / Wilson‑loop** phase extraction: a closed (or effectively closed) transport around the cube‑to‑cube circuit accumulates an oriented phase, and $\arg(W_{\mathrm{geo}})$ reads out that net geometric angle.

This is the **du_phase** prescription used in the “no-scan” CurvedCube predictions. The alternate **u_phase** is treated as an *ablation/control* (expected to fail if the connection interpretation is correct).

### Where “gate” enters (routing consistency)

A gate $\kappa_{\mathrm{gate}}\in\{0,1\}$ switches the auxiliary action off/on:

- $\kappa_{\mathrm{gate}}=0$: geometry decouples (the model should reduce to SM; used as an invariance consistency check).
- $\kappa_{\mathrm{gate}}=1$: geometry is active.

### Key weak-sector test reported here (single-shot, scan-free)

Instead of treating $\delta_{\mathrm{CP}}$ as a free knob, we:

1) **Predict** $\delta_{\mathrm{CP}}^{\mathrm{geo}}$ from geometry (CurvedCube + du_phase),
2) evaluate MINOS + NOvA spectra **at that predicted value**, and
3) evaluate T2K’s official $\Delta\chi^2_{\mathrm{T2K}}(\delta_{\mathrm{CP}})$ profile **at the same predicted value**.

#### Fixed choices for the v6 single-shot runs (pre-registered / not scanned)

The following values are **held fixed** in the reported CurvedCube $\delta_{CP}^{\mathrm{geo}}$ predictions. They are not scanned inside the predictor wrapper; the goal is to make the test **falsifiable** rather than “fit‑by‑search”.

| Quantity / flag | Value (v6 runs) | Physical meaning | Why fixed now (pre-registered intent) |
|---|---:|---|---|
| Geometry counts | $N_{\mathrm{in}}=8$, $N_{\mathrm{face}}=16$ | 8 bubble↔corner internal threads; 16 face threads per glued face (4×4 corner↔corner mapping) | Set by cube combinatorics / symmetry, not tuned |
| Gate | $\kappa_{\mathrm{gate}}\in\{0,1\}$ | turns geometry off/on | $\kappa_{\mathrm{gate}}=0$ is an invariance control; $\kappa_{\mathrm{gate}}=1$ is the tested hypothesis |
| RT resolution | $k_{\mathrm{rt}}\in\{180,360,720\}$ | discretization of the junction path / integration resolution | $k_{\mathrm{rt}}=180$ is the baseline; higher values are a convergence check (not a fit) |
| Coupling amplitude | $A=10^{-3}$ | small geometric phase/strain amplitude | kept small to stay in a perturbative regime (avoid “dial until it fits”) |
| Damping | $\zeta=0.05$ | internal viscoelastic loss in the bubble medium | moderate damping to suppress unphysical long‑range buildup; fixed for comparability |
| Phase offset | $\phi=\pi/2$ | quadrature phase between drive and response | fixed to avoid a trivial near‑zero projection; treated as a prereg constant |
| Holonomy readout | `u_phase` vs `du_phase` | displacement vs connection‑like readout of the strain profile | treated as an explicit **model variant / ablation**: `u_phase` is a negative control; `du_phase` is the physically motivated candidate (Sec. 6.3) |

**Important honesty note (model variants):** choosing between `u_phase` and `du_phase` is **not** a continuous “scan”, but it is a discrete **model‑definition choice**. This draft therefore reports both: `u_phase` fails strongly against T2K, while `du_phase` yields low T2K $\Delta\chi^2$. The next step is to pre‑register `du_phase` and test it on independent datasets/sectors.

We summarize results (verbatim logs in **Appendix A**):

| Run | Mode | T2K profile key | $\delta_{CP}^{geo}$ (rad) | T2K BF (rad) | T2K $\Delta\chi^2$ at geo | $\mathrm{SUM}=\Delta\chi^2_{\mathrm{MINOS}}+\Delta\chi^2_{\mathrm{NOvA}}$ | $\mathrm{PLUS\_PEN}=\mathrm{SUM}+\Delta\chi^2_{\mathrm{T2K}}$ |
|---|---|---|---:|---:|---:|---:|---:|
| IO (IH), wRC | du_phase | `h1D_dCPchi2_wRC_IH` | -1.315523 | -1.382301 | 0.048395 | -0.010 | +0.038 |
| IO (IH), woRC | du_phase | `h1D_dCPchi2_woRC_IH` | -1.315523 | -1.256637 | 0.005679 | -0.010 | -0.004 |
| NO (NH), wRC | du_phase | `h1D_dCPchi2_wRC_NH` | -1.315523 | -1.884956 | 0.436709 | -0.010 | +0.427 |
| IO (IH), wRC | u_phase (control) | `h1D_dCPchi2_wRC_IH` | +0.852159 | -1.382301 | 18.871793 | -0.006 | +18.866 |

**Interpretation (honest):**

- **Definition:** here we report $\Delta\chi^2 \equiv \chi^2_{\mathrm{model}}-\chi^2_{\mathrm{baseline}}$. Therefore **negative** $\Delta\chi^2$ means the model is (slightly) better than the baseline at that fixed point; the magnitude $\sim10^{-2}$ indicates the effect is tiny (implementation-consistency scale).
- The **du_phase** holonomy prescription can place $\delta_{CP}^{geo}$ **inside the low-$\Delta\chi^2$** region of the IH T2K profile family (especially woRC).
- The **u_phase** control fails dramatically (high T2K $\Delta\chi^2$), consistent with the “connection, not displacement” argument.
- The MINOS/NOvA $\Delta\chi^2$ values reported by the predictor wrapper are currently **very small** in magnitude; they should be treated as a *implementation check* rather than a decisive “SM is beaten” claim at this stage. The robust, high-signal part of this test is the **scan-free $\delta_{CP}$ prediction** confronted directly with the official T2K $\Delta\chi^2$ profile.
**About “ordering preference” (NO vs IO):** the CurvedCube predictor produces a single number $\delta_{CP}^{\mathrm{geo}}$ that is (by construction) **ordering‑independent**; it does not “know” $\Delta m^2_{31}$ or the mass ordering. Any apparent preference for IO in the tables above comes from the **shape and best‑fit location of the external T2K $\Delta\chi^2(\delta_{CP})$ profile** (NH vs IH, wRC vs woRC): our fixed $\delta_{CP}^{\mathrm{geo}}$ lands closer to the IH valley in this T2K release. This should therefore be treated as a **testable coincidence**, not as a claimed ordering measurement; independent ordering data (e.g., JUNO‑class experiments) can falsify it.

---

## Unified equation quick reference (one-line vs boxed long form)

The “one-line unified equation” is intentionally compact — think of it like **$E=mc^2$**: correct, but hiding many definitions (unit conventions, what is inside each Hamiltonian piece, how geometry enters, and what is actually predicted vs scanned). 
This section gives **both**:

1) a **one-line** form you can cite quickly, and 
2) a **boxed long form** that unpacks what the one-line statement really means in this framework.

### One-line unified equation (continuous propagation; weak-sector specialization)

In baseline-coordinate form (the same independent variable used by the forward code), the compact statement is:

$$
\boxed{
\frac{d\rho}{dL}
=
-i\,K(E)\,[\,H_{\mathrm{vac}}(E)+H_{\mathrm{mat}}(L,E)+H_{\mathrm{geo}}(L,E),\,\rho\,]
\;+\;
\sum_j \Gamma_j(L,E)\,\mathcal D[L_j]\,\rho
}
$$

where $L$ is baseline distance (km in the code convention), $E$ is neutrino energy (GeV), and
$K(E)=1.267/(E/{\mathrm{GeV}})$ is the standard oscillation unit-conversion factor.
The dissipator is $\mathcal D[L]\rho \equiv L\rho L^\dagger-\frac12\{L^\dagger L,\rho\}$.

### Sector-agnostic mapping postulate (kernel output → sector bridge operator)

The **CurvedCube geometry engine** produces a small set of **universal kernel outputs**. The framework’s claim is that these outputs are **not sector-specific**; what changes across sectors is only the **bridge operator** that converts the kernel output into the sector’s natural dynamical object.

#### Kernel outputs (shared across sectors)

From a normalized path parameter $s\in[0,1]$ and its complex profile $u(s)$, define the first-harmonic coefficient
$$
c_1 \;\equiv\; \frac{1}{N}\sum_{j=1}^{N} u(s_j)\,e^{-i\,2\pi s_j},
\qquad
|c_1| \in [0,1],
\qquad
\delta_{\mathrm{geo}}\equiv \arg(c_1).
$$

A fixed, preregistered “template” along the path is then
$$
T(s)\;=\;\cos\!\big(2\pi s-\delta_{\mathrm{geo}}\big)
\quad \text{or} \quad
T(s)\;=\;\sin\!\big(2\pi s-\delta_{\mathrm{geo}}\big),
$$
with the choice treated as part of the **pre-registered test definition** (not tuned).

We package the shared kernel output as
$$
\mathcal K \;\equiv\; \big(|c_1|,\ \delta_{\mathrm{geo}},\ T(\cdot)\big).
$$

#### Mapping postulate

For each sector $X\in\{\text{weak},\text{strong},\text{EM},\dots\}$, there exists a **bridge operator** $\mathcal B_X$ such that the geometric contribution is

$$
\text{(geometry in sector $X$)} \;=\; \mathcal B_X\!\left(\mathcal K;\ A_X,\ \text{(pre-registered knobs)}\right),
$$

where $A_X$ is a small amplitude parameter and the remaining “knobs” (template choice, mapping $s(\cdot)$, reference scales) must be fixed **before** the comparison (no scan).

Concretely:

| Sector $X$ | Dynamical object | Bridge operator $\mathcal B_X(\mathcal K)$ (code-faithful summary) |
|---|---|---|
| Weak (oscillation) | Hamiltonian term $H_{\mathrm{geo}}(L,E)$ | Add a **small phase / energy-scale perturbation** to the flavor evolution generator: $H_{\mathrm{geo}}\propto A_{\mathrm{weak}}\,|c_1|\,T(s(L))$. This is where **path accumulation** occurs. |
| Strong (elastic / $\sigma_{\mathrm{tot}}$ / CNI) | Eikonal / amplitude $F(t,s)$ | Add geometry as an **impact-parameter texture** or an **amplitude-level phase**: $\chi(b,s)\to \chi_{\mathrm{SM}}(b,s)+A_I\,\mathcal W_I(b,s;\mathcal K)$ for absorptive/bulk, and $F\to F\,e^{iA_R\,\mathcal W_R(\cdot;\mathcal K)}$ for dispersive/phase-sensitive observables (CNI, $\rho$). |
| EM (Bhabha, this draft) | Differential cross section vs. $\cos\theta$ | Shape-only multiplicative deformation on an imported baseline curve: $\sigma_i^{\mathrm{GEO}}=\beta_{g(i)}\sigma_i^{\mathrm{base}}(1+\delta_i)$, with $\delta\propto A_{\mathrm{EM}}\,s_{\mathrm{struct}}\,g_{\mathrm{gen}}\sin\phi\cdot R(|t|)\cdot[\alpha_{\mathrm{map}}\ln(|t|/t_{\mathrm{ref}})]$. Robustness uses preregistered pivot-centering $\delta\leftarrow\delta-\delta(x_p)$. |

**Why this matters:** the “one-line unified equation” is the correct weak-sector specialization, but **strong and EM do not share the same evolution variable**. The mapping postulate makes the framework explicit: the kernel is universal; the sector dependence is isolated into $\mathcal B_X$, which must itself be fixed and falsifiable.

#### Complex gauge amplitude (why strong data forces an $A_R/A_I$ split)

Early weak-sector tests can be described as a **pure phase-like modulation** of a Hermitian generator, so a single real coupling (called $A_{\mathrm{weak}}$ in the code interface) is sufficient.

High-precision strong-sector observables are different: the forward amplitude contains **absorptive** and **dispersive** components that feed different measurements:

- $\sigma_{\mathrm{tot}}$ is controlled by the **absorptive/imaginary** part (optical theorem).
- $\rho$ and CNI are controlled by the **dispersive/real** part and the **phase** of the amplitude.

The minimal way to express this inside the *same* “kernel → bridge” framework is to allow the sector coupling to be **complex**,
$$
A_X\equiv A_R + iA_I,
$$
and to route its quadratures through the bridge operator:

- $A_I$ enters the absorptive channel (e.g., an eikonal/opacity modulation driving $\sigma_{\mathrm{tot}}$).
- $A_R$ enters the dispersive/phase channel (e.g., a multiplicative phase rotation relevant for $\rho$ and CNI).

**Mechanistic link (jitter $\rightarrow A_R+iA_I$).** 
In the “engine-room” picture (Sec. Physical picture), a junction mixes an edge-like channel and a bulk-like channel with different arrival times and losses. A coarse‑grained response factor of the form $e^{-\Gamma\Delta t}e^{i\Omega\Delta t}$ directly motivates a complex effective coupling: the phase shift maps to a dispersive contribution ($A_R$) while the attenuation maps to an absorptive contribution ($A_I$). This is the intended physical meaning of the split—not an invitation to tune extra knobs.
This is **not** introduced as “extra freedom to fit strong data”: the strong preregistered track in this draft uses a *single fixed point* for $(A_I,A_R)$, and the split is only the **physically correct wiring** between the universal kernel and sector-specific observables.
> Interpretation: the entire “new physics / geometry” claim is contained in $H_{\mathrm{geo}}$. Everything else is standard.

#### Symbol glossary (continuous form)

> **Completeness note:** This table defines the *continuous unified-equation symbols*. 
> For the full cross‑sector parameter inventory (including $|c_1|$, $\delta_{\mathrm{geo}}$, $\kappa_{\mathrm{junc}}$, `env_mode/env_scale`, GW backreaction knobs, and the exact CLI names), see **§7.B**.

| Symbol | Meaning (code-faithful) | Typical unit / convention |
|---|---|---|
| $\rho$ | 3×3 flavor-basis density matrix ($\nu_e,\nu_\mu,\nu_\tau$); probabilities are $P_{\alpha\to\beta}=\rho_{\beta\beta}$ after propagation from initial $\rho(0)=|\nu_\alpha\rangle\langle\nu_\alpha|$. | dimensionless |
| $L$ | Baseline coordinate used as the propagation variable in the forward code. | km |
| $E$ | Neutrino energy for the given spectral bin. | GeV |
| $K(E)=1.267/(E/{\mathrm{GeV}})$ | Standard oscillation unit-conversion factor so that $\Delta m^2$ in eV$^2$ and $L$ in km give phases in radians. | (km$^{-1}$) when multiplied by eV$^2$ |
| $H_{\mathrm{vac}}(E)$ | Vacuum Hamiltonian built from $\Delta m^2$ and the PMNS matrix (Box A). | “mass-squared” convention (eV$^2$) inside $K(E)$ |
| $H_{\mathrm{mat}}(L,E)$ | Matter potential term (Box B), parameterized by constant $\rho$ and $Y_e$ in this draft. | same convention as $H_{\mathrm{vac}}$ |
| $H_{\mathrm{geo}}(L,E)$ | New geometric term (Box C). In CurvedCube runs this is ultimately driven by the oriented strain profile $a(s)$ and yields a predicted $\delta_{CP}^{\mathrm{geo}}$. | same convention as $H_{\mathrm{vac}}$ |
| $\Gamma_j(L,E)$ | Decoherence / damping rates for optional Lindblad channels (usually set to 0 in the CurvedCube predictor runs). | 1/km |
| $L_j$ | Lindblad operators specifying the decoherence channel. | dimensionless operators |
| $\mathcal D[L_j]\rho$ | Dissipator: $L\rho L^\dagger-\frac12\{L^\dagger L,\rho\}$. | — |

**Geometry-only ingredients used inside $H_{\mathrm{geo}}$** (as implemented):

| Symbol | Meaning | Notes |
|---|---|---|
| ${\mathrm{env}\_scale}(L)$ | Dimensionless environment strength. | Used to separate “flat/lab” vs “high-curvature/astrophysical” projections. |
| $\Delta m^2_{\mathrm{scale}}$ | Overall scale factor that converts the geometric phase proxy into an effective mass-basis deformation. | In preregistered weak runs this is fixed (no scan). |
| ${\mathrm{base}\_d}\phi/{\mathrm{d}}L$ | Baseline derivative of the geometric phase proxy. | Code chooses the specific proxy (LEFF/phase/curved-cube) via $\mathtt{geo\_action}$. |
| $G$ | Restricted SU(3) structure for the deformation (diagonal or selected generators). | Fixed choice in prereg runs. |

**CurvedCube / holonomy parameters (prediction runs)**

| Parameter | Meaning | Where it enters |
|---|---|---|
| $k_{rt}$ | Route resolution / number of segments used to discretize the ordered traversal. | Controls sampling of $u(s)$ and $a(s)=du/ds$. |
| $\phi$ | **Internal twist / chirality phase** between the bulk-thread frame and the edge-frame transport (implemented in code as a drive–response quadrature of the bubble proxy). | Controls CP-odd handedness/orientation of the accumulated phase ($\nu$ vs $\bar\nu$, forward vs reverse traversal). |
| $\zeta$ | **Topological friction / damping** of surface+bulk response (viscoelastic relaxation of the bubble/thread subsystem). | Sets the decay (dephasing) envelope of $u(s)$ and therefore how long geometric phase memory persists. |
| $A$ | Small geometric amplitude used inside the bubble drive term (fixed prereg). | Sets overall strain magnitude (sign flips strain). |
| $\kappa_{\mathrm{gate}}$ | Gate (0/1) that turns the geometric correction off/on for invariance checks. | consistency test: gate=0 must reproduce SM. |
| $\kappa_{\mathrm{junc}}$ | Junction stiffness (vacuum regulator) used in the junction filter $J(\tau;\kappa_{\mathrm{junc}})$ in EM (and optionally in other bridges). | dimensionless; typically $\lesssim 10^{-1}$. |

**Mechanistic reading of $\phi$ and $\zeta$ (not “free fit knobs”).** 
In the forward code, $u(s)$ is generated by a damped driven proxy (a minimal stand-in for the bubble+thread response). $\zeta$ controls *how rapidly the response relaxes* (topological friction / dephasing), while $\phi$ sets the *handed twist* of the internal response relative to the edge transport frame. Under path reversal (or $\nu\leftrightarrow\bar\nu$ in the weak mapping), the model treats $\phi$ as the CP-odd slot: the accumulated oriented phase is sensitive to the handedness implied by $\phi$, whereas $\zeta$ mainly controls the damping of contributions with traversal length.

#### Project integration note (how the one-line unified equation is wired into the repository)

The one-line **unified equation** above is not only a conceptual summary; it is now the **explicit software contract** used to connect sectors. The implementation follows a shared pattern:

- a **common GKSL/open-system evolution layer** carries the baseline propagation and sector insertion hooks;
- each sector contributes a declared mapping from its kernel outputs/observables into a bridge operator (coherent and/or dissipative);
- the runner executes the same contract with sector-specific defaults and datasets.

For this revision, the entanglement and photon sectors are treated on equal footing with the previously established weak / EM / strong / DM / LIGO sectors. In particular:

- **Entanglement sector:** the CHSH/correlation audit is interpreted as a sector-level observable test anchored to the common bridge framework (with NIST run4 HDF5-export coincidences as the validated evidence path).
- **Photon sector:** the birefringence / redshift-accumulation and photon-decay-style dissipative terms are represented as sector-level contributions that can be read in the same unified-equation language (coherent phase accumulation + optional dissipative channel).

This is the project-level mathematical unification claim: **different sectors keep their own observables and datasets, but they share one evolution grammar.**

#### Microphysics bridge note ($n\sigma v \rightarrow \gamma$ as a tested scaffolding layer)

The microphysics integration introduced in this revision promotes sector damping from a purely symbolic coefficient to an optional derived quantity:
$$
\Gamma = n\,\sigma\,v,
\qquad
\gamma = \Gamma/c.
$$

In repository terms, this is implemented as a switchable layer (via `use_microphysics=True`) rather than a forced replacement of all legacy defaults. This design choice is deliberate:

- it preserves backward compatibility with preregistered runner settings,
- it makes the microphysics conversion traceable and auditable,
- and it allows direct equivalence checks between “derived $\gamma$” and “explicit $\gamma$” modes.

Accordingly, the paper should be read as claiming a **validated integration scaffold** (mathematically consistent and tested), not a completed first-principles closure for every sector.

#### Sector Hook Map (observable → unified-equation hook → microphysics hook → runner/test status)

The table below is the explicit “sector-by-sector mathematics hook” catalog for this revision. It is meant to make the repository wiring auditable at a glance: each sector keeps its own observable, but plugs into the same unified-equation grammar ($H_s$, $\mathcal D_s$, and optional $n\sigma v\rightarrow\gamma$ bridge).

| Sector | Primary observable(s) | Unified-equation hook ($H_s$, $\mathcal D_s$) | Microphysics candidate ($n,\sigma,v$) | Runner / test anchor | Status |
|---|---|---|---|---|---|
| **Weak (oscillation)** | $P_{\alpha\to\beta}(L,E)$, $\Delta\chi^2$ on NOvA/MINOS/T2K packs | $H_s$: vacuum + matter + geometric mass-basis deformation $H_{\mathrm{geo}}$; $\mathcal D_s$: optional dephasing/damping channel | $n$: matter/electron density $n_e$; $\sigma$: weak interaction proxy/effective scattering scale; $v\!\approx\!c$ | `nova_mastereq_forward_kernel_BREATH_THREAD_v2.py`; `test_equivalence_weak_runner.py`; `test_equivalence_weak_golden_outputs.py` | **Validated (prereg real-data path)** |
| **Mass spectrometry (ESI FT-ICR)** | m/z shift, setting-conditioned separation, target-specific holdout performance pass | $\mathcal D_s$-dominant correction (effective dephasing/load damping); optional $H_s$-like phase/frequency bias term | $n$: ion-load / packet density proxy (TIC-based); $\sigma$: effective ion-ion interaction surrogate; $v$: cyclotron/packet speed proxy | `ms_sector.py` + locked mzML prereg runner family (§4.9.10 artefacts); microphysics hooks via `microphysics.py` | **Validated (observable pipeline)** / **Microphysics: scaffolding** |
| **EM (Bhabha / $\mu^+\mu^-$)** | $\sigma(\sqrt{s})$, angular dependence, residuals vs baseline | $H_s$: coherent bridge deformation; $\mathcal D_s$: optional absorptive/junction-filter correction $J(\tau;\kappa_{\mathrm{junc}})$ | $n$: target/luminosity density proxy; $\sigma$: QED process cross section; $v_{\mathrm{rel}}\!\approx\!c$ | `em_sector.py`; `test_equivalence_em_bhabha_golden_outputs.py`; `test_equivalence_em_mumu_golden_outputs.py` | **Validated (golden/equivalence)** |
| **Strong (hadronic)** | $\sigma_{\mathrm{tot}}$, $\rho$ ratio, ridge-style/elastic observables (sector-dependent) | $H_s$: phase-like coherent deformation; $\mathcal D_s$: absorptive/attenuative channel for hadronic broadening | $n$: effective hadronic medium/occupancy proxy; $\sigma$: hadronic cross section; $v$: relative beam speed | `strong_sector.py`; `test_equivalence_strong_sigma_tot_golden_outputs.py`; `test_equivalence_strong_rho_golden_outputs.py` | **Validated (golden/equivalence)** |
| **Dark matter (SPARC / RAR)** | Rotation curves, residual structure, profile-consistency metrics | $H_s$-dominant effective potential/geometry contribution; $\mathcal D_s$ typically off or secondary in current mapping | $n$: halo mass density proxy; $\sigma$: DM self-/baryon-coupling surrogate (model-dependent); $v$: halo orbital speed | `dm_sector.py`; `test_equivalence_dm_golden_outputs.py` | **Validated (observable mapping)** / **Microphysics: scaffolding** |
| **LIGO / GW ringdown** | Ringdown residuals, projected/null consistency, detector-combined diagnostics | $H_s$: coherent propagation/ringdown kernel deformation; $\mathcal D_s$: damping-envelope / loss channel (if enabled) | $n$: effective environment occupancy proxy (not literal particle gas); $\sigma$: interaction surrogate; $v$: propagation speed scale | `ligo_sector.py`; `test_equivalence_ligo_quadrupole_golden_outputs.py` | **Validated (equivalence)** / **Microphysics: scaffolding** |
| **Entanglement (Bell/CHSH)** | Coincidence counts, correlators $E(a,b)$, CHSH $S$, significance $z$ | Observable audit interpreted as sector-level coherence/decoherence test; $H_s$: analyzer-phase/setting convention; $\mathcal D_s$: decoherence channel governing correlation loss | $n$: pair/coincidence rate proxy; $\sigma$: effective pair-environment scattering surrogate; $v\!\approx\!c$ | Canonical evidence path: NIST run4 HDF5-export coincidences (`nist_run4_coincidences.csv`); equivalence: `test_equivalence_entanglement_runner.py` | **Validated (NIST run4 evidence path)** |
| **Photon (decay / birefringence)** | Birefringence accumulation, redshift-weighted phase rotation, attenuation/decay-style tests | $H_s$: coherent polarization-phase accumulation; $\mathcal D_s$: attenuation / decay-like dissipative channel | $n$: background medium/field occupancy proxy; $\sigma$: polarization-dependent interaction surrogate; $v\!\approx\!c$ | `photon_sector.py`; birefringence prereg runner family; `test_equivalence_photon_birefringence_runner.py` | **Validated (birefringence equivalence + prereg path)** / **Photon-decay microphysics: scaffolding** |

**Reading note.** “Scaffolding” in the microphysics column/status does **not** mean “untested code.” It means the $n,\sigma,v$ identification is presently a controlled, auditable bridge layer rather than a claimed unique first-principles derivation for that sector.

#### Verification status (declared math ↔ runners, plus microphysics wiring)

To verify that the mathematical declarations are correctly transferred into executable code, the project now includes two test families.

**(A) Declared-math / golden-output equivalence tests**  
Independent implementations are compared against runner outputs (or golden outputs) for sector-specific observables. Representative files include:

- `test_equivalence_weak_runner.py`
- `test_equivalence_weak_golden_outputs.py`
- `test_equivalence_em_bhabha_golden_outputs.py`
- `test_equivalence_em_mumu_golden_outputs.py`
- `test_equivalence_dm_golden_outputs.py`
- `test_equivalence_strong_sigma_tot_golden_outputs.py`
- `test_equivalence_strong_rho_golden_outputs.py`
- `test_equivalence_ligo_quadrupole_golden_outputs.py`
- `test_equivalence_entanglement_runner.py`
- `test_equivalence_photon_birefringence_runner.py`

A consolidated list/documentation is maintained in `EQUIVALENCE_CHECKS.md`.

**(B) Microphysics wiring equivalence tests**  
These tests verify that the `use_microphysics=True` path produces the same evolution as the path in which the corresponding $\gamma$ is injected explicitly:

- `test_microphysics_wiring_equivalence.py`
- `test_microphysics_scaffold.py`

At the integration snapshot corresponding to this paper revision, the full integration suite is recorded as **37 passed**, with the newly added entanglement + photon equivalence checks reported as **6/6 OK**. This is the main evidence that the cross-sector unified-equation narrative is not only conceptual prose, but also faithfully implemented.

### Boxed long form (what the one-line hides)

#### Box A — Vacuum mixing

$$
\boxed{
H_{\mathrm{vac}}(E)
=
\frac{1}{2E}\,
U(\theta_{12},\theta_{13},\theta_{23},\delta_{CP})\,
{\mathrm{diag}}(m_1^2,m_2^2,m_3^2)\,
U^\dagger
}
$$

- $U$ is the PMNS matrix; in the **prediction** runs we do **not** treat $\delta_{CP}$ as a free knob: we set $\delta_{CP}\leftarrow\delta_{CP}^{\mathrm{geo}}$.

#### Box B — Matter potential

$$
\boxed{
H_{\mathrm{mat}}(L,E)= {\mathrm{diag}}(V_e(L),0,0)
}
\qquad
V_e(L)\propto \sqrt{2}\,G_F\,n_e(L)
$$

- In practice we parameterize $n_e$ through $\rho$ and $Y_e$ (constant-density approximation in the current weak-sector runs).

#### Box C — Geometric term as an *effective* mass-basis deformation

The code-faithful implementation constructs a mass-basis deformation $\delta M^2_{\mathrm{geo}}$ and injects it into the Hamiltonian:

$$
\boxed{
H_{\mathrm{geo}}(L,E)=\frac{1}{2E}\,U\,\delta M^2_{\mathrm{geo}}(L,E)\,U^\dagger
}
$$

with

$$
\boxed{
\delta M^2_{\mathrm{geo}}(L,E)
=
{\mathrm{env}\_scale}(L)\;
\Delta m^2_{\mathrm{scale}}\;
{\mathrm{base}\_d}\phi/{\mathrm{d}}L(L,E)\;
G
}
$$

- ${\mathrm{env}\_scale}(L)$ is a dimensionless environment-strength factor (used to separate “flat/lab” from “high-curvature” projections).
- $G$ is a restricted SU(3) structure (diagonal or one of a small set of generators $\lambda_a$).

**CurvedCube / holonomy specialization (parameter-free $\delta_{CP}$ prediction).** 
In the CurvedCube predictor runs, geometry produces an oriented transport profile $u(s)$ across a normalized path coordinate $s\in[0,1]$ (Sec. “Physical picture”, Frames 4–6). 
The *connection/strain proxy* is

$$
a(s)\ \propto\ \frac{du}{ds}(s),
$$

and the Wilson-like complex projection is

$$
\boxed{
W_{\mathrm{geo}} \equiv \sum_i a(s_i)\,e^{i\,2\pi s_i},
\qquad
\delta_{CP}^{\mathrm{geo}}\equiv \arg(W_{\mathrm{geo}})
}
$$

This is the **du_phase** rule: CP phase comes from a **connection** (a gradient/strain), not directly from displacement $u$.

#### Box D — Optional decoherence / Lindblad channels

If decoherence is enabled (it is typically set to zero in the preregistered CurvedCube runs unless stated):

$$
\boxed{
\sum_j \Gamma_j\,\mathcal D[L_j]\,\rho
\quad\text{with}\quad
\mathcal D[L]\rho = L\rho L^\dagger-\frac12\{L^\dagger L,\rho\}
}
$$

### One-line unified equation (discrete lattice / ordered junction update)

For the discrete cube-lattice formulation used elsewhere in the program (route–register / gauge–energy / bubble-mode layers), the compact “$E=mc^2$” form is:

$$
\boxed{
X_{n+1}
=
\Pi_{\mathrm{Gauss}}\circ
\mathcal U_{AE}^{(\chi_n)}\circ
\mathcal U_{\mathrm{energy}}^{(\chi_n)}\circ
\mathcal U_{\mathrm{route}}^{(\chi_n)}\circ
\mathcal U_{\mathrm{mix}}^{(\chi_n)}
\big[X_n\big]
}
$$

and the “boxed long form” is exactly the list of $\mathcal U$ operators given later in Sec. 2.1.1 (each $\mathcal U$ is a physics-motivated sub-update: mixing, route flow, energy accounting, gauge constraint projection).

> The important conceptual bridge: **CurvedCube/holonomy** supplies a *geometric* phase object; the discrete lattice supplies a *physical substrate* in which oriented loops and strain-like connections are natural.

---

## 1. Motivation and scope
This work is organized around a practical question: can a single, structurally constrained “geometric kernel” be instantiated across sectors in a way that:

- preserves each experiment’s binning and covariance structure,
- maintains a strict separation between **baseline reference curves** (called “SM” in some scripts for legacy reasons) and **geometric modulation**, and
- enables explicit tests for overfitting (e.g., cross-validation and covariance robustness)?

A core methodological choice is to treat the baseline reference curve as a **frozen imported object** (from MC generators, perturbative calculations, or experiment-provided reference curves) and to introduce new structure only through a constrained geometric modulation. This ensures that “shape fixes” are not accidentally absorbed into nuisance normalizations without being tested. (Here, “SM” is simply a **do‑nothing baseline** label used in some legacy scripts; it is not a claim about the particle‑physics Standard Model.)

### 1.1 Physical motivation: why a cubic lattice, inner bubble, and threads?

This draft proposes the **cubic lattice + inner bubble + threads** as a *physical micro-geometry* of spacetime (a fundamental substrate carried by an **auxiliary field / extra DOF layer**), **not** as a computational metaphor or an effective parametrization.

At the same time, this draft does **not** attempt a direct microscopic detection of the lattice. Instead, it tests **observable consequences** of the substrate (e.g., a *scan-free* geometric prediction of $\delta_{CP}$ in the weak sector) against data. If the predicted consequences fail, the substrate model is **falsified**; if they succeed across sectors, the substrate interpretation gains empirical support.

The motivation is pragmatic and falsification-oriented:

- **Minimal isotropic discretization:** a cube tiling is the simplest 3D discretization that preserves a clean notion of local neighborhoods, faces, and corners. It provides an explicit bookkeeping for “where coupling happens” (links/threads) and a stable way to define closed vs open system checks.
- **Two-scale internal structure:** the **bubble** is a single internal DOF hub inside each cube; the **inner (CT) threads** tether corners to the bubble with constant-tension mechanics. This makes “localized excitation vs bulk strain” separable in code, letting us test whether a localized kick produces coherent propagation or only local sloshing.
- **Inter-cube stiffness control:** the **outer (RT) threads** between neighboring cube corners act as the primary elastic coupling. The parameter $k_{rt}$ is the *cleanest single knob* that controls the substrate’s characteristic mode frequencies. This is exactly what we need for GW ringdown falsification: if the substrate cannot be tuned to produce a QNM-like band, that is a concrete failure mode.
- **Universal localization-first structure:** the **gauge plane** (auxiliary field / extra DOF layer) carries a minimal “gate” $g(\phi)$ that turns couplings on/off in a controlled way. Conceptually: *localization first, then effect*. Operationally: it is a code-faithful mechanism to suppress uncontrolled long-range coupling until the auxiliary field indicates a localized support.

In a coarse-grained (continuum) limit, the substrate behaves like an **elastic/viscoelastic medium**: wave speeds and dominant mode frequencies scale as
$$
c_{\mathrm{eff}}\sim \sqrt{\frac{k_{\mathrm{eff}}}{\rho_{\mathrm{eff}}}},\qquad f_{\mathrm{mode}}\propto c_{\mathrm{eff}}/\ell,
$$
so increasing $k_{rt}$ (holding effective inertia fixed) is the correct direction to push the substrate toward higher-frequency GW-like content. The draft treats this as a **testable calibration question**, not as an assumed truth.

### 1.1.1 What is established in this draft — and what is legacy (reader‑facing)

**Established (re‑run in this revision):**

- **Weak sector:** CurvedCube holonomy provides a **single‑shot** prediction $\delta_{\mathrm{CP}}^{\mathrm{geo}}$ (no scan), and we evaluate it against:
 (i) T2K official $\Delta\chi^2(\delta)$ profiles (penalty), and
 (ii) MINOS/NOvA spectral Poisson+$ \chi^2 $ packs.
 The IO/IH runs show $\Delta\chi^2_{\mathrm{T2K}}\ll 1$ for IH profiles at the preregistered point (Appendix A), which is the key “new geometry → CP‑phase” result in this draft.

- **Implementation consistency:** gate0 invariance (null) and basic within‑runner stability checks were used throughout the debugging cycle; future drafts will formalize these as preregistered ablations rather than ad‑hoc diagnostics.

**Legacy reference (not yet re‑run with the updated CurvedCube/ordering fixes):**

- **Strong (ATLAS 13 TeV pp elastic), EM (LEP Bhabha), DM (RAR/SPARC), GW (ringdown):** earlier locked runs in older model snapshots showed encouraging $\Delta\chi^2$ improvements in several pipelines. Those results are kept here as *context for the multi‑sector program*, but **should not be interpreted as “confirmed under the current update”** until the same datasets are re‑run with the present geometry implementation and the same falsification constraints.

This is important for the reader: in this revision, **WEAK is the only sector whose “updated CurvedCube” claims are backed by fresh console logs and a reproducible preregistered point**. The next milestones are the EM/Strong re‑runs under the updated model (and then strong‑sector publication‑grade robustness).

## 1.2 Terminology: substrate, gauge plane, and sector knobs

Throughout this draft we use **gauge plane** to mean an **auxiliary field / extra DOF layer** attached to the geometric substrate, on which localization/transport structure is represented. In this sense the gauge plane is treated as a *universal* component of the kernel (weak/strong/EM/GW), while different sectors expose different effective “knobs” or projections of it:

- **Gauge-plane field** $\phi$: the kernel-level state on the auxiliary layer that defines a gate $g(\phi)\in[0,1]$. This gate is the simplest code-faithful way to express “localization first, then effect” (uncertainty-controlled coupling): it specifies *where/when* couplings are active before sector observables are evaluated.

- **Global lock / reference plane (conceptual)**: an auxiliary reference manifold used to define phases and to express “time = ordering” in a discrete junction schedule. In this draft it appears as an **ordered update** (Sec. 2.1.3a and the one-line map), and as gate functions; a fully explicit localization operator on this plane is planned but not required for the preregistered sector tests.

- **Sector-facing knobs (explicitly preregistered):**
 - weak: $\kappa_{\mathrm{gate}}$, $\zeta$, template choice (cos/sin), and the fixed geometry scale mapping $(\omega_0,L_0)$;
 - strong: complex coupling $A = A_R + iA_I$ routed into absorptive vs dispersive channels (Sec. 5.2);
 - EM: **shape-only** bridge with per-group normalizations $\beta_g$ plus an anchoring rule (pivot-centering) to prevent free renormalization (Sec. 2.4 and Sec. 4);
 - GW: detector projection $F_{+},F_{\times}$ and polarization angle $\psi$, plus the projection/plane conventions (Sec. 6).

These terms are used consistently below: the kernel (Sec. 2.5) defines the substrate + gate; sector sections then state exactly how their observables depend on that kernel.

This terminology is used consistently below: the kernel (§2.4/§2.5) defines the substrate + gauge-plane gate; sector sections then state exactly how their observables depend on that kernel.

---

## 1.3 Paper objectives, evidence levels, and what is completed in this draft

### 1.3.1 Primary objective
Demonstrate that a **single unified-equation modulation family** can be *ported* across sectors (weak, strong, EM, DM, GW) by changing only:
1) the sector baseline model and likelihood, and
2) the mapping from unified-equation state → an observable.

### 1.3.2 Evidence levels (do not mix)
This draft uses two evidence levels that must not be conflated:

- **Detection-grade evidence:** the template family contains statistically significant correlated structure **in the chosen analysis window** under a clearly defined null (off-source) procedure, and the result is reasonably stable under small analysis perturbations.

- **Localization-grade evidence:** the pipeline can infer (or strongly constrain) sky position/polarization **from timing + antenna geometry**, by scanning $(\alpha,\delta,\psi)$ and demonstrating a stable optimum consistent with published posteriors. This requires extra robustness tests and a multiple-testing penalty.

In other words: a model can be **correct/useful as a detector/template family** without yet being **localization-accurate**.

### 1.3.3 Completion snapshot (this draft)
- **EM sector:** re-run under the updated CurvedCube (v6) configuration using LEP Bhabha (Table 18) with an imported baseline curve. Under a preregistered, scan-free bridge, full-covariance runs show $\Delta\chi^2>0$ for $A=+10^5$ and a strong sign-flip falsifier; pivot-centered holdouts (diag_total shown) also pass. No discovery claim is made; robustness upgrades (full-cov pivot holdouts + cross-channel transfer) are listed in §4.7.
- **Mass spectrometry (real Bruker/CompassXport mzML; prereg-locked, fit-free):** scan-resolved per-scan mass estimate pipeline + setting separation; **multi-target target-specific test** with locked `good_ppm=3` yields prereg **performance pass** with holdout + third-arm stability (median_abs_delta 0.116/0.119; rank_corr_abs 0.965; MAD rank_corr 0.836; third-arm rank_corr 0.853; 12/12 nonzero targets). See §4.9.10 and signed artefacts under `out/particle_specific_final_goodppm3_lock/`.
- Entanglement sector — preregistered Bell/CHSH audit on NIST run4 (Bridge-E0, no-fit); HDF5-export path passes with GLOBAL_CHSH ≈ 2.455 and z ≈ 1.991 (see §4.10).
- Photon-decay / propagation bridge sector — preregistered cosmic birefringence accumulation and sky-fold falsifier tests (no-fit); current locked results are null-compatible and constrain the effect (see §4.11).
- **GW sector:** ringdown-only pipeline + cubic-lattice response implemented; *detection-grade exploration* is underway. A separate localization-grade claim is explicitly deferred (see §6.7).
- **Weak/Strong/DM sectors:** the unified-equation interface + CLI mapping are documented; quantitative sector-wide result tables are partly complete and flagged where additional runs are required.

### 1.3.4 What remains for a publication-quality claim set
Across sectors, the minimum “paper-ready” checklist is:
1) **one canonical run command per sector** (frozen defaults),
2) a **result table** (best-fit params, likelihood deltas, p-values as applicable),
3) a **robustness paragraph** (what knobs were varied and what changed), and
4) clear labeling of which claims are **primary** (detection-grade) vs **future work** (localization-grade, multi-event population claims, etc.).

## 1.4 Sector objectives, current status, and missing tests (reader-facing)

This snapshot is aligned to the **current performance scoreboard** used in the updated runbook.

| Sector | Current performance status | What is established now | Remaining work / scope limits |
|---|---|---|---|
| Weak (T2K/NOvA/MINOS) | **performance pass** | The locked single-shot point yields a positive combined score (`TOTAL SCORE = 0.489377`). | Best next step is an independent validation / release-holdout confirmation and figure polishing. |
| Strong (sigma_tot + rho) | **performance pass** | The locked strong rerun gives a positive net `Delta chi2` after combining sigma_tot and rho. | The rho branch still carries tension, so the paper should describe this as a net-positive but mixed strong result. |
| EM (LEP Bhabha + MuMu) | **not established** | The tested Bhabha and MuMu branches both return `Delta chi2 = 0`, so no performance superiority is established in the current branch. | Either find a genuinely positive preregistered branch or keep EM explicitly labeled as non-passing in the paper. |
| GW / LIGO ringdown | **performance pass** | The canonical exact GW170814 branch is locally re-confirmed as a passing performance result on the current exact run path. | Remaining work is presentation / figure cleanup, not a missing performance result. |
| DM / SPARC | **performance pass** | The current DM rerun is positive at the locked k-fold criterion (`all_folds_delta_test_positive = true`). | Remaining work is concise in-paper figure/table embedding only. |
| FT-ICR mass spectrometry (target-specific) | **performance pass** | Both the `internal_only` strict branch and the `full` ablation branch pass the locked prereg criteria with stateful dynamics confirmed. | This remains a target-specific cross-domain robustness result, not a fundamental-particle claim. |
| Entanglement (NIST CHSH audit) | **not scored here** | Retained as a bridge/audit line in the draft. | It is not part of the present performance scoreboard and is not a first-principles Bell derivation claim. |
| Photon (birefringence accumulation) | **not scored here** | Retained as a bridge/preregistered scaffolding line in the draft. | It is not part of the present performance scoreboard and is not yet a final calibrated cosmic-birefringence extraction. |

## 2. Framework

### 2.1 Weak sector: unified equation (density matrix evolution)
We evolve a 3×3 flavor-basis density matrix $\rho(L)$ (for $\nu_e,\nu_\mu,\nu_\tau$) as a function of baseline length $L$. The unified equation is written in Lindblad (GKSL) form:

$$
\frac{d\rho}{dL} = -i\,[H(L,E),\,\rho] + \sum_j \Gamma_j(L,E)\left(L_j\,\rho\,L_j^\dagger - \tfrac12\{L_j^\dagger L_j,\rho\}\right),
$$

where:

- $H(L,E)$ is an effective Hamiltonian (in flavor basis),
- $L_j$ are Lindblad operators representing decoherence channels,
- $\Gamma_j$ are (possibly energy- and baseline-dependent) rates.

We decompose the Hamiltonian as:
$$
H(L,E) = H_\mathrm{vac}(E) + H_\mathrm{mat}(L,E) + H_\mathrm{geo}(L,E).
$$

#### 2.1.0 Weak sector in lattice language (edge-addressed holonomy with plane anchors)

This sector is *edge‑addressed*: the dominant propagation of the flavor state follows the rigid **edge threads** (the cube skeleton). The global planes (auxiliary field layer) are **not** an extra dimension; they are a *global sheet set* that slices the lattice and provides a phase reference at every cube–cube junction.

**3D connection hierarchy (what exists, what does not).**

- **Plane ↔ Cube (YES; “anchor”)**: the bubble/inner state in a cube is anchored to the local plane slice through internal/bulk threads (the locking channel used for localization/identity).
- **Plane ↔ Plane (NO direct wires)**: parallel planes are coupled *indirectly* via the intervening cube lattice. The inter‑cube external threads act as the “springs” that transmit stress and maintain consistent plane spacing (this is the same mechanical path used in Gravity/DM).
- **Cube ↔ Cube (YES; “bus”)**: the face‑to‑face connection is the **16‑thread** corner↔corner mesh; it is the hardware where the plane slice, the junction ordering, and the propagating state are compared.

**Why an interference/phase pattern appears even for a nearest‑neighbor step.**  
When the state transfers from cube $A$ to cube $B$ across a junction (i.e., across a plane slice), the update is effectively a *split‑path + recombination* process:

1) **Fast component (edge path)**: propagates on the rigid edge skeleton (plane‑locked reference channel).  
2) **Slow component (bulk path)**: propagates through the amorphous bulk threads inside the cube, experiencing internal twist $\phi$ and damping controlled by $\zeta$.  
3) **Recombination at the next interface**: at the receiving plane slice, the two components recombine with a timing mismatch $\Delta t$, producing a complex response of the form
$$
e^{-\Gamma \Delta t}\,e^{i\Omega \Delta t},
$$
which is the operational origin of *phase rotation + attenuation* in the lattice language.

In the **Weak** sector, we read this primarily as a **geometric phase (holonomy)** accumulated along the edge‑addressed route (amplitude changes are sub‑leading unless explicit decoherence is enabled).

**Holonomy as a path‑ordered product (discrete picture).**  
Along a route of $N$ junctions, the geometric transport can be represented schematically as
$$
U_{\mathrm{geo}}(L)\;\equiv\;\mathcal P\prod_{k=1}^{N} U_{(k)}(\phi,\zeta,\kappa_{\mathrm{junc}},\ldots),
$$
where each $U_{(k)}\in\mathbb C^{4\times4}$ is the face transport tensor (the 16‑thread bus packaged as a matrix) evaluated at junction $k$, and $\mathcal P$ denotes the ordered (non‑commutative) composition.

**How the “gate” appears in the Weak operator (phase‑match selectivity).**  
To avoid turning the geometric operator into a universal always‑on knob, the implementation uses a *selectivity gate* that is maximal only near a phase‑match condition. A code‑faithful schematic is:

$$
g_{\mathrm{match}}(L)\;=\;\exp\!\left[-\left(\frac{\omega L/2 - \pi/2}{\sigma}\right)^2\right],
\qquad
\Delta\phi_{\mathrm{total}}=\Delta\phi_{\mathrm{base}}+w_{\mathrm{thread}}\,g_{\mathrm{match}}\,\Delta\phi_{\mathrm{thread}},
$$

with width $\sigma$ and internal frequency scale $\omega$; we **define the gate argument as $\omega L/2$** so that choosing $\omega_0=\pi/L_0$ centers the match at $L=L_0$.

Operationally:

- **If $g_{\mathrm{match}}\approx 0$** (baseline far from match), the geometric correction decouples and the prediction returns to the SM‑only evolution.
- **If $g_{\mathrm{match}}\approx 1$** (near match), the holonomy term becomes observable in the weak‑sector channels under the preregistered protocol.

**Neutrino vs antineutrino: “du\_phase” readout.**  
For each species, `du_phase` computes a phase $\delta_{du}(X)$ from the **connection proxy** $\nabla u$ (first Fourier mode; see Sec. 6.3). The CP-odd quantity used in comparisons is the antisymmetric difference:
$$
\delta_{\mathrm{CP}}^{\mathrm{geo}}\;\equiv\;\delta_{du}(\nu)\;-\;\delta_{du}(\bar\nu),
$$
which is the quantity compared to the weak‑sector $\delta_{\mathrm{CP}}$ profiles in the preregistered runs.

**Weak‑sector knobs (minimal map; code names in monospace).**

- $\omega$ (`--omega`, `--omega0_geom`, `--L0_km`): internal geometric frequency/scale that sets the phase‑match location.
- $\phi$ (`--phi`): internal twist (chirality) controlling the $\nu$ vs $\bar\nu$ asymmetry of the ordered holonomy update.
- $\zeta$ (`--zeta`): intrinsic topological friction / geometric temperature controlling phase memory loss along the lattice.
- $\kappa_{\mathrm{junc}}$ (`--kappa_gate` / junction stiffness in the discrete operator): penalizes out‑of‑order / non‑causal junction updates and regularizes the plane‑slice handshake.
- Optional explicit decoherence (`--decoh_zeta`): additional Lindblad‑like damping channel (kept off in the “SM‑limit stress” runs).

**Vacuum term.** Using the usual PMNS mixing matrix $U$,
$$
H_\mathrm{vac}(E) = \frac{1}{2E}\,U\,\mathrm{diag}(m_1^2, m_2^2, m_3^2)\,U^\dagger.
$$

**Matter term.** In constant-density approximation, the MSW potential enters as:
$$
H_\mathrm{mat}(L,E) = \mathrm{diag}(V_e(L),0,0),
$$
with $V_e(L)\propto \sqrt2 G_F n_e(L)$, and in code we parameterize density and electron fraction through $\rho$ and $Y_e$.

**Geometric term.** The geometric contribution is implemented as an additional effective phase/mass-splitting structure. In the current code-faithful form, the core driver is represented by a baseline-dependent phase-gradient-like object of the schematic form
$$
\mathrm{base\_dphi\_dL}(L,E)= \mathrm{amp}(E)\; g_\mathrm{eff}\; |R(\omega)|\;\omega\;\cos(\Phi(L))\;\mathrm{atten}(L),
$$
where $g_\mathrm{eff}=g_\mathrm{bp}+g_\mathrm{lp}$, $\omega$ is an internal geometric frequency parameter, and $R(\omega)$ is a scalarized response derived from the substrate kernel $\chi(\omega;\Theta)$ defined in Sec. 2.5 (e.g. a chosen component or magnitude $|\chi|$ under the relevant drive/readout).

**Environment scaling.** To decouple “lab/flat” sensitivity from “high-curvature” projections, we introduce a dimensionless environment-strength factor:
$$
\mathrm{env\_scale}(L) \equiv \frac{\mathcal{E}_\mathrm{env}(L)}{\mathcal{E}_0}.
$$
The minimal extension is the one-line modification:
$$
\delta M^2_\mathrm{geo}(L,E)\ \rightarrow\ \mathrm{env\_scale}(L)\,\delta M^2_\mathrm{geo}(L,E).
$$

**Mechanistic interpretation (“the clock”, not an energy label).** 
The lattice does not “measure TeV”; instead, higher-energy interactions are modeled as producing a **higher effective junction/lock-plane interrogation rate**—a larger number of substrate updates per unit propagation variable. We encode that coarse-grained interaction frequency into $\mathcal{E}_{\mathrm{env}}(\cdot)$, so $\mathrm{env\_scale}$ can be read as a normalized *interaction-count/clock* for how often the propagating state couples to the global lock reference and junction network. In strong-sector implementations, choosing forms such as `env_mode=log` or `env_mode=eikonal` corresponds to specific hypotheses about how this effective interaction count grows with collision energy (slow growth like $\log s$, or saturating growth in an eikonalized map). This is a **modeling postulate** and is falsifiable by cross-sector transfer: if one cannot use the same physical reading of $\mathrm{env\_scale}$ consistently, the “single substrate / different projections” claim fails.

---

#### 2.1.1 Code-faithful form used in the current implementation

To reduce ambiguity, we also record the *implemented*
evolution used by the current forward scripts. The code evolves $\rho(L)$ with a unit-conversion
prefactor:

$$
\frac{d\rho}{dL} = - i\, K(E)\,[
H(L,E),\rho] + \mathcal{D}(\rho),\quad\quad K(E) =
\frac{1.267}{E/GeV}.
$$

The Hamiltonian is assembled (internally) in an ${eV}^{2}$-based convention as:

$$
H(L,E) = U\left( M_{vac}^{2} + \delta
M_{geo}^{2}(L,E) \right)U^{\dagger} + H_{mat}(E),
$$

with $\delta M_{geo}^{2}$
constructed in the **mass basis** as:

$$
\delta M_{geo}^{2}(L,E) = \Delta
m_{scale}^{2}\, \mathrm{base\_dphi\_dL}(L,E)\,
G.
$$

Here $\Delta m_{scale}^{2}$ is an
implementation constant converting the phase-gradient driver into ${eV}^{2}$ units, and $G$ is either (i) a diagonal structure
$diag(h_{1},h_{2},h_{3})$ or (ii) an
off-diagonal SU(3) generator $\lambda_{a}$ selected from a restricted
set (lam1/lam2/lam4/lam5/lam6/lam7).

Finally, the environment-strength extension is applied
multiplicatively as:

$$
\delta M_{geo}^{2}(L,E)\,
\rightarrow \, \mathrm{env\_scale}(L)\,\delta
M_{geo}^{2}(L,E).
$$

#### 2.1.2 Path-Holonomy-Instrument unified equation (single-line conditioned form)

For experiments where the observable is **conditional**
(e.g., coincidence gating / quantum-eraser-style post-selection), the
correct object is a *conditioned* state $\rho_{c}$ and a stochastic master
equation. In a compact **one-line** form:

$$
d\rho_{c} = - \frac{i}{\hslash}\,[
H_{prop} + H_{slit} + H_{hol}(\theta_{geo};L,E) +
H_{mark}(L),\,\rho_{c}]\, dL +
\sum_{k}^{}\Gamma_{k}\,\mathcal{D}[ L_{k}]\rho_{c}\, dL +
\sum_{m}^{}\left(
\frac{M_{m}(\lambda_{L})\rho_{c}M_{m}^{\dagger}(\lambda_{L})}{Tr[
M_{m}^{\dagger}(\lambda_{L})M_{m}(\lambda_{L})\rho_{c}]} -
\rho_{c} \right)\,\left( dN_{m}(L) - Tr[
M_{m}^{\dagger}(\lambda_{L})M_{m}(\lambda_{L})\rho_{c}]\, dL
\right),
$$

with the usual dissipator $\mathcal{D}[ L]\rho \equiv L\rho L^{\dagger} - \frac{1}{2}\{ L^{\dagger}L,\rho\}$, and $dN_{m}$ Poisson increments (0/1 in $dL$) satisfying $\mathbb{E}[ dN_{m}] = Tr[ M_{m}^{\dagger}M_{m}\rho_{c}]\, dL$.

**Term-by-term (short):** - **Coherent
propagation:** commutator with $H_{prop} + H_{slit} + H_{hol} + H_{mark}$.

- **Unconditioned dissipation/decoherence:** $\sum_{k}^{}\Gamma_{k}\,\mathcal{D}[ L_{k}]\rho_{c}$. - **Measurement instrument /
quantum jumps:** the $M_{m}$
term updates $\rho_{c}$ only when the
corresponding record $dN_{m}$ clicks;
subtracting its expectation keeps the innovation correctly centered.

**Consistency check:** averaging over records (taking
$\mathbb{E}[ \cdot ]$)
removes the last stochastic term and returns the deterministic GKSL
unified equation used elsewhere in this paper.

#### 2.1.3 Discrete closed-system lattice unified equation (route–gauge–mode layer; ordered junction updates)

This paper’s weak-sector story can be read in two compatible ways:

- **Continuous GKSL umbrella (Sec. 2.1):** a standard Lindblad-form evolution for $\rho(L)$.
- **Code-faithful discrete map (this subsection):** a *closed-system, ordered* junction update on a cube-lattice graph. It reproduces the same conceptual split—(i) phase-generating “Hamiltonian-like” transport and (ii) decoherence/irreversibility—without requiring a globally Hamiltonian system. The ordering is explicit (a global lock/schedule), which is the minimal way to make “junction dynamics” time/sense-of-order driven.

**Bridge note (discrete ↔ continuous):** in the limit of small step size $\Delta L\to 0$ (or $\Delta t\to 0$) with appropriate scaling of the dissipators, the discrete route–register update is expected to approach a GKSL-type unified equation. A full derivation of this continuum limit (and the conditions under which complete positivity is preserved) is deferred to future work. For the weak-sector CurvedCube tests reported in this draft, the numerics use the **discrete** probability engine; the GKSL form is provided as a familiar umbrella description.

The discrete formulation is what we refer to as the **route–register unified equation**: the state is a coupled set of route weights, gauge/link fields, mismatch energy, and a response variable. Gates are *derived* (not new free knobs): they are functions of mismatch and response.

> **Terminology note.** In this document “gauge plane” means an **auxiliary field / extra‑DOF layer** carried on nodes/links. It is **not** a new coordinate direction and **not** the Standard Model gauge field; it is a bookkeeping/interaction layer used to express interference, constraints, and derived gates in the discrete update map.

---

##### Figure: conceptual picture (cubes, bubbles, threads, planes)

**Objects and their physical meaning (minimal mapping)**

- **Cube / node $i$:** a local spacetime cell. 
- **Neighbor link / junction $(i\to j)$:** local coupling between two cubes. 
 *“Junction state”* lives on the link: $A_{ij},E_{ij},E^{\mathrm{mis}}_{ij}$ plus the currently active flow.

- **RT threads (between cubes):** physical realization of link coupling (conceptually a bundle; for face–face corner↔corner, the symmetric choice is 16 threads). 
- **CT threads (inside cube):** corner→bubble connections with **constant tension** (creep/spool picture: length can change while tension stays fixed).
- **Bubble (inside cube):** carries the **Mode-Layer** (normal modes $\Omega_\ell$), providing “resting waviness” even at $T=0$ (zero-point).
- **Plane-A (Geometry/Response plane):** the local response $q_i$ (and its energy book-keeping). 
- **Plane-B (Gauge/Interference plane):** link fields $(A_{ij},E_{ij})$, node charges $Q_i$, and the route register $\rho_{i\to j}$.

---

### One-line unified equation (discrete, ordered, closed)

Let the full state at tick $n$ and energy bin $E$ be
$$
X_n(E) \equiv \Big(\{p_i(E)\},\{\rho_{i\to j}(E)\},\{A_{ij}\},\{E_{ij}\},\{Q_i\},\{E^{\mathrm{mis}}_{ij}\},\{q_i\}\Big).
$$

Define an **ordered edge schedule** $\chi_n(i,j)\in\{0,1\}$ (“global lock”) selecting which junctions update at tick $n$. Then the discrete unified equation is:

$$
\boxed{
X_{n+1}
=
\Pi_{\mathrm{Gauss}}
\circ
\mathcal U_{AE}^{(\chi_n)}
\circ
\mathcal U_{\mathrm{energy}}^{(\chi_n)}
\circ
\mathcal U_{\mathrm{route}}^{(\chi_n)}
\circ
\mathcal U_{\mathrm{mix}}^{(\chi_n)}
\big[X_n\big]
}
$$

- $\Pi_{\mathrm{Gauss}}$: exact Gauss-law projection (constraint enforcement). 
- $\mathcal U_{AE}$: gauge/link update on the active junction set. 
- $\mathcal U_{\mathrm{energy}}$: strict energy bookkeeping (work/pump/leak and response). 
- $\mathcal U_{\mathrm{route}}$: route register update $\rho\to\rho'$ (with dissipation handled by bookkeeping). 
- $\mathcal U_{\mathrm{mix}}$: probability-conserving mixing/transfer map $p\to p'$.

The operators are **local** (act only on scheduled junctions), but repeated ticks build long-range transport.

---

### 2.1.3a Ordered junction schedule (“lock”)

The lock mechanism is **only**: “put updates in a global order”. Formally:

- Choose $\chi_n(i,j)$ such that active edges do not collide at nodes (a matching), ensuring a well-defined sequential update.
- The schedule may be deterministic (pre-registered) or generated by a fixed rule; it is **not** a fit knob.

---

#### Time symmetry vs emergent arrow (no fundamental time-arrow is assumed)

At the level of the substrate update rules, we do **not** postulate a fundamental “arrow of time.” The dynamics is defined as an ordered sequence of local junction updates $\chi_n(i,j)$; if one (i) disables dissipative drains (e.g. $\gamma\to 0$ in the mismatch→response channel) and (ii) reverses the update schedule while applying the appropriate conjugations to the auxiliary fields, the update chain is intended to be **formally reversible** (up to numerical error).

An **arrow** can nevertheless emerge in practice from three sources that are explicitly modelled as *conditions*, not axioms:
1) **Ordering constraints** (LP/RL / lock schedule): the chosen global update order breaks time-symmetry at the level of the executed algorithm, even if the underlying local maps can be inverted.
2) **Coarse-graining into a response reservoir** ($E^{\mathrm{mis}}\to E^q$ with $\gamma>0$): this encodes irreversibility as a derived, slow relaxation channel.
3) **Boundary conditions / absorbers** (used in some sector simulations): these define an initial-value problem and remove artificial reflections.

(Interpretational note only.) In QFT, the Feynman–Stueckelberg reinterpretation allows antiparticles to be viewed as particles propagating backward in time. Here we use **no particle-content claim** of that sort; the only analogous structure is that the route register contains both directions $\rho_{i\to j}$ and $\rho_{j\to i}$, so reverse-directed propagation and backflow are naturally represented within the same bookkeeping.

### 2.1.3b Route register and flows

For each node $i$, outgoing weights $\rho_{i\to j}(E)\ge 0$ define a stochastic transport kernel
$$
T_{i\to j}(E)=\frac{\rho_{i\to j}(E)}{\sum_k\rho_{i\to k}(E)+\varepsilon},
\qquad \sum_j T_{i\to j}=1.
$$

On an active junction, define an antisymmetric flow (prevents double counting):
$$
J_{ij}(E)=\chi_n(i,j)\,\big(\rho_{i\to j}(E)-\rho_{j\to i}(E)\big),
\qquad J_{ij}=-J_{ji}.
$$

---

### 2.1.3c Gauge/Interference plane: $A,E,Q$ with Gauss constraint

The gauge plane is an **auxiliary field / extra-DOF layer** carried on links and nodes.

**Local update (generic form):**
$$
E_{ij}\leftarrow E_{ij}+\Delta t\,[\alpha_E F_{ij}(A)-J_{ij}],
\qquad
A_{ij}\leftarrow A_{ij}+\Delta t\,g_E^2\,E_{ij}^{\mathrm{mid}}.
$$

**Gauss constraint (node charge lives on nodes):**
$$
\boxed{\sum_{j\in\mathcal N(i)} E_{ij}=Q_i.}
$$

Enforce it exactly via a Laplacian projection:
$$
r_i=\sum_jE_{ij}-Q_i,
\qquad \mathcal L\lambda=r,
\qquad
E_{ij}\leftarrow E_{ij}-(\lambda_i-\lambda_j).
$$

---

### 2.1.3d Energy bookkeeping (strict closed; dissipation as derived)

Energy is tracked in three reservoirs:

- route energy $H_{\mathrm{route}}$,
- mismatch energy $E^{\mathrm{mis}}_{ij}\ge 0$ on links,
- response energy $E^q$ carried by $q_i$.

**Work (gauge→route):**
$$
\Delta E^{(ij)}_{g\to r}=\Delta t\,J_{ij}\,g_E^2\,E_{ij}^{\mathrm{mid}}.
$$

**Pump (route→mismatch):**
$$
\Delta E^{\mathrm{pump}}_{ij}=\eta_J J_{ij}^2\Delta t,
\qquad
E^{\mathrm{mis}}_{ij}\leftarrow E^{\mathrm{mis}}_{ij}+\Delta E^{\mathrm{pump}}_{ij}.
$$

**Leak handling (“mismatch absorbs route-energy loss”):** after the route update, if $\Delta H_{\mathrm{route}}<0$,
$$
\Delta E^{\mathrm{leak}}_{ij}= -\min\big(0,\Delta H_{\mathrm{route}}^{(ij)}\big),
\qquad
E^{\mathrm{mis}}_{ij}\leftarrow E^{\mathrm{mis}}_{ij}+\Delta E^{\mathrm{leak}}_{ij}.
$$

**4A mismatch→response (dissipative, but closed):**
$$
P_{ij}=\gamma\,E^{\mathrm{mis}}_{ij},
\qquad
E^{\mathrm{mis}}_{ij}\leftarrow E^{\mathrm{mis}}_{ij}-P_{ij}\Delta t,
\qquad
E^q\;{+}{=}\;\tfrac12\sum_{(i,j)} P_{ij}\Delta t.
$$

**Bidirectional propagation and junction backflow (accounted, not “free energy”).**  
Because the route register stores **both directions** on each neighbor pair $(i\to j)$ and $(j\to i)$, a “reflected” or “returned” component at a junction is represented as a redistribution between these directed weights (and, more generally, among the outgoing set $\{\rho_{i\to k}\}$). This does **not** violate the strict-closed bookkeeping: any loss/gain in route energy on an update is balanced by the explicitly tracked mismatch and response reservoirs via the pump/leak and mismatch→response channels above. In other words, backflow is a dynamical rearrangement inside the same update algebra, not an additional degree of freedom injected from outside.

This is where “collapse-like” behavior becomes *non-instantaneous*: gates close as mismatch accumulates and then decays into response.

![Energy ledger and mismatch→gate logic (schematic).](figs/fig3_energy_ledger.png)

---

### 2.1.3e Gate vs junction (definitions) and dephasing law

- **Junction:** the *local update event* on an oriented neighbor link $(i\to j)$ at tick $n$. 
- **Gate:** a *derived scalar multiplier* $g_{ij}(E)\in[0,1]$ that modulates transfer/mixing strength on that junction.

Define mismatch amplitude
$$
S_{ij}=\sqrt{\frac{2E^{\mathrm{mis}}_{ij}}{\kappa_T}},
$$
and the baseline dephasing gate
$$
\boxed{
g_{ij}(E)=\exp\big[-c_S S_{ij}^2 - c_q\,(q_i+q_j)\big].
}
$$

An “ordered resonant” variant is obtained by multiplying with a mode-derived match factor (Sec. 2.1.3g).

---

### 2.1.3f Probability-conserving mixing / transfer map

For each energy bin, the junction induces a **doubly-stochastic** mixing map $M_{ij}(E)$ so that total probability is conserved:
$$
p_j^{\alpha}(E)\leftarrow \sum_i\sum_{\beta}T_{i\to j}(E)\,M_{ij}^{\alpha\beta}(E)\,p_i^{\beta}(E).
$$

A minimal $\mu\leftrightarrow\tau$ disappearance kernel may be written as
$$
r_{\mu\tau,ij}(E)=g_{ij}(E)\,\sin^2(2\theta_{23})\,\sin^2\!\Delta_{ij}(E),
$$
where the local phase is
$$
\Delta_{ij}(E)=\omega(E)\,\ell + A_{ij}+\phi,
\qquad
\omega(E)=\omega_0\frac{E_0}{E}.
$$

---

### 2.1.3g Mode-Layer: “string/membrane small oscillations” (the single source of variants)

The bubble carries normal modes; this is the **only** source of particle-type variation.

**Wave speed from CT tension and effective inertia:**
$$
c_T\equiv\sqrt{\frac{T}{\mu_{\mathrm{eff}}}}.
$$

**Spherical bubble-mode spectrum (minimal):**
$$
\boxed{
\Omega_{\ell}=\frac{c_T}{R_{\mathrm{eff}}}\sqrt{\ell(\ell+1)},\qquad \ell=0,1,2,\dots
}
$$

**Particle type definition:**
$$
\boxed{\text{type}\equiv (T,\mu_{\mathrm{eff}},R_{\mathrm{eff}})\Rightarrow \{\Omega_{\ell}\}.}
$$

**Zero-point “resting waviness”:**
$$
E_{\ell,0}=\tfrac12\hbar\Omega_{\ell},
\qquad
\langle q_{\ell}^2\rangle_0\propto \frac{1}{\Omega_{\ell}}.
$$

**How modes enter the weak-sector model (only two entry points):**

1) **Phase scaling (dispersion factor):**
$$
\sigma_{\ell}\equiv\frac{\Omega_{\ell}}{\Omega_{\ell_{\ast}}},
\qquad
\omega(E)\to\omega_{\ell}(E)=\omega_{\mathrm{SM}}(E)\,\sigma_{\ell},
$$
with $\ell_{\ast}$ fixed by convention (not fit; e.g. $\ell_{\ast}=2$).

2) **Resonant match overlay (ordered gate):**
$$
g_{ij}(E)\to g_{ij}(E)\times g^{(\ell)}_{\mathrm{match}}(E),

g^{(\ell)}_{\mathrm{match}}(E)=\exp\Big[-\frac{\big(\Delta_{ij}(E)-\Delta_{\ell}^*\big)^2}{2\Sigma_{\ell}^2}\Big],
\qquad
\Delta_{\ell}^*=\Omega_{\ell}\Delta t,
\quad
\Sigma_{\ell}=\Gamma_{\ell}\Delta t.
$$

$\Gamma_{\ell}$ is not a free knob; it is taken from the same mismatch/reservoir scale that appears in $c_S$ and $\gamma$.

---

##### Figure: per-tick update pipeline (ordered junction updates)

![Per-tick update pipeline (ordered junction updates).](figs/fig2_tick_flow.png)

---

### 2.1.3h Readout and the T2K real spectral likelihood (Poisson deviance)

Let $n_b$ be observed counts in bin $b$ and $\mu_b(\theta)$ the predicted mean.

If a “no-oscillation” signal template $N_b^{\mathrm{noosc}}$ exists:
$$
\mu_b(\theta)=N_b^{\mathrm{noosc}}\,P_{\mu\to\beta}(E_b;\theta)+B_b.
$$

Default likelihood (Poisson deviance):
$$
\chi^2_{\mathrm{Pois}}(\theta)=2\sum_b\Big[\mu_b-n_b+n_b\ln\frac{n_b}{\mu_b}\Big].
$$

With nuisance pulls (example normalizations $a,b$):
$$
\chi^2(\theta)=\min_{a,b}\Big(\chi^2_{\mathrm{Pois}}(\theta;a,b)+\big(\tfrac{a-1}{\sigma_a}\big)^2+\big(\tfrac{b-1}{\sigma_b}\big)^2\Big).
$$

Define the release-referenced statistic without scanning:
$$
\Delta\chi^2(\theta)=\chi^2(\theta)-\chi^2(\theta_{\mathrm{ref}}),
$$
where $\theta_{\mathrm{ref}}$ is fixed by the official release (or the profile minimum), not discovered by an internal scan.

---

**Update note (2026-02-05).** This subsection formalizes the “ordered junction (time/sense-of-order) + strict bookkeeping + derived gate” picture used in the newer weak-sector forward runners (NOvA/MINOS/T2K). It is meant to replace ad-hoc gate tuning with a *physically grounded* chain: work/pump/leak → mismatch → gate → mixing.

### 2.1.3i CurvedCube holonomy: predicting $\delta_{\mathrm{CP}}$ from geometry (no scan)

This subsection records the current “best falsification-style” weak-sector test: **CurvedCube predicts** $\delta_{\mathrm{CP}}^{\mathrm{geo}}$ with *zero* parameter scans, then we evaluate:

- MINOS spectral $\chi^2$ (Poisson deviance + optional pulls),
- NOvA spectral $\chi^2$,
- T2K official profile penalty $\Delta\chi^2_{\mathrm{T2K}}(\delta_{\mathrm{CP}}^{\mathrm{geo}})$.

#### (i) Deterministic prediction rule

We compute $\delta_{\mathrm{CP}}^{\mathrm{geo}}$ from the CurvedCube transport profile by the holonomy rule in **Box 4** above:

- `u_phase`: $\delta=\arg\left[\frac{1}{N}\sum_{j=1}^{N} u(s_j)\,e^{-i2\pi s_j}\right]$,
- `du_phase`: $\delta=\arg\left[\frac{1}{N}\sum_{j=1}^{N} (\nabla u)(s_j)\,e^{-i2\pi s_j}\right]$.

**Fourier sign convention (important):** throughout this draft we use the first-mode kernel with a **negative** phase, $\sum x(s_j)\,e^{-i2\pi s_j}$. Using $e^{+i2\pi s_j}$ would complex-conjugate the coefficient and flip the reported phase sign; the choice is a convention, but it must be **consistent** across all sections and code.

No tuning is permitted here: the mode choice must be **physically defended** (connection/gradient argument) and then held fixed.

**Implementation note (versioning).** Early exploratory scripts reported $\delta_{\mathrm{CP}}^{\mathrm{geo}}\approx-1.298\,\mathrm{rad}$ at the same nominal inputs. After fixing the ordering/$\phi$ implementation and the T2K profile-key logic, the current runner (`run_curvedcube_predict_dcp_v6.py`) yields $\delta_{\mathrm{CP}}^{\mathrm{geo}}=-1.315523\,\mathrm{rad}$ for the preregistered point used here. All numeric results in this draft refer to **v6** and the console logs provided in Appendix A.

**Why `du_phase` is not “picking the better one”.** The CurvedCube transport profile $u(s)$ is a *displacement-like* readout of the internal/boundary thread network along the path. A genuine geometric phase (holonomy) is associated with a **connection**—i.e., how the local frame/response *changes* along the path—rather than with the absolute displacement itself. In a discretized setting the simplest connection proxy is the **path-gradient** $\nabla u$ (finite difference along the ordered junction schedule). Using $\arg\left[\frac{1}{N}\sum_{j=1}^{N} (\nabla u)(s_j)\,e^{-i2\pi s_j}\right]$ therefore corresponds to “phase from accumulated frame rotation / transport,” while $\arg\left[\frac{1}{N}\sum_{j=1}^{N} u(s_j)\,e^{-i2\pi s_j}\right]$ corresponds to “phase from absolute position,” which is not gauge-invariant under adding a constant offset to $u$.

This difference is empirically visible in the same preregistered point: the control mode `u_phase` predicts $\delta_{\mathrm{CP}}^{\mathrm{geo}}\approx +0.85\,\mathrm{rad}$ and incurs a large T2K penalty ($\Delta\chi^2_{\mathrm{T2K}}\sim 19$), while `du_phase` predicts $\delta_{\mathrm{CP}}^{\mathrm{geo}}\approx -1.316\,\mathrm{rad}$ and falls inside the T2K valley for IH profiles (sub-$1\sigma$). The `u_phase` result is therefore treated as an **ablation/control** demonstrating that “a random phase extractor” does *not* generically match T2K.

#### (ii) How we score (two metrics to avoid sign confusion)

From the spectral runners we parse totals:
$$
\Delta\chi^2_{\mathrm{pack}}(\delta)=\chi^2_{\mathrm{SM}}(\delta)-\chi^2_{\mathrm{GEO}}(\delta),
$$
so **positive** means “GEO improves the spectrum.”

Define
$$
\mathrm{SUM} = \Delta\chi^2_{\mathrm{MINOS}} + \Delta\chi^2_{\mathrm{NOvA}}.
$$

For T2K we use the official $\Delta\chi^2$ profile as a penalty:
$$
\mathrm{T2K\_pen}=\Delta\chi^2_{\mathrm{T2K}}(\delta_{\mathrm{CP}}^{\mathrm{geo}}).
$$

We report two combined metrics (same ingredients, different interpretation):

- **PLUS_PEN (chi2-like; lower is better):** $\mathrm{PLUS\_PEN}=\mathrm{SUM}+\mathrm{T2K\_pen}$
- **SCORE (net-score; higher is better):** $\mathrm{SCORE}=\mathrm{SUM}-\mathrm{T2K\_pen}$

The earlier “COMBINED” label was ambiguous; this paper uses **PLUS_PEN / SCORE** consistently.

#### (iii) Reproducible runs (PowerShell)

All below are **single-shot** evaluations at the predicted $\delta_{\mathrm{CP}}^{\mathrm{geo}}$; there is no $\delta$ scan.

*(CurvedCube δCP prediction commands were removed from the paper’s main text; see the repository’s reproducibility notes if you need to reproduce the δCP prediction runner.)*

#### (iv) Observed outputs (snapshot)

For the preregistered parameter point $A=10^{-3},\,\phi=\pi/2,\,\zeta=0.05,\,k_{rt}=180$:

- The holonomy prediction is stable:
 $$
\delta_{\mathrm{CP}}^{\mathrm{geo}}\approx -1.316\,\mathrm{rad}
$$
 in `du_phase` mode.

- **T2K profile agreement depends on the hierarchy key:**
 - NO uses NH profile; IO uses IH profile.
 - With the correct IH key, the T2K penalty drops dramatically (sub-$1\sigma$ agreement).

Numerical snapshot (from `run_curvedcube_predict_dcp_v6.py`):

- **NO + NH (wRC):** 
 $\mathrm{T2K\_pen}\approx0.437$, $\mathrm{SUM}\approx-0.010$, $\mathrm{PLUS\_PEN}\approx0.427$, $\mathrm{SCORE}\approx-0.447$.

- **IO + IH (wRC):** 
 $\mathrm{T2K\_pen}\approx0.048$, $\mathrm{SUM}\approx-0.010$, $\mathrm{PLUS\_PEN}\approx0.038$, $\mathrm{SCORE}\approx-0.058$.

- **IO + IH (woRC):** 
 $\mathrm{T2K\_pen}\approx0.0057$, $\mathrm{SUM}\approx-0.010$, $\mathrm{PLUS\_PEN}\approx-0.004$, $\mathrm{SCORE}\approx-0.016$.

These results mean: **in IO/IH**, the CurvedCube holonomy predicts a $\delta_{\mathrm{CP}}$ value that is essentially at the T2K best-fit valley, without scanning $\delta$.

#### (v) What is (and is not) implemented about “two thread families”

We *do* encode “internal vs face-mesh” difference via the **fixed geometry weights** $(N_{in},N_{face})=(8,16)$ in the CurvedCube transport profile used to predict $\delta_{\mathrm{CP}}^{\mathrm{geo}}$.

However, a **full two-mode dynamical model** (distinct natural frequencies / damping constants for “edge” vs “bubble” families simultaneously driving the Hamiltonian) is **not yet implemented** in the CurvedCube action; that remains a separate extension (and must be preregistered rather than tuned).

#### (vi) Falsifiable predictions (this draft)

Once the CurvedCube rule is fixed (here: `du_phase`, gate=1, $N_{in}=8$, $N_{face}=16$), the model makes **sharp, falsifiable** statements:

1) **A geometry‑predicted CP phase (no scan).** 
 For the preregistered point used throughout Appendix A,
 $$
(\phi,\zeta,k_{\mathrm{rt}})=\left(\frac{\pi}{2},\,0.05,\,180\right),\qquad (N_{in},N_{face})=(8,16),
$$
 the predicted value is
 $$
\delta_{\mathrm{CP}}^{\mathrm{geo}}=-1.315523~{\mathrm{rad}},
$$
 independent of mass ordering (the prediction comes from the geometry profile, not from $ \Delta m^2$). 
 When evaluated against official T2K $\Delta\chi^2(\delta)$ profiles, this lies **inside** the IH valley:
 $\Delta\chi^2_{\mathrm{T2K}}\approx0.048$ for IH+wRC and $\approx0.006$ for IH+woRC.

2) **A control that fails (ablation).** 
 With the same geometry inputs but using `u_phase` instead of `du_phase`, the predicted phase shifts to
 $\delta_{\mathrm{CP}}^{\mathrm{geo}}\approx +0.85~{\mathrm{rad}}$ and T2K incurs a large penalty
 ($\Delta\chi^2_{\mathrm{T2K}}\sim 19$). This is an explicit “wrong extractor” control.

3) **Within‑runner discretization convergence.** 
 Holding all physics inputs fixed, increasing the internal resolution (e.g. $k_{\mathrm{rt}}=180\to360\to720$) should not change $\delta_{\mathrm{CP}}^{\mathrm{geo}}$ beyond a small tolerance. If it does, the prediction is a numerical artefact and must be rejected.

4) **Near‑null spectral impact at this preregistered point.** 
 At the same predicted $\delta_{\mathrm{CP}}^{\mathrm{geo}}$, MINOS/NOvA spectral differences are tiny in the current runs ($|\Delta\chi^2|\sim10^{-2}$). A later claim of “spectral improvement” must show a non‑tiny effect under the same falsification constraints.

**External outlook.** Future long‑baseline data (Hyper‑K, DUNE) will sharpen the allowed $\delta_{\mathrm{CP}}$ region and can therefore falsify the geometric prediction directly. Independent mass‑ordering measurements (e.g. JUNO) help interpret which T2K profile branch is relevant, but the geometric $\delta_{\mathrm{CP}}^{\mathrm{geo}}$ itself is an ordering‑independent output in this minimal CurvedCube scheme.

---

### 2.2 CurvedCube substrate micro-architecture (formal layer; connects “mechanism” to kernel)

This subsection makes explicit what is otherwise only implicit in the kernel language: **what object in the cube lattice is being summarized** by $(|c_1|,\delta_{\mathrm{geo}})$.

#### 2.2.1 Lattice graph, corners, and RT junctions

Let cubes be nodes $i\in V$ of a graph $G=(V,E)$. Each cube has 8 corners $c\in\{1,\dots,8\}$. For a specific neighbor pair $(i,j)\in E$ that shares a face, define the four corners on the contacting face as sets $F_i$ and $F_j$ (each of size 4). The cube–cube contact is modeled as a **complete bipartite mesh**:
$$
J_{ij}\;=\;\{(a,b):\ a\in F_i,\ b\in F_j\},\qquad |J_{ij}|=4\times4=16.
$$
Each pair $(a,b)\in J_{ij}$ is a “thread” connecting corner $a$ on cube $i$ to corner $b$ on cube $j$.

In addition, each cube carries **bubble spokes** (constant-tension links) from its bubble node $B_i$ to each corner:
$$
(B_i\to c)\quad\text{for all corners }c\in\{1,\dots,8\}.
$$
Optional **internal diagonals** and **edge-frame** links can be added in mechanistic simulations, but the sector tests in this paper only require the *junction topology* above.

#### 2.2.2 Ordered path parameter and “route–register” viewpoint

To summarize a junction neighborhood, the program uses an **ordered traversal** along a path parameter $s\in[0,1]$ (or discrete index $k=1,\dots,N$). Conceptually, this corresponds to an ordered schedule of sub-updates in the route–register map (Sec. 2.1.3), which is one concrete way to represent “time = ordering” without introducing a fundamental time coordinate.

The key point for the kernel is that an ordered traversal induces an oriented loop structure (holonomy), even if the underlying cube graph is locally symmetric.

#### 2.2.3 Complex profile and holonomy summary

Along the ordered path, the model constructs a **complex profile** $u(s)$ (a scalar surrogate for the auxiliary-field phase transport along that route). The kernel compresses $u(s)$ by extracting its first Fourier mode:
$$
c_1\equiv \frac{1}{N}\sum_{j=1}^{N} u(s_j)\,e^{-i2\pi s_j},
\qquad |c_1|\in[0,1],\qquad \delta_{\mathrm{geo}}\equiv \arg(c_1).
$$

**Orientation (holonomy) and CP-odd structure.** 
Because the RT transport is defined on **oriented** routes, the phase $\delta_{\mathrm{geo}}=\arg(c_1)$ is an **oriented-loop holonomy** summary. In the simplest symmetric limit, reversing the traversal order would send $c_1\to c_1^\ast$ and hence $\delta_{\mathrm{geo}}\to -\delta_{\mathrm{geo}}$. In the full ordered/gated update, the map need not be exactly symmetric under reversal, so “clockwise vs counter‑clockwise” traversal can accumulate different effective phases. This is the mechanical slot where CP‑odd effects can enter the weak-sector bridge (without introducing an arbitrary free $\delta_{CP}$ scan).
A preregistered template
$$
T(s)=\cos(2\pi s-\delta_{\mathrm{geo}})\quad\text{or}\quad \sin(2\pi s-\delta_{\mathrm{geo}})
$$
is then used to construct sector-facing modulations via bridge operators (Sec. 2.5 and later).

This “kernel compression” is the practical reason the paper can stay scan-free: the high-dimensional micro-architecture is reduced to a low-dimensional observable object that is **the same across sectors**.

### 2.3 Scattering sectors: forward model as “baseline × modulation”
For scattering datasets binned in a kinematic variable $x$ (e.g., $\cos\theta$ for Bhabha, or $|t|$ for elastic pp), the prediction is written schematically as
$$
y^\mathrm{pred}_i = \beta_{g(i)} \, y^\mathrm{SM}_i \, \mathcal{M}(x_i; \theta_\mathrm{geo}),
$$
where:

- $y^\mathrm{SM}_i$ is the imported SM baseline (from generator/calc),
- $\beta_{g(i)}$ is a group-wise normalization nuisance (e.g., per energy block),
- $\mathcal{M}$ is the geometric modulation, constrained to a low-dimensional parameter set $\theta_\mathrm{geo}$ (including an overall amplitude $A$).

Goodness-of-fit uses a covariance-aware chi-square:
$$
\chi^2 = (y^\mathrm{obs}-y^\mathrm{pred})^T \, C^{-1}\, (y^\mathrm{obs}-y^\mathrm{pred}).
$$

---

#### 2.3.1 Strong sector (bulk-addressed): jitter → complex amplitude, and the energy-axis “clock”

The **strong** instantiation differs from the weak one by *where the state primarily lives*:

- **Weak (edge-addressed):** phase memory accumulates along **edge threads** (holonomy).
- **Strong (bulk-addressed):** the dominant modulation arises from **bulk transport + bulk tensioning**, while the edge network provides the rigid reference frame used for comparison at the interface.

To visualize the strong mechanism, treat the cube–cube interface as a repeated *compare-and-recombine* event.

**(A) Split-path transport (micro story, repeated at each interface)**

When a transport packet leaves cube $i$ and is received at cube $j$, the substrate supports two concurrent components:

1. **Edge component (fast, rigid):** propagates on the skeletal edge network and remains tightly aligned to the local plane-slice reference.
2. **Bulk component (slow, amorphous):** propagates through the bubble/bulk interior, undergoing delay and scattering due to the amorphous manifold.

The receiver therefore sees a **timing mismatch**
$$
\Delta t \equiv t_{\mathrm{bulk}}-t_{\mathrm{edge}},
$$
which is the operational definition of **topological jitter** in this framework.

**(B) Complex response from a single physical mismatch (macro observable)**

A minimal coarse-grained response of the recombined signal is
$$
\mathcal{R}(\Delta t)=e^{-\Gamma\,\Delta t}\,e^{i\Omega\,\Delta t}.
$$
We parameterize this as a **complex effective coupling**
$$
A \equiv A_R + iA_I,
$$
where the identification is:

- $A_I$ (absorptive / “loss”): summarizes $e^{-\Gamma\Delta t}$ (bulk delay + scattering).
- $A_R$ (dispersive / “rotation”): summarizes $e^{i\Omega\Delta t}$ (phase rotation from path difference).

This is not an arbitrary complex fit: it is a macroscopic encoding of **edge–bulk desynchronization**.

**(C) The strong “clock”: environment scaling as interaction frequency**

In strong scattering the natural accumulation axis is not the baseline $L$ (as in weak oscillations) but the **energy axis**: increasing $\sqrt{s}$ effectively increases the number of coherent “attempts” (multi-exchange / saturation-like resummation) during the interaction. We therefore use an accumulation proxy $\mathcal{N}(s)$ (e.g. logarithmic) and interpret it mechanically as the **interaction frequency** with the plane-slice reference:

- the cube does not “know” the beam energy,
- but higher-energy states interrogate the substrate (and its plane anchors) more frequently, producing the observed $\ln(s)$-type scaling.

**(D) Unitarity bookkeeping (no “energy disappearance”)**

If $A_I<0$ reduces elastic-channel flux, the framework must respect unitarity: the missing flux is transferred to inelastic production. Operationally, this is enforced by the **optical-theorem logic** used in the strong bridge: absorptive components control $\sigma_{\mathrm{tot}}$ while dispersive components control $\rho$ and CNI phase structure (see Section 5.2 for the preregistered strong protocol).

**Implementation knobs (strong-facing)**

The strong sector consumes the same kernel outputs $(u(s),c_1,\delta_{\mathrm{geo}})$ but uses a bulk-addressed bridge with explicit environment scaling. The main knobs that appear in reproducible runs are:

- $A_R,A_I$ : dispersive/absorptive couplings,
- $\phi$ : internal twist (chirality) that shapes the kernel profile $u(s)$,
- $\zeta$ : geometric temperature / friction (damping strength),
- $\mathcal{N}(s)$ : energy-axis accumulation proxy (environment “clock”),
- $t_{\mathrm{ref}},t_{\max},R_{\max}$ : preregistered mappings for $t\rightarrow s(t)$ and kernel support.

### 2.4 EM bridge philosophy (Bhabha): shape-only + anchoring, not free normalization

In EM scattering, the natural observable is a **differential cross section**. The bridge used here is deliberately minimal:

- start from an imported SM/baseline curve per bin,
- allow only per-energy-block normalizations $\beta_g$ as nuisance,
- apply geometry as a **shape deformation** $(1+\delta_i)$,
- enforce “anti-normalization” either by per-group mean removal (`shape_only`) or (preferably) by a preregistered **pivot-centering** anchor $\delta\leftarrow\delta-\delta(x_p)$.

This is the EM analogue of the “no scan / preregistered knobs” rule: geometry is not allowed to win by renormalizing the dataset, only by changing angular **shape** in a constrained way.

A single additional *protocol* parameter appears here: the **junction stiffness** $\kappa_{\mathrm{junc}}$ in the bounded filter $J(\tau;\kappa_{\mathrm{junc}})$, which damps the deformation in the extreme forward regime ($\tau\to 0$). The intended falsification workflow is: determine (or preregister) $\kappa_{\mathrm{junc}}$ in EM, then hold it fixed when stress-testing other sectors—so it is not a per-sector “fit knob,” but a vacuum-lattice property.

#### 2.4.1 Junction-addressed EM mechanism (Bhabha “animation”): stiffness + pivot-centering

This subsection makes the EM bridge **mechanical**, not “black-box statistical”.

**Objects.** Each Bhabha bin $i$ has an angle $x_i\equiv\cos\theta_i$ and belongs to an energy block (group) $g(i)$ (e.g. 200/202/205/207 GeV blocks). We import a baseline curve $y^{\mathrm{SM}}_i$ (BHAGEN-like) for each bin.

**Prediction model (shape-only).**
We only allow a per-group nuisance normalization $\beta_g$ and a bounded geometric *shape* deformation $\delta_i$:
$$
y^{\mathrm{pred}}_i \;=\; \beta_{g(i)}\,y^{\mathrm{SM}}_i\,[1+\delta_i].
$$
The geometric deformation is produced by the CurvedCube transport output $u_i$ and then **regularized at the junction**:
$$
\delta_i \;=\; A\;\mathrm{env\_scale}\;\underbrace{J(\tau_i;\kappa_{\mathrm{junc}})}_{\text{junction stiffness filter}}\;u_i,
\qquad \tau_i \equiv 1-\cos\theta_i.
$$

- $\tau\to 0$ is the extreme-forward regime. $J(\tau;\kappa_{\mathrm{junc}})$ is bounded and suppresses unphysical blow-ups in that limit.
- Mechanically: $\kappa_{\mathrm{junc}}$ is the **resistance of the face-handshake** against misaligned / out-of-order 16-thread connections. (It is the EM “traffic cop”.)

**Why the “junction” is the right address.**
In this framework, EM lives on the **inter-cube face mesh**:

- crossing from cube $A$ to cube $B$ is a **face event** with a 16-channel bus $U_{AB}\in\mathbb C^{4\times4}$,
- the global planes slice this interface, so the handshake is evaluated at a **plane–junction intersection**,
- stiffness $\kappa_{\mathrm{junc}}$ penalizes non-causal ordering and filters unstable forward configurations.

**Anti-normalization / anchoring (pivot-centering).**
“Shape-only” must be enforced explicitly; otherwise a tiny DC offset can masquerade as a physics effect and (worse) can create the old mid/forward sign-tension.

Define a *group-wise* fractional residual:
$$
\delta^{\mathrm{raw}}_i \;\equiv\; \frac{y^{\mathrm{data}}_i}{\beta_{g(i)}\,y^{\mathrm{SM}}_i}-1.
$$
Then impose the preregistered **pivot anchor** at a fixed boundary point $x_{\mathrm{pivot}}$ (used in the runs: $x_{\mathrm{pivot}}=0.72$, the mid/forward boundary):
$$
\delta^{\mathrm{center}}(x) \;=\; \delta^{\mathrm{raw}}(x)\;-\;\delta^{\mathrm{raw}}(x_{\mathrm{pivot}}),\qquad x_{\mathrm{pivot}}=0.72.
$$
Interpretation: the bridge is not allowed to win by “floating the whole curve”; it must win by a differential distortion relative to a fixed angular anchor.

**Holdout protocol (what makes it falsifiable).**
For band-holdouts (mid vs. forward), the nuisance $\beta_g$ is **trained once** and then **frozen** on the held-out band. This prevents the EM bridge from “explaining away” the test region by renormalization.
A correct wiring has three forced outcomes:

- $A=0$ gives $\Delta\chi^2=0$ in a strict pivot-centered holdout (sanity).
- $A>0$ and $A<0$ must flip the sign of test $\Delta\chi^2$ (sign-falsifier).
- forward and mid holdouts must agree on the **same sign** under the same preregistered anchor (the pivot is what fixed the historical mid/forward tension).

**Numerical conditioning note (EM-specific).**
Because correlated systematics can make $C_{\mathrm{sys},corr}$ near-singular, we report both `total` and `diag_total` variants and require *sign-consistency* across them. The stiffness filter $J(\tau;\kappa_{\mathrm{junc}})$ is not a numerical trick: it is the **physical forward regulator** (junction resistance) that also improves conditioning by suppressing the $\tau\to 0$ sensitivity.

### 2.5 Geometric substrate kernel: CT/RT thread network + auxiliary-field gating

Across sectors we use the same underlying object: a **geometric/mechanical kernel** $K_\Theta$ produced by a discrete cubic substrate with an embedded “bubble” node per cube and two families of threads:

- **CT (constant-tension) threads**: one-sided (tension-only) rope-like links (no compression).
- **RT (restoring-tension) threads**: one-sided links that behave as a rope with slack, but add a spring-like restoring term when stretched; these are the *inter-cube* couplers that largely set the collective mode scale. 
 In the current “new geometry” baseline used for falsification scans we take $k_{\mathrm{rt}}=100$ (model units) as the working stiffness scale.

> **Important:** $k_{\mathrm{rt}}$ is a *model-unit stiffness scale inside the substrate kernel*. The value $k_{\mathrm{rt}}=100$ cited here is the working scale used in the time-domain kernel simulations (GW pipeline). In the weak CurvedCube holonomy runs we use a **separately preregistered discretization parameter** (e.g. $k_{\mathrm{rt}}=180$) inside the path sampler. These are not directly comparable numbers across sectors; only *within-sector* convergence checks (e.g. 180→360→720 in the same runner) are meaningful.

This kernel is used in two ways:
1) **Time-domain** (GW ringdown): simulate $u(t)\rightarrow (h_+(t),h_\times(t))\rightarrow$ detector projection.
2) **Frequency-domain** (weak/strong/EM modulation): use the same substrate as a *susceptibility generator* $\chi(\omega;\Theta)$ that enters the geometric phase-gradient / modulation functions.

#### 2.5.1 Discrete geometry and indexing maps

We consider an $n_x\times n_y\times n_z$ array of cubes of edge length $L_0$. 
Each cube $(c_x,c_y,c_z)$ has:

- 8 **corner nodes** $i=\mathrm{idx\_corner}(c_x,c_y,c_z,\nu)$, $\nu\in\{0,\dots,7\}$
- 1 **bubble node** $b=\mathrm{idx\_bubble}(c_x,c_y,c_z)$ at the cube center.

Rest positions:
$$
\mathbf{x}^{(0)}_{\mathrm{corner}}=\mathbf{x}^{(0)}_{\mathrm{center}}+\boldsymbol{\delta}_\nu,\qquad
\mathbf{x}^{(0)}_{\mathrm{bubble}}=\mathbf{x}^{(0)}_{\mathrm{center}},
$$
with $\boldsymbol{\delta}_\nu\in\{\pm \tfrac{L_0}{2}\}^3$. The dynamical positions are $\mathbf{x}_i(t)=\mathbf{x}^{(0)}_i+\mathbf{u}_i(t)$.

#### 2.5.2 CT (tension-only) threads

For each CT link $\ell=(i,j)$ with tension scale $T_\ell$, damping $c_\ell$, and softening $\varepsilon_\ell$, define
$$
\mathbf{r}_{ij}=\mathbf{x}_j-\mathbf{x}_i,\quad d_{ij}=\|\mathbf{r}_{ij}\|,\quad \hat{\mathbf{n}}_{ij}=\mathbf{r}_{ij}/(d_{ij}+\epsilon),
$$
and the **one-sided** force (always pulling, never pushing):
$$
\mathbf{F}^{\mathrm{CT}}_{i\leftarrow j}
=\max\!\left(0,\;T_\ell\,\tanh\!\frac{d_{ij}}{\varepsilon_\ell}\;+\;c_\ell\,(\Delta\mathbf{v}_{ij}\!\cdot\!\hat{\mathbf{n}}_{ij})\right)\hat{\mathbf{n}}_{ij},
\qquad \Delta\mathbf{v}_{ij}=\mathbf{v}_j-\mathbf{v}_i.
$$
We apply Newton’s third law: $\mathbf{F}_{j\leftarrow i}^{\mathrm{CT}}=-\mathbf{F}_{i\leftarrow j}^{\mathrm{CT}}$.

**CT connectivity in the “new geometry”.**

- Bubble–corner: 8 CT links per cube with tension $T_{\mathrm{cb}}$.
- Corner–corner inside each cube: CT links classified by rest-distance:
 - edge links ($1$) with tension $T_{\mathrm{edge}}$,
 - face-diagonals ($\sqrt2$) with tension $T_{\mathrm{face}}$,
 - body-diagonals ($\sqrt3$) with tension $T_{\mathrm{body}}$.

#### 2.5.3 RT (stretch-only spring) inter-cube threads and “rt_face_diagonals=16”

An RT link $e=(i,j)$ carries parameters $(L_{0,e},k_e,p_e,c_e,T_{0,e})$. With stretch $s_{ij}=d_{ij}-L_{0,e}$,
$$
T^{\mathrm{RT}}(s_{ij})=T_{0,e}+\mathbf{1}_{s_{ij}>0}\,k_e\,s_{ij}^{p_e},
\qquad
\mathbf{F}^{\mathrm{RT}}_{i\leftarrow j}
=\max\!\left(0,\;T^{\mathrm{RT}}(s_{ij})+c_e(\Delta\mathbf{v}_{ij}\!\cdot\!\hat{\mathbf{n}}_{ij})\right)\hat{\mathbf{n}}_{ij}.
$$

Across each shared face we connect the 4 face corners on cube A to the 4 opposing corners on cube B:

- Default (“straight”): 4 links (one-to-one corner pairing).
- With `rt_face_diagonals`: add three additional 4-permutations, yielding **16 links per shared face**.

Explicitly, if the face corner lists are ordered as $f_A=[a_0,a_1,a_2,a_3]$ and $f_B=[b_0,b_1,b_2,b_3]$, we add four matchings:

- identity: $(a_i\leftrightarrow b_i)$
- perm1: $(a_i\leftrightarrow b_{p^{(1)}_i})$, $p^{(1)}=[1,3,0,2]$
- perm2: $(a_i\leftrightarrow b_{p^{(2)}_i})$, $p^{(2)}=[2,0,3,1]$
- perm3: $(a_i\leftrightarrow b_{p^{(3)}_i})$, $p^{(3)}=[3,2,1,0]$

The union of these four matchings yields the full $4\times4$ bipartite coupling (every $a_i$ connects to all $b_j$).

#### 2.5.4 Optional bubble–corner repulsion (REP1) and anisotropic cutoff modulation

To introduce a conservative “compression/repulsion” channel, add a short-range bubble–corner repulsion active only for $d<R_{\mathrm{rep}}$. For each bubble–corner pair $(b,c)$:
$$
\mathbf{r}_{bc}=\mathbf{x}_c-\mathbf{x}_b,\quad d=\|\mathbf{r}_{bc}\|,\quad \hat{\mathbf{n}}_{bc}=\mathbf{r}_{bc}/(d+\epsilon).
$$
Define overlap $\delta = R_{\mathrm{rep}}-d$. For $\delta>0$,
$$
\|\mathbf{F}^{\mathrm{rep}}\|
= k_{\mathrm{rep}}\delta^{\,p_{\mathrm{rep}}},
\qquad
\mathbf{F}^{\mathrm{rep}}_{b\leftarrow c}=-\mathbf{F}^{\mathrm{rep}}_{c\leftarrow b}
= \|\mathbf{F}^{\mathrm{rep}}\|\,\hat{\mathbf{n}}_{bc},
$$
and for $\delta\le 0$ the force is zero.

A matching potential-energy form (useful for strict energy-closure tests when damping is disabled) is
$$
U_{\mathrm{rep}}(d)=
\begin{cases}
\dfrac{k_{\mathrm{rep}}}{p_{\mathrm{rep}}+1}\,(R_{\mathrm{rep}}-d)^{p_{\mathrm{rep}}+1}, & d<R_{\mathrm{rep}},\\[6pt]
0,& d\ge R_{\mathrm{rep}}.
\end{cases}
$$

**Amorph / anisotropic cutoff (optional).** 
A minimal geometric anisotropy can be introduced by modulating the effective cutoff radius in the transverse plane:
$$
R_{\mathrm{eff}}(\theta)=R_{\mathrm{rep}}\Bigl[1+\eta_R\bigl(q_+\cos 2\theta+q_\times\sin 2\theta\bigr)\Bigr],
$$
with clipping $R_{\mathrm{eff}}\in[R_{\min}R_{\mathrm{rep}},R_{\max}R_{\mathrm{rep}}]$ for numerical stability.

#### 2.5.5 Gauge-plane gating on a plane (TT2 / auxiliary field layer)

In this paper, the **gauge plane** is realized as an auxiliary field layer $\phi$ defined on an interface plane. The field produces a gate $g(\phi)\in[0,1]$ that scales only RT links crossing that plane.

An auxiliary field layer $\phi$ defined on an interface plane produces a gate $g(\phi)\in[0,1]$ that scales only RT links crossing that plane:
$$
k_e\rightarrow g(\phi_{\mathrm{cell}})k_e,\qquad g(\phi)=\frac{1}{1+\exp\{-\beta(|\phi|-\phi_0)\}}.
$$

#### 2.5.6 Kernel entry into weak/scattering

In the frequency domain we define a (small) linear susceptibility on the substrate:
$$
\chi_{ab}(\omega;\Theta)=\mathbf{r}_a^\top\bigl(-\omega^2\mathbf{M}+i\omega\mathbf{C}+\mathbf{K}_{\mathrm{eff}}(\Theta)\bigr)^{-1}\mathbf{s}_b,
$$
where $\Theta$ collects micro-geometry parameters (CT/RT stiffnesses, damping, repulsion settings, and gate parameters), $\mathbf{s}_b$ is a chosen drive pattern, and $\mathbf{r}_a$ is a chosen readout pattern. In practice we use a **scalarized response**
$$
R(\omega;\Theta)=\mathrm{scalarize}\bigl(\chi(\omega;\Theta)\bigr)=|R(\omega)|\,e^{i\delta(\omega)},
$$
where the scalarization is sector-dependent but *explicit* (examples below).

A single “response coordinate” $s$ is used to apply the kernel across sectors. The mapping $s=s(x)$ depends on the sector’s natural independent variable $x$:

- **weak:** $x=L$ (baseline length), so $s=L$ (km).
- **EM (Bhabha):** $x=\cos\theta$ (bin mid), and we use the forwardness proxy $s=\tau=1-\cos\theta$.
- **strong (elastic):** $x=t$ (momentum transfer), and we use a nondimensional proxy $s=\tau_t=|t|/t_{\mathrm{ref}}$.
- **GW (ringdown):** $x=t$ (time), so $s=t$ (seconds) and the micro-simulator directly outputs $h_+(t),h_\times(t)$.

With this common coordinate $s$, the “geometric phase drive” used in the forward models is:
$$
\Phi(s)=\omega\,s + \phi + \delta(\omega),\qquad
\mathrm{atten}(s)=\exp\!\left(-\frac{|s-s_0|}{\alpha}\right),
$$
and the code-faithful scalar phase-gradient term is
$$
\mathrm{base\_dphi\_ds}(s)=\mathrm{amp}(x)\; g_{\mathrm{eff}}\;|R(\omega)|\;\omega\;\cos\!\bigl(\Phi(s)\bigr)\;\mathrm{atten}(s),
$$
where $\mathrm{amp}(x)$ is the sector’s amplitude map (e.g. $\mathrm{amp}(E)=\sqrt{E_0/E}$ in weak, or a constant in some scattering experiments), and $g_{\mathrm{eff}}=g_{\mathrm{bp}}+g_{\mathrm{lp}}$ is a (locked) effective coupling. (bubble–plane and lock‑plane coupling; see §7.6; both are set to 0 in prereg weak/EM/strong verdict runs).

##### Sector-specific observable mappings (explicit)

**Weak (neutrinos).** The kernel enters as a small phase-gradient shift that is converted to an effective mass-splitting deformation:
$$
\delta(\Delta m^2)_{\mathrm{geo}}(L,E)=\frac{2E}{L}\,\delta\phi_{\mathrm{geo}}(L,E),\qquad
\delta\phi_{\mathrm{geo}}(L,E)=\int_{0}^{L}\mathrm{base\_dphi\_dL}(L',E)\,dL'.
$$
In the simplest implementation this becomes an additive term in the vacuum Hamiltonian (or directly in the phase evolution), preserving the GKSL structure.

**EM (Bhabha) and strong (elastic) “baseline×modulation”.** The kernel produces a bounded multiplicative modulation applied to a frozen baseline curve:
$$
y^{\mathrm{pred}}(x)=\beta_g\,y^{\mathrm{base}}(x)\,\Bigl[1 + A\,\mathcal{M}(x;\Theta)\Bigr],
$$
with $|A\,\mathcal{M}|\ll 1$ enforced by priors and scan bounds. Here
$$
\mathcal{M}(x;\Theta)=J(\tau;\kappa_{\mathrm{junc}})\,\mathrm{base\_dphi\_ds}\bigl(s(x)\bigr),
$$
where $J(\tau;\kappa_{\mathrm{junc}})=\tau/(\tau+\kappa_{\mathrm{junc}})$ is the **junction filter** (used in EM and optional elsewhere), and $\tau$ is the sector’s forwardness/interaction-strength proxy ($\tau=1-\cos\theta$ for EM; $\tau_t=|t|/t_{\mathrm{ref}}$ for strong). The normalization convention for $\mathcal{M}$ (and whether it uses $\cos\Phi$ or an averaged magnitude) is kept fixed within a sector and reported in the CLI mapping tables.

**GW (ringdown).** The GW simulator provides $(h_+(t),h_\times(t))$ directly from the micro substrate. The mapping to detector $d$ uses antenna patterns and geometric delays:
$$
h_d(t)=F^d_+(\alpha,\delta,\psi)\,h_+(t-\tau_d)+F^d_\times(\alpha,\delta,\psi)\,h_\times(t-\tau_d).
$$
The falsification metrics are then applied on bandpassed/whitened windows of $h_d(t)$ (see §6.0.3).

This section is intentionally explicit: “sector-dependent readout” means only **(i)** the coordinate map $s(x)$ and **(ii)** the scalarization choice $R(\omega)$, both of which are listed and kept fixed when scanning $(A,\alpha,\kappa_{\mathrm{junc}},\dots)$.

#### 2.5.7 Implementation map (named functions and data structures)

The paper’s $\mathrm{idx\_corner}$, $\mathrm{idx\_bubble}$, and face-coupling rules correspond directly to a minimal set of implementation utilities:

- `idx_corner(cx,cy,cz, corner_id)` / `decode_corner(corner_id)`: forward/backward maps between cube-local corner IDs and global node indices.
- `build_model(...)`: constructs $\mathcal{E}_{\mathrm{CT}}$ (bubble–corner + intra-cube corner graph) and $\mathcal{E}_{\mathrm{RT}}$ (inter-cube face couplers).
- `add_face_links(...)` with `rt_face_diagonals`: generates the 4 matchings that realize 16 links per face.
- `precompute_plane_rt_scales(...)` + `gate_from_phi(...)`: assigns plane-crossing RT links to plane cells and computes $s_{ij}(\phi)=g(\phi_{\mathrm{cell}})$.

Keeping these maps explicit is part of the falsification stance: topology is fixed and auditable; parameter scans vary only $\Theta=\{k_{\mathrm{rt}},\gamma,\dots\}$ within a fixed graph.

---

### 2.6 One-line unified equation used across sectors

$$
\boxed{
\frac{d\rho}{dL}
=
-i\bigl[H_{\mathrm{vac}}+H_{\mathrm{mat}}+H_{\mathrm{geo}}(\chi(\omega;\Theta)),\rho\bigr]
+\sum_j \Gamma_j\,\mathcal{D}L_j,\qquad
H_{\mathrm{geo}}\equiv \mathrm{env\_scale}(L)\,A\,\mathcal{G}(\chi(\omega;\Theta)).
}
$$

#### (v) 3D plane-slice visualization (edge-addressed; “global slicers”)

To make the weak-sector mechanism **visually reconstructible**, interpret the “global planes” as 3D families of reference slices (vertical + horizontal) that intersect every cube–cube face. The weak-sector state is **edge-addressed**: it propagates primarily on the rigid skeleton (edge threads), while the planes provide the phase-reference that enforces gauge continuity at each face.

**Connectivity rules (what exists / what does not):**

- **Plane ↔ cube (YES):** each cube’s bubble node couples to the plane reference through internal/bulk anchor threads (localization/identity reference).
- **Plane ↔ plane (NO direct wires):** parallel planes do not connect by “skipping the cubes”; any phase/stress coupling is **mediated** by the cube lattice (RT skeleton).

**Single-hop storyboard (Cube A → Cube B):**

- **Frame 0 (departure):** bubble $A$ holds a local phase reference relative to the nearest plane slice.
- **Frame 1 (edge propagation):** the neutrino state advances along an edge-thread segment toward the face $A\leftrightarrow B$.
- **Frame 2 (plane-sliced face handshake):** at the face, the 16-thread bus compares the 4-component boundary states $\psi_A^{\mathrm{face}}$ and $\psi_B^{\mathrm{face}}$ on that plane slice.
- **Frame 3 (connection accumulation):** the face update contributes a *connection-like* increment (finite-difference) to the ordered path record.
- **Frame 4 (loop closure):** over many hops the ordered sequence closes an effective loop; the net oriented content is extracted as $\delta_{\mathrm{CP}}^{\mathrm{geo}}$.

#### (v*) Where the gauge “pattern” lives (code-faithful) and how we visualize it

A frequent confusion point is whether the “gauge pattern” is *painted on cube faces* or lives *on the planes*. In the **current implementation used for the preregistered tests**, we do **not** store an explicit 2D bitmap/graph on each plane. Instead, the plane enters as an **operator evaluated at the plane-slice cell that an RT crossing intersects**:

- **Crossing operator (effective):** $s_{ij}=g(\phi_{\mathrm{cell}})$ multiplies (or conditions) the face-to-face RT coupling only **during the crossing**; the 16-thread bus itself is not “wired into the plane.”
- **Junction conditioning (EM/QEM):** $\kappa_{\mathrm{junc}}$ acts as a stiffness/threshold/filter at the interface, rejecting out-of-order or non-causal junction configurations.
- **Ordering/localization reference:** the Lock Plane is **global** and functions as a reference schedule (time-order) and localization anchor; it is not a local per-cube patch.

So the “pattern” is best understood as a **mapping**
$$
(\text{plane family},\ \text{slice index},\ \text{junction / face id}) \longmapsto \{\text{magnitude},\ \text{phase},\ \text{acceptance}\},
$$
rather than a literal painted texture. **A cube “sees” the pattern only at crossings** (and only through the induced gate/phase/ordering conditions).

**Figure language (recommended):** to make this film-like without changing the math, we render that mapping in one of three standard 2D encodings (you can mix them per panel):

1. **Scalar heatmap** (cell color): $|s_{ij}|$ or $\kappa_{\mathrm{junc}}$ or $\zeta$ to show “where transport is easy vs hard.”
2. **Phasor glyphs** (tiny arrows/wheels): $\arg(s_{ij})$ or accumulated holonomy phase to show interference structure directly.
3. **Vector/quiver field** (arrows): EM/Q/U-like direction information when discussing polarization-like readouts.

This is intentionally **explanatory** (diagrammatic) and does not introduce new fitted parameters; it is consistent with the operator-level plane-slice picture used throughout the tests.

**Why `du_phase` matches this picture.** The holonomy lives in the *connection* (how the local frame changes), not in an absolute displacement. The discrete gradient $\nabla u$ is therefore the minimal “connection proxy,” so `du_phase` is the correct phase extractor in an edge-addressed transport picture.

#### (vi) From holonomy to interference: “pattern vs threshold” (what sets the probability)

In the weak sector the **pattern** is a phase-memory effect (holonomy). The **accept/reject** of a given configuration is controlled separately by the gate stiffness.

- **Pattern (holonomy):** geometry produces an oriented phase via a Wilson-loop–like object
$$
W_{\mathrm{geo}}\;\sim\;\mathrm{Tr}\!\left(\prod_{(i\to j)\in \mathcal{C}} U_{ij}\right),\qquad
\delta_{\mathrm{CP}}^{\mathrm{geo}}=\arg(W_{\mathrm{geo}}),
$$
where $\mathcal{C}$ is the ordered closed circuit defined by the junction schedule, and $U_{ij}\in\mathbb C^{4\times4}$ is the 16-thread face transport tensor.

- **Threshold (gate stiffness):** once the phase pattern is formed at a face, the junction/plane filter enforces a mismatch penalty via $\kappa_{\mathrm{gate}}$ (and, in EM, $\kappa_{\mathrm{junc}}$). This is what turns “phase coherence” into an observable probability contribution.

This resolves a common confusion: **interference/phase comes from split-path/connection geometry; pass/fail comes from stiffness gating**. They are different operators.

#### (vii) Ordering (NO vs IO): what is claimed vs what is not

This draft treats $\delta_{\mathrm{CP}}^{\mathrm{geo}}$ as a **single-shot geometry output** that is *ordering-independent* in the sense that it is not computed using $\Delta m^2$ sign inputs. The ordering label enters only through the **external experimental profile choice** (NH vs IH, wRC vs woRC) used for the T2K penalty.

Therefore:

- Any apparent preference (e.g., smaller $\Delta\chi^2$ under IH profiles at the preregistered $\delta_{\mathrm{CP}}^{\mathrm{geo}}$) is reported as a **testable coincidence** tied to the published profile shapes.
- A genuine “geometric ordering mechanism” would require promoting an explicit operator that couples chirality $\phi$ to the mass-basis mapping (beyond the present prereg set). This is logged as an open falsification target rather than claimed here.

## 3. EM dataset and baseline construction (LEP Bhabha)

This EM test is intentionally **falsification-first** and **scan-free**: we do not grid-search $(A,\kappa_{\mathrm{junc}},\dots)$ to “win”.
Instead we preregister the **bridge operator**, the **covariance choice**, and a small set of locked hypotheses (NULL vs GEO plus a sign-flip falsifier).

### 3.1 Dataset (HEPData) and pack definition

- Process: $e^+e^-\to e^+e^-$ (Bhabha).
- Observable: binned differential cross section vs. $\cos\theta$ (60 bins total).
- Data CSV: `lep_bhabha_table18_clean.csv`
- Pack: `lep_bhabha_pack.json`
- Imported baseline curve: `bhagen_cos09_v4_baseline_L0_Sp1.csv` (column `sm_pred_pb`) with group label `group_id`.

**Block grouping (baseline-consistent):** 4 energy blocks (15 bins each), treated as 4 “groups” $g=0,1,2,3$.
The baseline file contains the per-bin SM prediction and the group membership used by the runner.

### 3.2 Groupwise normalization nuisance ($\beta_g$) and “freeze” discipline

We allow an overall normalization per group to absorb acceptance/normalization differences that are not the target of this test:

$$
\sigma^{\mathrm{SM}}_i \equiv \beta_{g(i)}\,\sigma^{\mathrm{base}}_i,
\qquad
\sigma^{\mathrm{GEO}}_i \equiv \beta_{g(i)}\,\sigma^{\mathrm{base}}_i\,(1+\delta_i).
$$

- $\beta_g$ are fitted by minimizing $\chi^2$ (nonnegative constraint optional).
- In **preregistered GEO** runs we typically set `--freeze_betas`, i.e. we reuse the SM-fit $\beta_g$ and do **not** refit them under geometry. 
 This prevents “nuisance leakage” where geometry wins by re-choosing normalizations.

### 3.3 Covariance model used in this draft

We expose covariance choices explicitly (so the test is falsifiable and reproducible):

**(a) Full covariance (`--cov total`, recommended):**
$$
C_{\mathrm{total}}=C_{\mathrm{stat}}+C_{\mathrm{sys}},
$$
with
$$
C_{\mathrm{stat}}=\mathrm{diag}(\sigma_{\mathrm{stat},i}^2),\qquad
\sigma_{\mathrm{stat},i}\equiv \frac{|\delta\sigma^+_i|+|\delta\sigma^-_i|}{2},
$$
and two correlated systematic sources (as encoded by the pack):
$$
C_{\mathrm{sys}}=\Delta^{(1)}(\Delta^{(1)})^T+\Delta^{(2)}(\Delta^{(2)})^T,\qquad
\Delta^{(k)}_i \equiv ({\mathrm{sys}}k\_{\mathrm{rel},i})\,\sigma_{\mathrm{obs},i}.
$$

**(b) Diagonalized check (`--cov diag_total`):**
$$
C_{\mathrm{diag}\_total}\equiv \mathrm{diag}(C_{\mathrm{total}}).
$$

These are implemented via the supplied matrices:
`lep_bhabha_cov_stat.csv`, `lep_bhabha_cov_sys_corr.csv`, `lep_bhabha_cov_total.csv`, and `lep_bhabha_cov_diag_total.csv`.

---

## 4. EM bridge and preregistered results (Bhabha)

### 4.1 EM bridge operator (code-faithful)

The deformation $\delta_i$ is built from a momentum-transfer proxy $|t_i|$ (massless approximation within each group):

$$
|t_i|\ \approx\ \frac{s_g}{2}\,(1-\cos\theta_i),
\qquad \sqrt{s_g}\equiv E_{\mathrm{cm},g}\;\;(\text{so }s_g\equiv E_{\mathrm{cm},g}^2).
$$

A log-response driver:
$$
f_i \equiv \alpha_{\mathrm{map}}\,\ln\!\Big(\max(|t_i|/t_{\mathrm{ref}},\,1)\Big)\ \ge 0,
$$
and a bounded support factor:
$$
R_i \equiv R_{\max}\left(1-e^{-\zeta |f_i|}\right).
$$

A bounded **junction stiffness filter** (vacuum regulator) is applied in the forward regime using the proxy
$$
\tau_i\equiv 1-\cos\theta_i\in[0,2],\qquad
J_i\equiv J(\tau_i;\kappa_{\mathrm{junc}})=\frac{\tau_i}{\tau_i+\kappa_{\mathrm{junc}}},
$$
so $J_i\to 0$ as $\tau_i\to 0$ (very forward) and $J_i\to 1$ away from the forward limit.

With preregistered structure/generator scalars:
$$
s_{\mathrm{struct}}=
\begin{cases}
+1,& \mathtt{diag}\\
-1,& \mathtt{offdiag}
\end{cases},
\qquad
g_{\mathrm{gen}}=
\begin{cases}
0.5,1.0,1.5,2.0,& \mathtt{lam1},\mathtt{lam2},\mathtt{lam4},\mathtt{lam5}
\end{cases},
$$
the raw deformation is
$$
\delta_{{\mathrm{raw}},i}
=
{\mathrm{env}\_scale}\cdot A_{\mathrm{EM}}\cdot s_{\mathrm{struct}}\cdot g_{\mathrm{gen}}\cdot \sin\phi\cdot J_i\cdot R_i\cdot f_i.
$$

**Shape-only constraint (anti-normalization):**
in `--shape_only` mode we enforce per-group zero-mean deformation:
$$
\delta_i \leftarrow \delta_{{\mathrm{raw}},i}-\langle\delta_{\mathrm{raw}}\rangle_{g(i)}.
$$

**Pivot-centering variant (used in the strongest holdout checks):**
to remove the normalization-like component by a *single anchor bin* rather than a group mean, we use
$$
\delta_i \leftarrow \delta_{{\mathrm{raw}},i}-\delta_{\mathrm{raw}}(x_p;\sqrt{s_{g(i)}}),
\qquad x_p\equiv \cos\theta_p\ \text{(preregistered, here }x_p=0.72\text{)}.
$$
In the code this is `--center_mode pivot_cos --center_cos 0.72`.
(When pivot-centering is active, the runner ignores mean-subtraction because the pivot already removes the DC component.)
#### 4.1.1 U(1) plane-cell addressing and runtime gate pipeline (EM and QED share the same plane)

In the unified lattice picture, EM and QED are represented on the **same U(1) auxiliary layer**. A cube↔cube RT crossing does **not** add a new wire to the graph; it **samples** a plane-cell state and conditions the local transfer at the moment of crossing.

**Addressing.** For a crossing, define a macro plane-cell address
$$
c_{\mathrm{macro}}=(axis,\;slice\_id,\;u,\;v),
$$
and (when needed) a micro address encoding the 16-port corner↔corner mapping:
$$
c_{\mathrm{micro}}=(axis,\;slice\_id,\;u,\;v,\;u_\mu,\;v_\mu).
$$
Corner ports $p$ map to $(a,b)\in\{0,1\}^2$. A port-pair $(p_{\mathrm{in}},p_{\mathrm{out}})$ maps to the 4×4 micro indices by
$$
u_\mu = 2a_{\mathrm{in}}+a_{\mathrm{out}},\qquad v_\mu = 2b_{\mathrm{in}}+b_{\mathrm{out}}.
$$

**Cell state (minimal scalars).** The addressed cell carries at least
$$
(\phi_{\mathrm{cell}},\;\kappa_{\mathrm{cell}},\;\tau_{\mathrm{cell}},\;\zeta_{\mathrm{cell}}),
$$
interpretable as a $\phi$-gate phase/conditioning, EM/QED stiffness (threshold/penalty), ordering reference, and damping/temperature proxy.

**Canonical single-crossing operator (spec layer).** For a crossing addressed to cell $c$ at time $t$, define the effective complex factor
$$
U_{\mathrm{eff}}(c,t)
=
M_{\mathrm{ord}}\!\big(\tau_{\mathrm{cell}}(c,t)\big)\cdot
G_\phi\!\big(\phi_{\mathrm{cell}}(c,t)\big)\cdot
D_{\mathrm{split}}(c,t)\cdot
F_\kappa\!\big(\kappa_{\mathrm{cell}}(c,t)\big),
$$
with split-path recombination (edge-fast vs bulk-slow)
$$
D_{\mathrm{split}}(c,t)
=
w_e(c,t)\;+\;
w_b(c,t)\,e^{-\Gamma \Delta t(c,t)}\,e^{i(\Omega \Delta t(c,t)+\phi_{\mathrm{cell}}(c,t))}.
$$
The stiffness field is sourced from local thread crowding:
$$
\kappa_{\mathrm{cell}}(c,t)=\kappa_0+\lambda\,\rho_{\mathrm{thread}}(c,t).
$$
Branch weights are computed **at runtime** (no pre-enumerated paths) using a single sigmoid split:
$$
S(\kappa)=\frac{1}{1+\exp\!\big[-(\kappa-\kappa_\ast)/s_\kappa\big]},
\qquad
w_e=\sqrt{S(\kappa)}\,M_{\mathrm{ord}},
\qquad
w_b=\sqrt{1-S(\kappa)}\,M_{\mathrm{ord}}.
$$
Repeated application of sparse junction updates generates the effective multi-path sum automatically (no explicit enumeration).

**Code-faithful note (current EM Bhabha implementation).** The present Bhabha runner implements a **1D reduction** of the above plane-cell pipeline, in which each data bin $i$ effectively addresses a single “cell” labeled by $\tau_i=1-\cos\theta_i$. In this reduction:

- the stiffness conditioning $F_\kappa$ is realized by the bounded forward regulator $J_i=\tau_i/(\tau_i+\kappa_{\mathrm{junc}})$,
- $\phi$ enters as the real prefactor $\sin\phi$ in the deformation $\delta_i$,
- there is no explicit complex split-path recombination term $D_{\mathrm{split}}$ in the current EM baseline (this is part of the *spec layer* to unify how plane patterns are visualized across sectors).

Figures below visualize the plane-cell addressing and the canonical $|U_{\mathrm{eff}}(u,v)|$ pattern representation used in this draft.

![EM/QED plane: base cell addressing and micro 16-port patch](figs/Fig-EMQED-v5-A_base_cell.png)

![Canonical plane pattern representation: heatmap = $|U_{\mathrm{eff}}(u,v)|$ with sparse bulk phasor glyphs](figs/Fig-EMQED-v4-B_pattern_Ueff.png)

![Ports → micro 4×4 → macro cell mapping (example)](figs/Fig-EMQED-v5-C_mapping_example.png)

### 4.2 Effective amplitude convention (why $A_{\mathrm{EM}}$ may look “huge”)

Because $f_i\propto\alpha_{\mathrm{map}}\ln(\cdot)$ with $\alpha\ll 1$, the numerically meaningful strength is an effective scale
$$
A_{\mathrm{eff}}\sim A_{\mathrm{EM}}\alpha_{\mathrm{map}}\,g_{\mathrm{gen}}\sin\phi
$$
rather than the raw $A_{\mathrm{EM}}$ itself.

For the preregistered point used below,
$A_{\mathrm{EM}}=10^5,\ \alpha_{\mathrm{map}}=7.5\times10^{-5},\ g_{\mathrm{gen}}=1,\ \phi=\pi/2\Rightarrow A_{\mathrm{eff}}\approx 7.5$
(order-unity).

A directly reportable alternative is the realized deformation size:
$$
A_{\mathrm{eff}}^{(\delta)}\equiv \mathrm{RMS}_i[\delta_i],\qquad \delta_{\max}\equiv\max_i|\delta_i|.
$$
For the full-sample `total` run at $A=10^5$ in `shape_only` mode we obtain
$A_{\mathrm{eff}}^{(\delta)}\approx 6.78\times10^{-3}$ and $\delta_{\max}\approx 1.45\times 10^{-2}$
(from the saved output CSV).

### 4.3 Preregistered test configuration (“EM seal” candidate)

Locked configuration (no scan):

- `geo_structure=offdiag` $\Rightarrow s_{\mathrm{struct}}=-1$
- `geo_gen=lam2` $\Rightarrow g_{\mathrm{gen}}=1$
- $\phi=\pi/2\Rightarrow \sin\phi=1$
- $\alpha_{\mathrm{map}}=7.5\times10^{-5}$
- $\zeta=0.05,\ R_{\max}=10,\ t_{\mathrm{ref}}=0.02$
- `--shape_only --freeze_betas --beta_nonneg`

Hypotheses:

- NULL: $A_{\mathrm{EM}}=0$
- GEO: $A_{\mathrm{EM}}=+10^5$
- Sign-falsifier: $A_{\mathrm{EM}}=-10^5$ (same magnitude, sign flip)

### 4.4 Full-sample results with full covariance (`total`)

Using the supplied full covariance matrix $C_{\mathrm{total}}$:

- $A=0$: by construction $\sigma^{\mathrm{GEO}}=\sigma^{\mathrm{SM}}$ and $\Delta\chi^2=0$.
- $A=+10^5$: $\chi^2_{\mathrm{SM}}=147.901628,\ \chi^2_{\mathrm{GEO}}=133.941717\Rightarrow \Delta\chi^2=13.959911$.
- $A=-10^5$ (sign flip): $\chi^2_{\mathrm{GEO}}=164.765429\Rightarrow \Delta\chi^2=-16.863801$ (worse than SM).

Interpretation (strictly within this preregistered bridge):
the dataset not only tolerates the deformation, but also prefers the **sign** of the deformation (sign-flip falsifier is disfavored).

### 4.5 Predictive holdouts with pivot-centering (diag_total shown)

To test whether geometry is merely reabsorbing normalization freedom, we perform band holdouts where:

- The group normalizations $\beta_g$ are fitted on TRAIN only;
- The fitted $\beta_g$ are applied unchanged to TEST;
- Geometry is evaluated with **pivot-centering** (`center_cos=0.72`) to remove DC components without per-group mean subtraction.

Two preregistered bands (within each group):

- Forward band: $\cos\theta\in[0.72,0.91)$ (test=8 bins)
- Mid band: $\cos\theta\in[0.45,0.72)$ (test=12 bins)

Using `--cov diag_total` (explicit diagonalized check), we obtain:

**Forward-band holdout $[0.72,0.91)$:**

- $A=+10^5$: TRAIN $\Delta\chi^2=1.344949$, TEST $\Delta\chi^2=15.574840$.
- $A=-10^5$: TRAIN $\Delta\chi^2=-1.982704$, TEST $\Delta\chi^2=-16.221858$.

**Mid-band holdout $[0.45,0.72)$:**

- $A=+10^5$: TRAIN $\Delta\chi^2=11.774899$, TEST $\Delta\chi^2=1.658903$.
- $A=-10^5$: TRAIN $\Delta\chi^2=-13.200970$, TEST $\Delta\chi^2=-1.757912$.

Jury-language reading:

- **Historical branch-level positive sign:** GEO improves residuals in both bands for $A=+10^5$.
- **Sign-falsification check cleared:** sign-flip is consistently worse on TEST.
- **Caveat**: full-covariance pivot-centered holdouts are the next required robustness step (planned below).

### 4.6 Parameter definitions and CLI mapping (EM)

| Symbol / name | Meaning (code-faithful) | Units / convention | CLI |
|---|---|---:|---|
| $A_{\mathrm{EM}}$ | Raw EM deformation amplitude. Interpretable only together with $\alpha_{\mathrm{map}},\phi,g_{\mathrm{gen}}$. | dimensionless | `--A` |
| $\alpha_{\mathrm{map}}$ | Log-response scale in $f=\alpha_{\mathrm{map}}\ln(\cdot)$. (Not the QED fine-structure constant.) | dimensionless | `--alpha` |
| $\phi$ | Phase knob; deformation scales as $\sin\phi$. | rad | `--phi` |
| $t_{\mathrm{ref}}$ | Momentum-transfer reference in the log driver. | GeV | `--t_ref_GeV` |
| $\zeta$ | Saturation rate in $R=R_{\max}(1-e^{-\zeta |f|})$. | dimensionless | `--zeta` |
| $R_{\max}$ | Maximum response amplitude in $R$. | dimensionless | `--R_max` |
| $\kappa_{\mathrm{junc}}$ | Junction stiffness in the junction filter $J(\tau;\kappa_{\mathrm{junc}})$ (forward-regime regulator). | dimensionless | `--kappa_junc` |
| $s_{\mathrm{struct}}$ | Structure sign (+1 diag, −1 offdiag). | — | `--geo_structure` |
| $g_{\mathrm{gen}}$ | Generator scalar (lam1..lam4 → 0.5..2.0). | — | `--geo_gen` |
| $\beta_g$ | Group normalization nuisance multipliers (4 blocks here). | — | `--freeze_betas`, `--beta_nonneg` |
| `shape_only` | Removes per-group mean of $\delta$ (anti-normalization). | — | `--shape_only` |
| `center_mode` | Pivot-centering mode (preferred in holdouts). | — | `--center_mode pivot_cos` |
| $\cos\theta_p$ | Pivot location used for centering. | — | `--center_cos 0.72` |
| Covariance | Either `total` or `diag_total`. | — | `--cov total/diag_total` |

Note: in some legacy runners the same parameter may be exposed as `--kappa`; here we denote it explicitly as $\kappa_{\mathrm{junc}}$ to avoid confusion with matrix conditioning.

### 4.7 Limitations and numerical conditioning notes (EM)

This EM track is deliberately framed as a **clean consistency + sign-falsifier** test. The current “tension/conditioning” label refers to *technical sensitivity*, not a claimed physical anomaly:

- **Covariance structure matters.** The supplied matrices include a correlated systematic component ($C_{{\mathrm{sys},corr}}$) that is numerically near-singular (smallest eigenvalues $\sim 10^{-14}$ in our check), which can trigger unstable inversions in some numeric setups. The full covariance $C_{\mathrm{total}}$ used in Sec. 4.4 is positive definite with a moderate condition number $\kappa_C\equiv\mathrm{cond}(C)\approx 6.5\times 10^3$ (min eigenvalue $\approx 4.0\times10^{-2}$, max $\approx 2.6\times10^{2}$). 
 For robustness we therefore report both `total` and `diag_total` variants and require consistency of **sign** and broad behavior.

- **Holdouts are the real judge.** Full-sample $\Delta\chi^2>0$ can still be a shape-flex artifact. This is why Sec. 4.5 uses **predictive band holdouts** with frozen group normalizations and **pivot-centering** to remove DC-like components. In the current state, the geometry deformation remains favored in the full sample and in several holdouts, but the strongest full-cov holdout set remains an *open prereg robustness step* (Sec. 4.8).

- **Interpretation discipline.** Until the full-cov holdouts are completed and shown stable, the EM result should be read as: 
 **historical branch-level positive sign + TENSION (numerical / covariance sensitivity under investigation).**

### 4.8 Planned EM upgrades (scan-free)

The goal is to strengthen the **unified** claim without “fixing until it works”.
Concrete next preregistered steps:

1) **Pivot-centered full-cov holdouts:** repeat the forward/mid band tests under `--cov total` (same locked knobs).
2) **Cross-channel EM validation with an amplitude convention:** freeze an **effective amplitude** (e.g. $A_{\mathrm{eff}}^{(\delta)}=\mathrm{RMS}[\delta]$) and apply it to an independent EM observable (e.g. $\mu^+\mu^-$ angular spectrum or $A_{\mathrm{FB}}$ at LEP2) with no tuning.
3) **Baseline upgrade:** replace BHAGEN-derived curve with an official collaboration SM prediction pipeline (radiative/acceptance-matched) if available.
4) **Systematics upgrade:** replace the 2-source correlated model with published nuisance breakdown if available.

Until (1)-(2) are completed, the EM sector is best labeled as **not established (historical hint only; dataset-conditional)** rather than a discovery claim.

## 4.9 Mass Spectrometer sector (real Bruker mzML; fit-free, prereg-locked target-specific test)

**What is being tested here (real data).** This sector evaluates whether a **target-wise, mass-conditioned signature** exists in real instrument outputs and remains **stable under holdout**—using **fit-free** observables:

- $p_{\mathrm{success}}(g)$: near-target success probability as a function of ion-load proxy $g$,
- $\mathrm{MAD}_{\mathrm{success}}(g)$: robust width among successes.

A preregistered lock is applied (not tuned per-target), and a **final performance pass / not established verdict** is produced under fixed criteria (C1–C3). This section supersedes earlier toy-only demonstrations and is the canonical Mass Spectrometer write-up in this document.

### 4.9.1 Real-data validation (Bruker mzML) — setting separation and target-specific multi-target test (fit-free)

**Why this section exists.** We validate the target-specific signature directly on Bruker-origin mzML exports (CompassXport metadata visible in mzML), using a fit-free, prereg-locked protocol.

#### Data (real runs; full-scan)

We use full-scan Bruker-origin runs exported to mzML and treat each run as a “setting”. In the current prereg we use the Cyto FD 500ng set:

- Mode A (discovery): `190226_Cyto_1_FD_500ng.mzML`
- Mode B (discovery): `190226_Cyto_2_FD_500ng.mzML`
- Mode B (holdout): `190226_Cyto_3_FD_500ng.mzML`
- Independent cross-check arm: A2 vs B3 (same protocol, separate files)

Each mzML contains $\~528$–$\~529$ MS1 scans (full spectra).

#### Derived per-scan table (mzML → CSV; no fitting)

From each mzML we generate a per-scan table with at minimum:

- `scan_index` (integer scan counter)
- `tic` (total ion current proxy per scan)
- `mz1` (the scan-level mass estimate used for the prereg plots; produced by the project’s pipeline)

We then define an ion-load proxy $g\in[0,1]$ from fixed quantile anchors (locked):

$$
g=\mathrm{clip}\left(\frac{\mathrm{TIC}-Q_{10}}{Q_{90}-Q_{10}},\;0,\;1\right),
$$
where $Q_{10},Q_{90}$ are the 10th and 90th percentiles of TIC **within a run**.

A run-level reference mass is set to the Mode-A median:

$$
m_\mathrm{ref}\equiv \mathrm{median}_{\mathrm{Mode\ A}}(mz1),\qquad
\Delta_{\mathrm{ppm}} \equiv 10^6\,\frac{mz1-m_\mathrm{ref}}{m_\mathrm{ref}}.
$$

#### Observable choice (the key fix)

Earlier “echo/tail” style observables can easily miss the effect if the dominant instrument difference is instead **setting-conditioned separation**, **main-peak width change**, or **drift**. The prereg here therefore targets:

1) **Setting-conditioned separation:** do Mode A and Mode B produce systematically different $\Delta_{\mathrm{ppm}}(g)$ profiles?

2) **Particle-specific signature (multi-target):** does the Mode A↔B separation *change across target m/z windows* in a stable way?

The second question is the “target-specific” question in operational form: a global offset would look similar at every m/z; a target-specific (mass-conditioned) effect produces a target-dependent signature.

---

## Target-specific multi-target test (preregistered lock)

We define a set of $K$ target m/z values (auto-selected, locked by `topK`) and analyze each target independently within a fixed window:

- `window_ppm = 30` (target window half-width)
- `good_ppm = 3` (**locked prereg threshold**; see below)
- `min_n = 8` per $g$-bin and per setting
- `max_bins = 8` (balanced-by-availability)

For each target $t$ and $g$-bin $b$, we compute:

- $p_{\mathrm{success}}(t,b)$: fraction of scans whose per-scan estimate falls within the “good” band around the target,
- $\mathrm{MAD}_{\mathrm{success}}(t,b)$: robust width (median absolute deviation) of the successful scans.

We then form per-target **setting deltas** as a function of $g$-bin:
$$
\Delta p_{\mathrm{success}}(t,b) \equiv p_{\mathrm{success}}^{(B)}(t,b)-p_{\mathrm{success}}^{(A)}(t,b),
$$
and summarize each target by a bin-mean absolute delta:
$$
\overline{\lvert\Delta p\rvert}(t) \equiv \langle\lvert\Delta p_{\mathrm{success}}(t,b)\rvert\rangle_{b}.
$$

A target-specific signature exists if $\overline{\lvert\Delta p\rvert}(t)$ is **nonzero** for many targets and **stable** across an independent holdout.

### Locked prereg gate (good_ppm = 3)

This is the key lock that prevents “moving the goalposts” by loosening success thresholds until everything saturates.

Empirically, for this dataset family:

- When `good_ppm` is too large (tens → thousands of ppm), $p_{\mathrm{success}}$ saturates toward 1 for most targets → **no discrimination**.
- A tight lock (`good_ppm=3`) avoids saturation and yields stable target-wise structure.

### Results (locked, fit-free; real mzML)

**Paper-ready results paragraph.** Using CompassXport-exported Bruker full‑scan mzML runs (A1–B2 discovery; A1–B3 holdout; A2–B3 third‑arm), we applied a strictly **no‑fit** preregistered multi‑target signature test. For each target m/z, scans are binned by the normalized ion‑load proxy $g$ (quantile anchors from TIC), and we compute $p_{\mathrm{success}}(g)$—the fraction of scans meeting the locked “good” gate `good_ppm=3` within `window_ppm=30`—along with a width proxy (MAD among successes). With `topK=12` auto‑targets, the target‑wise signature is stable across holdout and third‑arm checks: median $|\Delta p_{\mathrm{success}}|$=0.116 (A1–B2) and 0.119 (A1–B3), holdout rank correlation 0.965; MAD rank correlation 0.836 with the same top‑MAD target (T01); and third‑arm rank correlations 0.853/0.853 with the same top target (T03). Under preregistered criteria C1–C3 this yields a final verdict **performance pass**, with signed artifacts written to `out/particle_specific_final_goodppm3_lock/`.

Using `topK=12` targets and the lock above, the run outputs (written under `out/particle_specific_final_goodppm3_lock/`) report:

- **Median absolute target delta** (A1–B2): $\mathrm{median}_t\,\overline{\lvert\Delta p\rvert}=0.116172$
- **Holdout stability** (A1–B3): $\mathrm{median}_t\,\overline{\lvert\Delta p\rvert}=0.119307$
- **Holdout rank correlation** of $\overline{\lvert\Delta p\rvert}(t)$: $\rho_{\mathrm{rank}}=0.965035$
- **Nonzero targets:** 12/12 in both discovery and holdout
- **Width (MAD) stability:** rank correlation $0.836364$ and the top-MAD target matches (T01 vs T01)
- **Third-arm consistency** (A2–B3): rank correlations $0.853147/0.853147$; top target matches across all three arms (T03)

**Preregistered final verdict (good_ppm=3): performance pass.**

#### What this does and does not mean

- **Does mean (strong):** within this pipeline, the setting effect is not purely global. It has a **stable target-dependent signature** across multiple runs and a holdout. That is an *operational* “mass/target-specific” effect.

- **Does not mean (yet):** we have identified chemical species, charge states, or vibrational transitions. This test only says the model’s gate (or correction) behaves as if it is **m/z-conditioned** in the instrument readout. Connecting that to underlying molecular physics requires:
  - annotating targets with actual m/z and tentative assignments (isotope envelopes / charge states),
  - repeating across chemically distinct mixtures,
  - verifying that the signature follows the expected mass ordering under known calibrants.

This addendum is therefore positioned as: **performance pass for target-specific behavior in real mzML**, with clear next falsifiers.

### 4.9.11 Preregistered follow-up plan — bridging to species/charge (no-fit)

The real-mzML performance-pass result above is an **operational target-specific signature** in the instrument readout: different target $m/z$ windows exhibit different, stable $p_{\mathrm{success}}(g)$ and $\mathrm{MAD}_{\mathrm{success}}(g)$ patterns across setting comparisons and holdouts.

What it is **not yet** (and what this plan targets) is a **species-resolved physical explanation** (charge state, isotope envelope, adduct class, or vibrational/energy-transition mapping). The next step is to preregister a minimal, decisive bridge that either (a) strengthens the “species/charge-linked” interpretation or (b) falsifies it by exposing a purely global/pipeline artifact.

#### Frozen lock (do not change)
These parameters are now part of the prereg lock:

- `good_ppm = 3`
- `window_ppm = 30`
- `tail3_ppm = -300000` (diagnostic only; does not decide performance pass / not established)
- `min_n = 8`
- `max_bins = 8`
- Target set: `out/particle_specific_cytofull_A1_B2_direct/targets_used.csv` (12 targets)

#### New unseen data (future holdouts)
Choose **two additional full-scan CompassXport mzML files** not used in A1/B2/B3/A2/B3 (e.g., Cyto_4 and Cyto_5 if available). Define:

- Discovery pair: A\* vs B\* (two different “settings” runs)
- Holdout pair: A\* vs B\*hold
- Third-arm pair: A\*alt vs B\*hold

No tuning based on these new files is allowed.

#### Primary endpoints (fit-free)
For each target $t$, compute:

- $\Delta p_{\mathrm{success}}(t) = \mathrm{median}_b\left[p_{\mathrm{success}}^{(B)}(t,b) - p_{\mathrm{success}}^{(A)}(t,b)\right]$
- A width/robustness metric from successful scans, $\mathrm{MAD}_{\mathrm{success}}(t,b)$, and its target-wise stability across runs via the log-ratio summary used in §4.9.10.

#### Decision rule (performance pass / not established; preregistered)
Using the same gate as the locked final artefact:

**C1 (p_success signature + holdout stability)**

- $\mathrm{median}_t\,\overline{|\Delta p_{\mathrm{success}}|} \ge 0.10$ in both discovery and holdout,
- holdout target-rank correlation $\rho_{\mathrm{rank}}\ge 0.90$,
- at least 10/12 targets have nonzero signal in both runs.

**C2 (MAD signature stability)**

- MAD rank correlation $\ge 0.80$,
- same top-MAD target in discovery and holdout.

**C3 (third-arm consistency)**

- rank correlations $\ge 0.80$ between discovery↔third-arm and holdout↔third-arm,
- the top-$|\Delta p_{\mathrm{success}}|$ target matches across all three arms.

Final verdict: **performance pass** iff C1 & C2 & C3 are all true; otherwise **not established**.

#### Reproducible commands (real mzML -> target-specific verdict)

The older mzML-specific command block has been removed from the main paper to avoid carrying obsolete or duplicate CLI steps.

Use **Section 8** for the current canonical performance commands:
- `internal_only` strict branch
- `full` ablation branch
- shared locked finalizer / aggregator steps

### 4.9.12 Internal occupancy-gate and two-center boundary addendum (derived from the same locked real-mzML export; diagnostic-only)

This addendum extends the canonical real-mzML target-specific performance pass with a locked internal branch test performed on the derived real-data points exports (from the same locked real-mzML export stream) and the frozen target registry. It is included here because it now survives the current internal falsification ladder, but it remains a diagnostic-only Mass Spectrometer extension. It is not a new sector, and it does not replace the primary real-mzML result above.

#### (A) Minimal adapter hook into the unified equation (explicit attachment)

These Mass Spectrometer addenda are carried as **sector adapters** under the already-declared unified equation, not as stand-alone side stories. The attachment point is the same cross-sector skeleton used elsewhere in this paper:

$$
\frac{d\rho}{dL}
=
-i\!\left[H_{\mathrm{vac}} + H_{\mathrm{MS}}^{(0)} + \delta H_{\mathrm{MS}}^{(2c)} + \sum_{s\neq \mathrm{MS}} H_s,\rho\right]
+
\mathcal D_{\mathrm{MS}}^{(0)}\!\left[\rho;\gamma_{\mathrm{MS}}^{\mathrm{eff}}\right]
+
\delta \mathcal D_{\mathrm{MS}}^{(2c)}\!\left[\rho;\gamma_A^{\mathrm{eff}},\gamma_B^{\mathrm{eff}}\right]
+
\sum_{s\neq \mathrm{MS}} \mathcal D_s[\rho].
$$

The safe reading is purely adapter-level:

- $H_{\mathrm{MS}}^{(0)}$ and $\mathcal D_{\mathrm{MS}}^{(0)}$ are the already-declared Mass Spectrometer baseline sector terms;
- the single-center branch supplies a **small locked modulation** of the baseline MS damping/success channel;
- the two-center branch supplies a **diagnostic bridge adapter** that shows how the branch attaches mathematically to the unified equation, while remaining explicitly prepaper and non-validated as a literal physical Hamiltonian term.

#### (B) Single-center occupancy-gate adapter

The normalized occupancy proxy is carried as

$$
x_{\mathrm{occ}}
=
\frac{I_{\mathrm{core}}}{I_{\mathrm{core}} + I_{\mathrm{shoulder}} + I_{\mathrm{outer}}},
\qquad 0 \le x_{\mathrm{occ}} \le 1.
$$

The locked single-center adapter is the multiplicative map

$$
\gamma_{\mathrm{MS}}^{\mathrm{eff}}
=
\gamma_{\mathrm{MS}}^{(0)}\left(1-\rho_{\mathrm{occ}} x_{\mathrm{occ}}\right),
\qquad \rho_{\mathrm{occ}} = 0.10,
$$

with the directly implemented observable-level equivalent

$$
p_{\mathrm{success,occ}}
=
p_{\mathrm{success,legacy}}\left(1-\rho_{\mathrm{occ}} x_{\mathrm{occ}}\right).
$$

So the single-center branch is not an unbounded new sector term; it is a constrained MS-sector adapter that rescales the already-frozen success / damping channel inside the unified-equation bookkeeping.

The value $\rho_{\mathrm{occ}}=0.10$ is not a fit parameter here. It is the pre-committed minimal carry-forward value selected by the locked single-center hard-regression screen after larger trial values failed to remain uniformly safe under the current three-arm coverage.

**Locked full-run result (current 3-arm real-data family):**

- data family: current locked 3-arm MS family (`ModeA_points`, `ModeB_points`, `ModeB_holdout_points`)
- targets: 12
- settings: 3
- baseline `p_success = 1.0` in the current locked runner rows
- `p_success_occ` / `gate_occ_factor_mean` range: `0.9310250312` to `0.9677384486`
- mean `p_success_occ` / `gate_occ_factor_mean`: `0.9459447610`
- mean cross-compare `mean_abs_delta_p_success_occ`: `0.0030917513`
- worst `max_abs_delta_p_success_occ`: `0.0191164089` (worst target: `T02` vs `ModeB_holdout_points`)

**Interpretation (strict):**

- Under the current locked MS family, the minimal occupancy-gate insertion with `rho = 0.10` survives the full 3-arm occgate runner.
- This makes `rho = 0.10` the current default carry-forward candidate for the single-center branch.
- This is not a general physical proof and is not a claim of validity beyond the current MS family.

#### (C) Two-center diagnostic-boundary adapter

At the conceptual level, the constrained two-center law is carried in the entanglement-first form

$$
\frac{d\Psi_{AB}}{dt}
=
(\alpha-\gamma)\Psi_{AB}
-\beta |\Psi_{AB}|^2\Psi_{AB}
+\eta L_{\mathrm{overlap}},
$$

where $\Psi_{AB}$ is the bounded bridge amplitude, $L_{\mathrm{overlap}}$ is the deterministic overlap drive, and the nonlinear term enforces boundedness.

Here $t$ is only an internal interaction parameter for the local two-center working law. The attachment back to the unified equation is still carried at the path-length level $L$ through the MS-sector adapter, so this does not introduce a competing evolution variable in the main framework.

The minimal unified-equation adapter for this branch is then written as a **bookkeeping bridge**, not as a validated literal Hamiltonian claim:

$$
B_{AB} = |\Psi_{AB}|^2,
\qquad
\gamma_A^{\mathrm{eff}} = \gamma_A^{(0)}\left(1-\xi B_{AB}\right),
\qquad
\gamma_B^{\mathrm{eff}} = \gamma_B^{(0)}\left(1-\xi B_{AB}\right),
$$

and, at the same adapter level,

$$
\delta H_{\mathrm{MS}}^{(2c)}
=
\kappa_B B_{AB}\left(|A\rangle\langle B| + |B\rangle\langle A|\right).
$$

The safe meaning of this insertion is narrow:

- $B_{AB}$ is the bounded bridge-strength shadow of the two-center branch;
- $\gamma_{A,B}^{\mathrm{eff}}$ encodes the adapter-level statement that a nonzero bridge can reduce effective loss relative to isolation;
- $\delta H_{\mathrm{MS}}^{(2c)}$ is the minimal explicit coherent adapter showing where the two-center bridge would sit inside the unified equation if carried forward;
- the paper does **not** claim that this term is already a physically validated microscopic Hamiltonian.

The implemented pair layer remains deliberately modest:

- deterministic pair construction from the frozen target ordering
- adjacent baseline preserved at all times
- refinement allowed only if it increases resolution without changing the story

**Current frozen pair-layer results:**

- adjacent baseline: `11` pairs = `8 stable / 3 repulsive / 0 inconclusive`
- adjacent + next-nearest refined layer: `21` pairs = adjacent subset preserved, added shell `5 stable / 5 repulsive / 0 inconclusive`
- shell monotonicity stability sweep: `27 / 27` scenarios passed under mild deterministic parameter variation

#### (D) Raw-data rebuild and arm-by-arm stability

The two-center diagnostic layer was then rebuilt from the raw points files under frozen ex-ante thresholds and compared against an archived frozen Track-8 comparator.

Frozen thresholds:

- `width_scale = 1.0`
- `corridor_min = 0.25`
- `reject_max = 0.75`
- `leak_ratio_max = 0.90`
- `sep_s0 = 0.11`
- `confidence_quantile = 0.25`

Under four separate rebuild runs (`A1_B2 ModeA`, `A1_B2 ModeB`, `A1_B2_direct ModeB_holdout`, and the combined pool), all four runs yielded:

- `classification_changes = 0`
- `confidence_changes = 1`
- `shell_monotonicity = OK`
- verdict: `OK-DIAGNOSTIC-REBUILD`

The explicit rollup answer was that the observed two-center skeleton is not only a pooled-data effect; the same classification skeleton survives in each arm individually.

#### (E) Weak-stable boundary hard falsifier (single global frozen edge)

The weak-stable boundary question was then reduced to the two weakest stable-boundary pairs:

- `T05 <-> T12`
- `T08 <-> T09`

A soft version (with run-specific edge recalculation) was treated only as preliminary support. The stricter version used **one single frozen weak-stable edge** for all runs:

- `global_frozen_weak_stable_edge = 0.33904771546`
- `global_edge_band_median_abs_distance = 0.022510457733`

Under all `4 runs x 2 pairs = 8` checks:

- `near_global_edge = True`
- base label stayed `STABLE-INTERMEDIATE-CANDIDATE`
- confidence stayed `WEAK_STABLE`
- `conf_changed_vs_track8 = False`

The signed distances to the same frozen edge remained small and negative (approximately `-0.000879170387197` to `-0.00163583576279`). These distances are small relative to the frozen edge-band median absolute distance (`0.022510457733`), so they remain consistent with weak-stable boundary proximity and are not a boundary-violation signal.

**Interpretation (strict):**

- these two pairs still behave as genuine weak-stable boundary pairs under one single frozen edge
- the boundary-proximity explanation survives the hard version of the falsifier
- this remains an internal diagnostic-support result, not a chemistry claim, not a molecular-bond proof, and not a direct entanglement measurement

#### (F) Current claim boundary and carry-forward use

These Mass Spectrometer addenda are now safe to carry as **scoped working submodules** of the unified-equation program:

- the single-center branch provides a locked damping / success-channel adapter at `rho = 0.10`
- the two-center branch provides a diagnostic bridge adapter plus a raw-data-stable pair-layer boundary story

What is safe to say:

- under the current locked MS real-data scope, both adapters survive the present internal falsification ladder and can be carried forward as constrained working components

What is not safe to say:

- the full model is physically proven
- chemistry has been explained
- molecular bond has been validated
- direct entanglement has been measured from these MS data

For stronger claims, the next requirement is not more repetition on the same pack, but new independent real data or a more direct observable.

### 4.9.13 Current freeze status, carry-forward rule, and claim ladder (post-addendum operational note)

This operational note records the immediate branch status after the internal occupancy-gate and two-center boundary addendum. It does not replace the substantive results above; it freezes how those results are to be carried forward inside the unified-equation program at the present scope.

**Frozen operational status (current scope):**

- the **single-center branch** is frozen at the current locked 3-arm Mass Spectrometer family, with the minimal occupancy-gate adapter carried forward at `rho = 0.10`;
- the **two-center weak-stable boundary sub-branch** is frozen after the Track 1-8 diagnostic ladder, the four-run raw-data rebuild, and the single global frozen-edge hard falsifier;
- the explicit unified-equation attachment remains the adapter-level structure already stated in §4.9.12(A)-(C).

To avoid ambiguity, the concrete frozen adapter statements retained in the unified-equation program are:

a. single-center adapter carried forward under the unified equation:

$$
\gamma_{\mathrm{MS}}^{\mathrm{eff}}
=
\gamma_{\mathrm{MS}}^{(0)}\left(1-\rho_{\mathrm{occ}} x_{\mathrm{occ}}\right),
\qquad
\rho_{\mathrm{occ}} = 0.10.
$$

b. two-center bounded bridge carried at the same adapter level:

$$
\delta H_{\mathrm{MS}}^{(2c)}
=
\kappa_B B_{AB}\left(|A\rangle\langle B| + |B\rangle\langle A|\right),
\qquad
\delta \mathcal D_{\mathrm{MS}}^{(2c)}\!\left[\rho;\gamma_A^{\mathrm{eff}},\gamma_B^{\mathrm{eff}}\right].
$$

These are therefore retained as **working adapter insertions** in the present paper state, not as independent proof-level terms.

**Carry-forward rule (current paper state):**

- these terms are now allowed as **scoped working adapters** inside the unified equation;
- they are **not** to be promoted in this document to stand-alone proof claims, new validated sectors, or literal microscopic Hamiltonian confirmation;
- the correct reading is: the present real-data Mass Spectrometer branch survives the current internal falsification ladder strongly enough to remain attached to the unified-equation framework in prepaper form.

**Claim ladder (strict):**

1. **Safe now (current-scope claim):** under the current locked Mass Spectrometer data family, the single-center and two-center adapters survive the present internal real-data checks and can remain in the master-equation program as constrained working components.
2. **Not safe yet (broader physical claim):** a broader physical claim would require a truly independent real-data family, not merely more reruns on the same current pack.
3. **Not safe yet (cross-domain claim):** a cross-domain claim would require new real data from another observable family or sector.
4. **Not safe yet (direct-observable claim):** any direct-observable claim would require a dataset that measures the target observable more directly, rather than an additional proxy-only repetition.

**Operational next-step rule:**

- do **not** keep rerunning the same current 3-arm Mass Spectrometer pack;
- do **not** overstate the present result as “physically proven”;
- if future work is opened again from this point, it should either use a genuinely new independent real-data family or a more direct observable.


### 4.9.14 Current Mass Spectrometer performance commands

The obsolete pre-freeze CLI history has been removed from the main paper to avoid carrying outdated run commands.

The **current** canonical Mass Spectrometer performance commands are maintained in **Section 8**:
- `internal_only` strict branch
- `full` ablation branch
- shared locked finalizer / aggregator steps

This keeps the paper aligned with the updated repo-root runbook and avoids duplicate command blocks with conflicting paths.

### 4.10.1. Role of this sector in the unified-equation program

In the broader framework, this sector tests whether the model family can at least remain compatible with a standard, externally validated nonlocality benchmark after our event-building and counting pipeline is fixed. Concretely, this sector is a **pipeline-integrity + compatibility test**:

- **Pass condition:** the locked event-building + CHSH audit reproduces a statistically positive Bell violation on the accepted NIST run4 coincidence export.
- **Fail condition:** the same locked pipeline collapses to a non-violating or sign/pathology result on the canonical export.

This is not yet a full geometric derivation of Bell correlations from the lattice/bubble dynamics. It is the correct preregistered first step: **prove the pipeline does not destroy the signal** before attempting any deeper mechanism claims.

### 4.10.2. Data object and format discipline (important)

The valid entanglement audit here is tied to the **HDF5-derived NIST run4 coincidence export** (the CSV produced from the known-good HDF5 route). We explicitly do **not** use the incompatible prescreen coincidence CSV batch for the Bridge-E0 claim.

Why this matters:

- The prescreen CSV (`02_54_coinc_slotfix.csv`) can produce a diagnostic outcome like $S=-2.0$, which indicates a **format/mapping mismatch** (especially setting-dependent slot→outcome interpretation), not a physics failure.
- The HDF5-derived coincidence CSV preserves the intended field semantics for the Bridge-E0 CHSH audit.

So the entanglement claim in this paper is attached to the **correct export path** only.

### 4.10.3. CHSH observable and counting definitions

Let the four analyzer-setting pairs be indexed as
$$
ab \in \{00,01,10,11\}.
$$

For each setting pair, let the coincidence outcomes be binary and encoded into the usual correlator form. Denote the setting-conditioned coincidence counts
$$
N_{ab}^{++},\; N_{ab}^{+-},\; N_{ab}^{-+},\; N_{ab}^{--},
$$
and total
$$
N_{ab}=N_{ab}^{++}+N_{ab}^{--}+N_{ab}^{+-}+N_{ab}^{-+}.
$$

The setting-wise correlator is
$$
E_{ab} = \frac{N_{ab}^{++}+N_{ab}^{--}-N_{ab}^{+-}-N_{ab}^{-+}}{N_{ab}}.
$$

The CHSH combination (signed convention may differ by encoding order) is
$$
S = E_{00}+E_{01}+E_{10}-E_{11},
$$
and the reported physics quantity is $|S|$.

Classically (local-hidden-variable bound),
$$
|S| \le 2.
$$

The question is whether the locked pipeline returns $|S|>2$ with positive significance on the accepted NIST run4 coincidence export.

### 4.10.4. Preregistered no-fit significance test

We use a preregistered, no-fit significance audit:

1. Build coincidences with locked Bridge-E0 rules from the HDF5 source.
2. Compute the observed $S_{\mathrm{obs}}$.
3. Generate null surrogates under a label-preserving / setting-consistent randomization rule (locked in script).
4. Form the null distribution of $S$.
5. Report:
   - one-sided null p-value (for Bell-violation direction),
   - z-score derived from the null ensemble,
   - stability diagnostics across seeds/trials.

No regression fitting is used. No “optimize-until-pass” step is allowed.

### 4.10.5. NIST run4 result (Bridge-E0 prereg audit)

Using the accepted HDF5-derived coincidence CSV route, the locked prereg audit returns:

- $S_{\mathrm{obs}} = 2.455001027$
- null mean $\mu_0 \approx 1.999999713$
- null std $\sigma_0 \approx 0.228559614$
- one-sided $p \approx 0.023236$
- $z \approx 1.991$

Interpretation:

- The pipeline preserves a **positive Bell violation** relative to the local bound.
- The null benchmark places the result at roughly **2-sigma** (preregistered, no-fit).
- This is an **audit-positive result** for the entanglement-sector pipeline in the falsification-first sense; it is **not part of the current performance scoreboard**.

### 4.10.6. What this pass does and does not claim

**What it does claim**

- The locked Bridge-E0 counting/audit pipeline is compatible with a genuine Bell-violation dataset.
- The data-processing chain used in this sector does not trivially wash out entanglement signatures.
- The broader program can legitimately include an entanglement-facing empirical checkpoint.

**What it does not claim**

- It does **not** yet derive Bell correlations from the geometric lattice dynamics.
- It does **not** prove a unique microscopic entanglement mechanism.
- It does **not** validate any prescreen CSV format that is semantically mismatched to Bridge-E0.

This is exactly the kind of scoped claim we want in a preregistered falsification workflow.

### 4.10.7. Connection to the “memory” idea (careful wording)

Earlier conversations framed entanglement in terms of a possible shared-field or residual-memory picture (e.g., finite-time correlation support after direct coupling). The present section does **not** test that mechanism directly. Instead, it establishes the prerequisite empirical fact:

> our locked event-processing and CHSH audit can pass a real Bell benchmark.

That is the correct foundation before attempting any stronger mechanism-level derivation (shared mediator field, damped common mode, finite-memory kernel, etc.).

### 4.10.8. Immediate next falsifiers for this sector

The strongest next steps are:
1. **Weihs audit repair** (offset/format bugfix) using the same prereg rules.
2. **Cross-dataset invariance:** run the same no-fit CHSH audit on additional Bell datasets with no retuning.
3. **Mapping robustness:** explicitly enumerate and lock setting-dependent slot→outcome mappings where data format requires it, then preregister before rerun.
4. **Mechanism layer (later):** only after repeated empirical passes, attempt a true model-generated correlator $E_{ab}^{\text{model}}$ comparison.

This keeps the project aligned with the user’s stated rule: **falsification first, no p-hacking, no fit-driven storytelling**.

## 4.11. Photon-decay / propagation bridge sector (preregistered cosmic birefringence accumulation tests)
> **Interpretation note:** This section reports **preregistered accumulation-law / consistency / bridge-wiring** checks for the photon propagation/birefringence line. It is a **scaffolding + falsification testbed** in this revision, not a final calibrated cosmic birefringence parameter claim.

This section formalizes the photon-facing part of the program in a way that is testable now. Earlier discussions used “photon decay” language as a conceptual motivation (phase/energy leakage during propagation). The current data-facing implementation is a **propagation bridge observable**:

- a tiny polarization-rotation accumulation law along line of sight,
- tested on real cosmological polarization compilations,
- with **locked, no-fit, preregistered** statistics.

So this is the empirical bridge sector for the photon-decay/progression idea, not yet a direct microscopic decay-rate derivation.

### 4.11.1. Observable definition (rotation accumulation)

We model a polarization-angle rotation contribution
$$
\alpha(z) = \beta\, I(z),
$$
where $\beta$ is a single locked amplitude (not fit in the prereg tests), and
$$
I(z)=\int_0^z \frac{dz'}{(1+z')E(z')}
$$
is the propagation accumulation kernel in flat $\Lambda$CDM with
$$
E(z)=\sqrt{\Omega_m(1+z)^3+\Omega_\Lambda+\Omega_r(1+z)^4}.
$$

In the prereg runs used here, the kernel is locked to
$$
\Omega_m=0.315,\quad \Omega_\Lambda=0.685,\quad \Omega_r=0.
$$

This choice is not fit to the birefringence data. It is fixed in advance as part of the test protocol.

### 4.11.2. Why this is a photon-decay “bridge”

The original physical intuition was that photon propagation may carry a small cumulative phase effect (or phase/energy bookkeeping leakage in the broader geometric picture). A direct decay-law test is not yet available in the current pipeline, so we use a safer, falsifiable projection:

- If a propagation-linked effect exists, a redshift-integrated kernel like $I(z)$ is a natural first observable.
- If the effect is absent, locked no-fit tests should return null-compatible statistics.

Thus, the birefringence accumulation analysis is a **bridge observable**: it probes the propagation-side consequence of the photon-sector idea without overclaiming a full microscopic derivation.

### 4.11.3. Preregistered test A (accumulation correlation; no fit)

For a dataset with measured polarization rotation angles $\alpha_i$ and uncertainties $\sigma_i$ at redshifts $z_i$, define the kernel values $I_i = I(z_i)$.

We run a preregistered, no-fit correlation-style test:

- **Null:** no monotonic accumulation signal relative to the locked kernel $I(z)$.
- **Statistic:** correlation / signed trend statistic locked in the script.
- **Calibration:** permutation or equivalent null generation (locked).
- **Outputs:** p-value(s) for signed and absolute variants.

No regression coefficient is fitted to maximize significance.

### 4.11.4. Preregistered test B (sky-fold anisotropy falsifier)

A second locked test probes whether any apparent signal is actually a sky-geometry artifact. The sample is split by a preregistered sky-fold rule (hemisphere / angular partition fixed in code), and a contrast statistic is evaluated under a null randomization.

This gives a **falsifier** for accidental directional structure:

- If significance appears only in a specific sky split and is unstable, it is likely not a robust propagation law.
- If no significance appears, that is consistent with null and still scientifically useful.

### 4.11.5. Results (locked prereg runs)

The current locked prereg outputs are null-compatible:

**Accumulation test (no-fit)**

- signed p-value $\approx 0.3603$
- absolute-metric p-value $\approx 0.3936$

**Sky-fold anisotropy falsifier**

- p-value $\approx 0.1536$

Interpretation:

- No statistically compelling birefringence accumulation signal is detected in the present locked tests.
- No robust sky-fold anisotropy signal is detected either.
- Therefore, the photon bridge sector is currently a **null result**, but a **successful falsification-style execution** (the pipeline ran correctly and did not manufacture a false positive).

### 4.11.6. Why this still counts as progress

In this program, a null result is informative because the methodology is preregistered and no-fit:

- It constrains the size of any propagation-linked effect in this observable.
- It validates the pipeline and locked-kernel implementation.
- It prevents premature theory inflation from weak or post-selected signals.

This is exactly the behavior we want before adding more complex structure (anisotropic kernels, energy dependence, source-population stratification, etc.).

### 4.11.7. Relationship to future direct photon-decay tests

The long-term photon sector may include more direct observables (energy attenuation, spectral distortions, lifetime-like constraints, or source-class-specific transport effects). When those are implemented, the present birefringence accumulation sector remains valuable as:

1. a locked baseline transport observable,
2. a null benchmark for pipeline sanity,
3. a cross-check against overfitting in future photon-sector extensions.

In other words, this section is the photon-sector **discipline layer**.

### 4.11.8. Immediate next falsifiers for this sector

The strongest preregistered follow-ups are:

1. **Holdout datasets:** quasar polarization compilations or tighter tomography samples (no retuning of kernel form).
2. **Subsample robustness:** rerun by redshift bins and source classes with preregistered splits.
3. **Sign convention audit:** lock angle-wrap and sign conventions across all catalogs before rerun.
4. **Energy/frequency stratification:** only if data quality supports it, add a preregistered frequency-dependent extension.

Again, the rule is unchanged: **no fit-driven claim; nulls are acceptable; robustness beats excitement**.

### 5.1 Weak sector (neutrino oscillations; NOvA pack)

**Goal.** Demonstrate that the unified-equation geometric modulation can be inserted into a realistic oscillation likelihood (matter effects, multiple channels, nuisance handling) and that the pipeline is stable under scan / profiling.

**Canonical forward run (PowerShell):**
*(Forward-run example removed; use the locked weak-sector commands in Section 8.1.)*

**Interpretation (current stage).** In the weak sector, the role of this analysis is primarily *implementation + consistency*: confirm that (i) the “geometry kernel” can be injected without breaking the fit, and (ii) the resulting likelihood surfaces are smooth and scan‑stable. The strongest publishable statement from the weak sector should be deferred until the same robustness protocol used in EM/strong is fully mirrored (jackknife / split tests / alternative covariance choices and pre‑registered scan ranges).

#### 5.1.1 Parameter definitions and CLI mapping (Weak / NOvA)

This section maps each weak-sector (neutrino) parameter in the unified-equation form to the exact CLI flag used in the reproducible runs (Section 8.4).

| Paper symbol / name | Definition + purpose | Units | CLI flag (Section 8.4 example) |
|---|---|---|---|
| A | Strength of the GEO/mech modulation term on top of the standard oscillation probability. | dimensionless | `--A 0.0065` |
| alpha | Scale of the modulation (how quickly the geometric term varies with baseline/energy proxy). | implementation-defined | `--alpha 7.5e-05` |
| omega0 | Base frequency parameter in the mech-kernel parameterization. | implementation-defined | `--omega0 0` |
| zeta | Damping parameter in the mech-kernel parameterization. | dimensionless | `--zeta 0.05` |
| omega0_geom | Convention for converting `L0_km` into the geometric frequency term (e.g., fixed vs inferred). | - | `--omega0_geom fixed` |
| L0_km | Baseline length used by the weak-sector forward model. | km | `--L0_km 810` |
| phi | Quadrature/phase of the GEO kernel (often pi/2 in the current scans). | radians | `--phi 1.57079632679` |
| R_max | Kernel support limit / truncation radius. | implementation-defined | `--R_max 10` |
| rho | Matter density for MSW (electron potential term) in the forward model. | g/cm^3 | `--rho 2.8` |
| Ye | Electron fraction for MSW. | dimensionless | `--Ye 0.5` |
| bin_shift_app, bin_shift_dis | Empirical bin shifts used to align appearance/disappearance channels. | bins | `--bin_shift_app 2 --bin_shift_dis 0` |
| dis_pred | Controls how the disappearance prediction is injected (e.g., template). | - | `--dis_pred template` |

Note: in the reproducibility block the sweep script passes these flags through to the forward model; the names above are the public CLI interface used in the reproducible runs.

### 5.2 Strong sector (updated: CNI + energy‑axis accumulation)

This section replaces the previous (obsolete) ATLAS‑elastic placeholder. The strong‑sector program here is intentionally **minimal and falsification‑first**:

* **Consistency criterion:** in clean phase-sensitive observables (CNI) the geometry phase must **not** degrade the published baseline.
* **DISCOVERY / residual reduction:** in energy‑axis observables (σ_tot(√s), ρ(√s)), geometry must reduce residuals **without scanning**. If it cannot, strong remains “consistent but non‑explanatory”.

We report only **single‑shot, preregistered** runs (no fitting of strong data).

---

#### 5.2.0 Strong-sector knobs (what is fixed vs what is injected)

The strong pipeline is constrained to be **single-shot** and **baseline-respecting**:

- Published baseline parameters used inside the pack (e.g. CNI $\sigma_{\mathrm{tot}},\rho,B$) are **frozen** for the phase-sensitivity test.
- Geometry enters only through a preregistered **phase / absorption injection** controlled by $(A_R,A_I)$, plus a preregistered **energy accumulation** $\mathcal{N}(s)$.

**Primary injected couplings (this draft’s prereg point):**
$$
A_I=-3\times 10^{-3},\qquad A_R=+3\times 10^{-3},
$$
with $\zeta=0.05$ used as the thermodynamic damping scale in the kernel layer.

**Environment scaling (“clock”):** we use a logarithmic proxy
$$
\mathcal{N}(s)=\frac{\ln(s/s_M)}{\ln(s_{\mathrm{ref}}/s_M)},
$$
interpreted as the number of effective plane-slice “queries” at energy $s$ (interaction-frequency picture).

**Legacy note (do not mix parameterizations):**
Earlier exploratory elastic-$pp$ runs used an ATLAS 13 TeV $|t|$ pack and a minimal exponential baseline; the headline prereg settings recorded in the project logs include
$A\simeq 8.5\times 10^{-3},\ \alpha\simeq 7.5\times10^{-5},\ \phi=\pi/2,\ \zeta=0.05$,
with structure choices $\mathtt{geo\_structure=offdiag}$ and $\mathtt{geo\_gen=lam2}$.
Those runs served as **sanity checks** on the modulation machinery; the present draft’s strong claims are anchored instead on **CNI phase sensitivity** and **energy-axis observables** under frozen baselines.

**CLI mapping (representative):**

- absorptive/dispersive injection: $\mathtt{--A\_I}$, $\mathtt{--A\_R}$ (or $\mathtt{--A}$ in legacy parameterization),
- environment mode: $\mathtt{--env\_mode log}$ with $\mathtt{--s\_M}$, $\mathtt{--s\_ref}$,
- kernel-shape controls: $\mathtt{--phi}$, $\mathtt{--zeta}$,
- $t$-mapping: $\mathtt{--t\_ref\_GeV}$, $\mathtt{--R\_max}$ (support window).

#### 5.2.0a Strong-sector machine (macro→micro storyboard; what the code is actually doing)

This subsection is the “no-handwaving” mechanism map for **strong**. It is written so a reader can *mentally animate* the pipeline without seeing the code.

**Objects:**

- **Incoming state**: a boundary excitation that enters a local cube neighborhood.
- **Edge threads (fast)**: rigid skeleton transport (metric‑locked).
- **Bulk threads (slow)**: amorphous interior transport (gauge‑carrying; lossy/thermal).
- **Plane-sliced face**: every cube–cube face is intersected by a global plane slice; the face handshake is the 16‑thread bus $U_{ij}\in\mathbb C^{4\times 4}$.

**Micro mechanism: split–delay–recombine (the origin of $A_R+iA_I$):**
1. **Split:** when the excitation traverses $A\to B$, its transport decomposes into an **edge component** and a **bulk component**.
2. **Delay/scatter:** the bulk component experiences a timing lag $\Delta t$ and scattering due to the amorphous manifold and internal twist.
3. **Recombine at the plane-sliced face:** the two components interfere at the receiving face, producing the complex response
$$
\mathcal R(\Delta t)=e^{-\Gamma \Delta t}\,e^{i\Omega \Delta t}.
$$
4. **Identification with strong couplings:** the *magnitude loss* maps to an absorptive effect ($A_I$, $\sigma_{\mathrm{tot}}$‑sensitive) and the *phase rotation* maps to a dispersive effect ($A_R$, $\rho$‑ and CNI‑sensitive). In short:
$$
A_I \;\leftrightarrow\; \Gamma\Delta t \quad(\text{bulk loss / opacity}),\qquad
A_R \;\leftrightarrow\; \Omega\Delta t \quad(\text{phase shift / dispersion}).
$$
This is not a “fit story”: it is the operational reason the model uses **two** couplings in strong.

**Macro mechanism: why the energy axis matters (the “clock”):**

- A fixed‑energy elastic amplitude is not a long path in $L$, so tiny per‑step effects would be invisible.
- The only place the strong sector accumulates a small effect into a measurable one is the **energy axis**: increasing $\sqrt{s}$ corresponds to increasing the number of effective plane‑slice interactions / resummed exchanges.
- The accumulation proxy $\mathcal N(s)$ is therefore interpreted as an **interaction frequency count** (not an external environment).

**Two strong tests and why both are required:**

- **(A) CNI phase‑sensitivity (tiny |t|):** checks that the geometry phase does **not** destroy a published interference structure. This is the strongest falsification gate.
- **(B) Energy‑axis observables ($\sigma_{\mathrm{tot}}, \rho$):** checks whether the same mechanism reduces residuals in $\sqrt{s}$ trends at a prereg point without scanning.

#### 5.2.0b Derived strong quantities (defined explicitly; not free knobs)

These quantities appear in the equations but are **computed**, not tuned:

| Quantity | Definition | Where it enters |
|---|---|---|
| $u(s)$ | 1‑periodic CurvedCube output profile (one run of the geometry kernel) | Fourier extraction |
| $c_1$ | first harmonic $c_1=\frac{1}{N}\sum_j u(s_j)e^{-i2\pi s_j}$ | amplitude/phase template |
| $|c_1|$, $\delta_{\mathrm{geo}}$ | $|c_1|$ magnitude and $\delta_{\mathrm{geo}}=\arg(c_1)$ | modulation phase |
| $s(t)$ | fractional log‑map $s(t)=\mathrm{frac}\!\left[\ln(|t|/t_{\mathrm{ref}})/\ln(t_{\max}/t_{\mathrm{ref}})\right]$ | CNI $t\to$ phase |
| $\mathcal N(s)$ | energy accumulation proxy $\mathcal N(s)=\ln(s/s_M)/\ln(s_{\mathrm{ref}}/s_M)$ | $\sqrt{s}$ trends |

By writing them out, we prevent the common referee objection “where do these symbols come from?”

#### 5.2.0c Unitarity bookkeeping (optical theorem) in one line

The strong sector uses an absorptive component because **elastic alone is not closed**. The optical‑theorem bookkeeping can be summarized as:

- forward imaginary part $\Im F(s,0)$ fixes $\sigma_{\mathrm{tot}}(s)$,
- any “loss” from the elastic channel corresponds to **inelastic production**, not disappearance.

Our sign convention may show this as $A_I<0$ in the bridge parameterization; the physically meaningful statement is **positive opacity** $\chi_I(b)\ge 0$ in an eikonal picture.

#### 5.2.1 Why “energy accumulation” is the only plausible strong lever

In weak oscillations, a tiny per‑step phase accumulates along a macroscopic baseline L, so the total effect can be O(1). In strong scattering at fixed √s, elastic amplitudes look “instantaneous”; therefore the only strong lever analogous to “film‑like accumulation” is **the energy axis**: as √s increases, the forward amplitude effectively resums more exchanges (eikonal multi‑exchange / saturation).

This motivates using an energy‑dependent **accumulation factor**
$$
\mathcal{N}(s) \equiv \frac{\ln(s/s_M)}{\ln(s_{\mathrm{ref}}/s_M)} \quad (\text{eikonal‑count proxy})
$$
rather than a √s‑independent “constant offset”.

---

#### 5.2.2 Phase‑sensitive baseline: TOTEM 13 TeV CNI / ρ region

We use the standard Coulomb–nuclear interference (CNI) structure at very small |t|:
$$
\frac{d\sigma}{dt} = \pi\,\left| F_C(t)\,e^{i\alpha_{\mathrm{em}}\,\phi_C(t)} + F_N(s,t)\,e^{i\phi_{\mathrm{geo}}(t)} \right|^2.
$$

**Coulomb amplitude (schematic):**
$$
F_C(t) \simeq -\frac{2\alpha_{\mathrm{em}}}{|t|}\,G^2(t),
$$
with standard proton form factor G(t) and Coulomb phase $\phi_C$ (West–Yennie–type).

**Nuclear amplitude near t≈0 (frozen published baseline):**
$$
F_N(s,t) = \frac{\sigma_{\mathrm{tot}}}{4\pi}\,(i+\rho)\,e^{Bt/2}.
$$
For this CNI test we keep $\sigma_{\mathrm{tot}},\rho,B$ fixed to the published numbers used in the pack (no refit).

**Geometry phase injection (CurvedCube → phase template):**

1) CurvedCube outputs a 1‑periodic profile u(s), s∈[0,1]. 
2) We take the first harmonic:
$$
c_1 \equiv \frac{1}{N}\sum_{j=1}^N u(s_j)\,e^{-i2\pi s_j},\quad
|c_1|,\;\delta_{\mathrm{geo}}\equiv \arg(c_1).
$$
3) For each data point, map t→s(t) (preregistered mapping):
$$
x(t)=\frac{\ln(|t|/t_{\mathrm{ref}})}{\ln(t_{\max}/t_{\mathrm{ref}})},\quad
s(t)=\mathrm{frac}(x(t))\in[0,1).
$$
4) Phase template:
$$
\phi_{\mathrm{geo}}(t)=A_R\,|c_1|\,\cos\!\big(\delta_{\mathrm{geo}}\,s(t)\big).
$$

**Why split A into (A_I, A_R)?** 
Optical‑theorem logic: the forward **imaginary/absorptive** component controls $\sigma_{\mathrm{tot}}$; the **real/dispersive** component controls $\rho$ and phase‑sensitive interference. For strong we therefore track two couplings:

* $A_I$: absorptive/bulk coupling used for $\sigma_{\mathrm{tot}}$
* $A_R$: dispersive coupling used for $\rho$ and CNI phase

In this draft we report the single prereg point:
$$
A_I=-3\times 10^{-3},\qquad A_R=+3\times 10^{-3}.
$$
(Interpretation: exploratory motivation may exist historically, but inference is based on this **fixed** point only.)

**Unitarity / “where does the lost flux go?” (consistency, not a fit knob).** 
In this framework a nonzero absorptive coupling $A_I$ does **not** mean energy/information disappears. It means the *elastic channel alone* is not closed: the “missing” probability current is transferred to **inelastic production**, consistent with standard high‑energy scattering logic.

A convenient way to see this is the eikonal form in impact parameter $b$:
$$
S(b)=e^{2i\chi(b)}=e^{2i\chi_R(b)}\,e^{-2\chi_I(b)},\qquad \chi_I(b)\ge 0.
$$
Then the inelastic overlap is
$$
P_{\mathrm{inel}}(b)=1-|S(b)|^2=1-e^{-4\chi_I(b)},
$$
and the optical theorem relates the forward absorptive part to the total rate. In words: **absorption in the elastic amplitude is exactly the bookkeeping of inelasticity**, not a violation of conservation. (Our sign convention may present this as $A_I<0$ in the bridge parameterization; the physical content is $\chi_I>0$ / positive opacity.)

This draft uses this only as a **sanity constraint** on interpretation. We do *not* impose additional dispersion/black‑disk limits as priors, and we do *not* tune $A_I$ to “make unitarity work”; the point is to prevent a referee from (correctly) objecting that an imaginary term “destroys probability.”

A useful minimal motivation for the sign choice is the **quadrature** relation of a pure phase rotation:
$$
(i+\rho)\,e^{i\phi} \approx (i+\rho) + i\phi(i+\rho)
$$
so the same $\phi$ that perturbs the **imaginary** part also induces a **real** shift with an opposite sign in the small‑phase limit. The simplest prereg “one‑number” choice consistent with this is therefore $A_R \approx -A_I$, which is exactly what the current strong prereg point implements.

**CNI result (single‑shot, n_bins=25):**

* NULL (A_R=0): χ² = 1.526190
* GEO (A_R=+0.003): χ² = 1.362251
* Δχ² = 0.163939 (≈ null, no degradation)

This is our cleanest **“jury”** battlefield: baseline and covariance are healthy, and the geometry phase does **not** falsify the observable.

---

#### 5.2.3 σ_tot(√s) energy scan: COMPETE baseline + eikonal accumulation

We test the forward total cross section using a frozen COMPETE‑type baseline (parameters fixed):
$$
\sigma_{\mathrm{tot}}^{\mathrm{SM}}(s)=Z+B\ln^2\!\left(\frac{s}{s_M}\right)
+Y_1\left(\frac{s}{s_M}\right)^{-\eta_1}
\pm Y_2\left(\frac{s}{s_M}\right)^{-\eta_2},
$$
with the sign (±) for pp / $p\bar{p}$.

**Minimal absorptive modulation (single‑shot):**
$$
\sigma_{\mathrm{tot}}^{\mathrm{GEO}}(s)=\sigma_{\mathrm{tot}}^{\mathrm{SM}}(s)
\left[1 + A_I\,|c_1|\,\cos\!\Big(\delta_{\mathrm{geo}}\,\mathcal{N}(s)\Big)\right],
\qquad
\mathcal{N}(s)=\frac{\ln(s/s_M)}{\ln(s_{\mathrm{ref}}/s_M)}.
$$

**Result (channel=both, n=22):**

| channel | χ²_SM | χ²_GEO | Δχ² |
|---|---:|---:|---:|
| pp | 107.540799 | 104.305169 | 3.235630 |
| $p\bar{p}$ | 10.393117 | 10.183955 | 0.209162 |
| **total** | **117.933915** | **114.489123** | **3.444792** |

Caution: pp σ_tot compilation is heterogeneous and treated with a diagonal error model here, so χ²/ndf can be inflated by systematics/norm mixing. The sign and direction (Δχ²>0) is the key point; the absolute significance requires a better covariance model or restricted “single‑source” subsets.

> **Figure placeholder (recommended):** insert `(removed)` here — two panels showing $\sigma_{\mathrm{tot}}(\sqrt{s})$ and $\rho(\sqrt{s})$ residuals (SM vs GEO) for the prereg strong point $(A_I,A_R)=(-0.003,+0.003)$.

---

#### 5.2.4 ρ(√s) energy scan: dispersive rotation under a geometry phase

We treat ρ as a ratio of real/imag parts of the forward amplitude. Using the baseline ρ_SM(s) and applying a small phase rotation:
$$
\rho_{\mathrm{geo}}(s)=
\frac{\Re\left[(\rho_{\mathrm{SM}}(s)+i)\,e^{i\phi_{\mathrm{geo}}(s)}\right]}
{\Im\left[(\rho_{\mathrm{SM}}(s)+i)\,e^{i\phi_{\mathrm{geo}}(s)}\right]}.
$$

For the energy dependence we use an “amplitude accumulation” prescription (robust in the small‑phase limit):
$$
\phi_{\mathrm{geo}}(s)=A_R\,|c_1|\,\mathcal{N}(s)\,\cos(\delta_{\mathrm{geo}}),
\qquad
\mathcal{N}(s)=\frac{\ln(s/s_M)}{\ln(s_{\mathrm{ref}}/s_M)}.
$$

**Result (channel=both, n=4):**

* NULL (A_R=0): χ² = 17.851169
* GEO (A_R=+0.003): χ² = 17.208047
* Δχ² = 0.643122

Caution: current ρ dataset is tiny (n=4), so this is only a directional hint.

---

#### 5.2.5 Consistency check: dispersion relation “ρ predicted from σ_tot”

If one enforces that ρ(s) is not independently coupled but derived from σ_tot(s) via a derivative‑dispersion relation (DDR)–type proxy, then the sign preference can change. We include this as a **diagnostic**, not as a discovery claim.

**DDR proxy test output (n=4):**

* NULL: χ² = 29.250876
* GEO using σ_tot modulation (A_I=-0.003): χ² = 29.651184
* Δχ² = -0.400308

Interpretation: σ_tot‑driven modulation alone does not automatically improve ρ; this is the main reason we track (A_I, A_R) separately in the current strong bridge.

---

#### 5.2.6 Reproducibility: current strong-sector command source

The legacy strong-sector runbook references have been removed from the main text to avoid preserving obsolete command names.

Use **Section 8** for the current canonical strong performance commands and paths.

### 5.3 Cross‑sector parameter locking

Across weak/EM/strong, we keep a minimal set of global geometry knobs fixed (e.g. geometry structure/generator choices, and common damping envelopes where applicable), and introduce only sector‑specific ingredients that have a clear physical role.

- **Weak:** propagation-phase modulation inside the unified equation, with an explicit gate $\kappa_{\mathrm{gate}}\in\{0,1\}$ used for *null-limit consistency*.
- **Strong:** split couplings $(A_I,A_R)$ reflecting absorptive ($\sigma_{\mathrm{tot}}$) vs dispersive/phase ($\rho$, CNI) sensitivity; the current prereg point uses the minimal relation $A_R\approx- A_I$.
- **EM (Bhabha):** a shape-level multiplicative deformation on an imported baseline, enforced as **shape-only** (per-group zero-mean) and, in the strongest holdout checks, **pivot-centering** to remove DC normalization components without re-fitting nuisance normalizations.

A recurring practical point is that the raw amplitude parameter $A$ is not a universal “physical strength” by itself: the meaningful quantity is an **effective amplitude** (e.g. $A_{\mathrm{eff}}\sim A\alpha g_{\mathrm{gen}}\sin\phi$ or directly $\mathrm{RMS}[\delta]$), which should be used when transporting a locked hypothesis across panels.

## 6. Gravitational-wave sector (ringdown-only): cubic-lattice response + detector projection

This section documents a third instantiation of the same “structured-kernel” philosophy: a **mechanistic discrete substrate model** (a damped cubic lattice with an embedded bubble + constant-tension threads) generates a **two-component polarization basis** $h_+(t),h_\times(t)$. These are then projected into each interferometer via standard antenna pattern factors and compared to data in a ringdown-only window.

The intent is not to replace full GR waveform modeling, but to provide a **controlled, falsifiable reverse-engineering test**: if a compact low-dimensional lattice response can systematically predict correlated structure across detectors (beyond off-source backgrounds), it becomes a candidate geometric kernel worth further study.

### 6.0 Parameter definitions and reproducibility mapping (GW sector)

This subsection defines the key parameters used in the GW sector and maps them to the command-line flags used in the reproducible runs below.

#### 6.0.1 Lattice simulation (SIM) parameters (code-faithful, v9 “new geometry”)

This section is intentionally **code-faithful** to the current v9 runner (the same family used in the two-phase GW tests). The knobs group naturally into geometry, CT/RT threads, damping/integration, auxiliary-field gating, and detector projection.

**Core geometry**

- `--nx --ny --nz`: number of cubes in each axis.
- `--L0`: cube edge length $L_0$ (sets the rest geometry scale).
- Plane selection for the **auxiliary-field layer** (TT2 / gating): 
 `--plane_axis` (typically `z`), `--plane_cz` (interface index), `--plane_mode`, `--plane_components`.

**CT (tension-only) threads (intra-cube + bubble connections)** 
These implement Sec. 2.5.2 and are **one-sided** (never compressive).

- `--T_cb`: bubble–corner CT tension $T_{\mathrm{cb}}$ (8 per cube).
- `--T_edge --T_face --T_body`: corner–corner CT tensions inside each cube (edge / face-diagonal / body-diagonal).
- `--c_ct`: CT damping coefficient $c_{\mathrm{ct}}$.
- `--ct_soft_eps`: CT softening length $\varepsilon$ in $T\tanh(d/\varepsilon)$.

**RT (stretch-only spring) inter-cube threads (face couplers)** 
These implement Sec. 2.5.3 and are the *primary* control knob for the collective mode scale.

- `--k_rt`: inter-cube stiffness $k_{\mathrm{rt}}$ (baseline for the new-geometry scan: $k_{\mathrm{rt}}=100$).
- `--p_rt`: power $p_{\mathrm{rt}}$ in $k\,\mathrm{stretch}^{p}$.
- `--rt_T0`: baseline tension $T_{0,\mathrm{rt}}$.
- `--c_rt`: RT damping coefficient $c_{\mathrm{rt}}$.
- `--rt_face_diagonals`: if set, each shared face uses **16 links per face** (maximally symmetric 4×4 coupling); otherwise 4 links per face.
- Optional anisotropic RT variants (kept explicit, not “fitted”): 
 `--k_rt_diag`, `--k_rt_rot_deg`, `--c_rt_diag`, `--c_rt_rot_deg`, `--rt_L0_scale`.

**Time stepping / damping / boundary absorption**

- `--duration --steps`: simulation time and number of main steps (dt = duration/steps).
- `--substeps`: sub-stepping inside each main step.
- `--integrator`: time integrator (e.g. leapfrog).
- `--gamma`: global velocity damping term.
- `--gamma_absorb --absorb_thickness`: boundary absorber strength and thickness (optional).
- `--strict_closed`: enforce strict closure constraints if enabled.

**Drive / source**

- Generic source: `--source_mode` (plus/cross), `--source_center`, `--source_radius`, `--source_t_end`.
- Ringdown drive: `--ringdown_drive` with 
 `--ring_f0_hz`, `--ring_tau_s`, `--ring_t_start`, `--ring_t_end`, `--ring_phase_deg`, `--ring_amp`.

- Additional drive controls: `--drive_pattern`, `--drive_gain`, `--drive_gate_only`.

**Auxiliary-field gating + backreaction (TT2 plane)**

- `--enable_gauge_plane`: enable the auxiliary field layer $\phi$ on the chosen plane.
- `--enable_backreaction`: allow $\phi$ to scale RT links crossing the plane.
- Field dynamics: `--gamma_phi`, `--c_phi`.
- Gate parameters (see Sec. 2.5.5): `--gate_apply`, `--gate_phi0`, `--gate_beta`, `--gate_hard`, `--gate_use_abs`, `--gate_threshold`.

**Detector projection (GW)**

- `--project_detectors` / `--proj_detectors H1,L1(,V1)`: enable detector projection.
- Sky/polarization: `--sky_ra_deg`, `--sky_dec_deg`, `--pol_psi_deg` (and optional `--gmst_deg`).
- Detector geometry controls (if overriding defaults): `--det_z`, `--det_rot_deg`, `--det_tol`, `--H1_xarm_az_deg`, `--L1_xarm_az_deg`, `--V1_xarm_az_deg`.
- Output: `--out_csv`, `--output`, optional `--phi_snapshot_npy`.

The key point for falsification workflow is that the **“new geometry”** is structurally fixed (Sec. 2.5): we vary $k_{\mathrm{rt}}$ (and secondarily damping) to bring the dominant modes into the ringdown band, without changing the topology.

#### 6.0.1a Current calibration status: frequency content vs the 250 Hz target

A key practical lesson from the January 2026 GW150914 “two-phase” experiments is that **the pipeline can be real-data connected**, but the **micro-simulator’s dominant frequencies must be calibrated** before ringdown-band comparisons can be meaningful.

Using the free-decay window $t\in[0.02,0.2]$ s from the uploaded 2-phase run artifacts (see §8.7), a simple FFT diagnostic on the raw plus/cross proxies shows:

- **dominant power in $h_\times$** at $\sim 5.6$ Hz (most of the free-decay energy),
- only a very small fraction of power in the **100–350 Hz** “ringdown comparison band”.

This explains the empirical outcome that (after bandpass to 100–350 Hz) the model’s H1–L1 correlation becomes small in magnitude: the bandpass is discarding nearly all of the model’s power, leaving only numerical residuals.

**Interpretation in this draft:** this is **not** a fundamental falsification of the lattice+bubble geometry; it is a **frequency-calibration failure mode** of the current parameter set (notably $k_{rt}$, damping, and possibly inertia/resolution choices). Therefore, the GW track in this draft treats:

- **geometry + projection + falsification metrics** as the validated part of the pipeline, and
- **$k_{rt}$/damping calibration to QNM-like bands** as the open physics task.

In other words: *the experiment falsifies “this particular parameter set reproduces a 250 Hz ringdown”, not the whole geometric substrate ansatz.*

#### 6.0.2 Hybrid basis construction (optional)

When the raw plus/cross proxies are not sufficiently independent, we used a deterministic hybridization:

- cross(t) = cross0(t) + lambda * crossAB(t)

where cross0 is taken from the CROSS SIM run, and crossAB is the differential readout channel.

- lambda : mixing coefficient (in the current experiments, chosen to reduce plus/cross colinearity at Gate-0)

#### 6.0.3 Ringdown correlation runner parameters

These are the main flags of the ringdown runner script that consumes the model CSV and the detector HDF5 strain data.

- Data inputs
 - h1_hdf5, l1_hdf5, v1_hdf5 : detector strain files
 - center_guess_gps : event center time (GPS)

- Antenna patterns / sky geometry
 - auto_event gw170814 : convenience option that sets event-specific defaults (e.g., uses 3-det patterns)
 - auto_antenna : compute (Fplus,Fcross) from (ra_deg, dec_deg, psi_deg) and center_guess_gps
 - ra_deg, dec_deg, psi_deg : sky position and polarization angle
 - Fplus_H1, Fcross_H1, ... : manual antenna pattern override (used when auto_antenna is not used)

- Model CSV layout
 - model_csv : CSV containing model time series
 - t_col : time column name (seconds)
 - model_col_plus, model_col_cross : plus/cross proxy column names
 - model_t0peak_col : column used to define the model peak time (t=0 alignment)

- Analysis windowing and filtering
 - anchor_band : band (Hz) used for finding the anchor correlation
 - analysis_band : band (Hz) used for the reported correlations
 - ringdown_start_s, ringdown_dur_s : time window relative to the model peak
 - time_scales : number of time-scale variants (multi-scale improves null smoothness)

- Time alignment
 - fixed_anchor_lag_s : fixed lag for the anchor alignment (e.g., the H1-L1 lag)
 - fixed_anchor_lag_h1_v1_s : fixed H1-V1 relative lag (3-det)
 - max_model_lag_s : allowed extra model lag freedom (0 means fixed)

- Null/offsource background
 - offsource_n : number of offsource trials
 - seed : RNG seed

- Reported statistics (in summary.json)
 - event_abs_corr_avg : the on-source abs correlation average (defines the abs threshold)
 - event_min_abs_corr : the on-source minimum abs correlation (defines the min threshold)
 - p_abs_corr : fraction of offsource trials with abs_corr_avg >= event_abs_corr_avg
 - p_min_abs_corr : fraction of offsource trials with min_abs_corr >= event_min_abs_corr
 - p_joint_abs_and_minabs : fraction of offsource trials satisfying both thresholds simultaneously

### 6.1 Discrete dynamics in the new geometry (CT/RT + optional REP1 + auxiliary-field gating)

#### 6.1.0 How to *picture* the GW kernel in 3D (planes, RT “springs”, CT “rigidity”, and detector readout)

This subsection is intentionally **visual / operational**: it answers “what is a GW in this lattice?” without hand‑waving.

**Objects (recap, but in GW language).**

- **RT inter‑cube links** are the *metric-carrying* elastic skeleton: they **stretch with distance** and transmit long‑range stress.
- **CT intra‑cube links** (and bubble↔corner CT ropes) are the *gauge‑rigidity* elements: they are **one‑sided** (tension‑only) and resist compressive “ghost” modes.
- **Global planes** provide the *reference sheets* that slice cube–cube contacts. In GW runs, they matter only when we enable the auxiliary field layer (Sec. 6.1.4 / 7.B.9): the plane is where the auxiliary field lives and where RT links can be gated/backreacted.

**No “plane → plane wires”.**  
Even in GW/DM language, we do **not** add direct couplers between parallel planes. Any plane‑to‑plane stress/phase propagation is mediated by the RT skeleton (cube↔cube external links). This keeps the model closed: *stress travels through the lattice, not through a hidden broadcast channel.*

**Mental movie (GW ringdown, 8 frames).**
1) **Prepare** a cubic volume (nx×ny×nz) with RT links active (optionally with 16 links per face for maximal symmetry).  
2) **Excite** a localized region with a quadrupole drive pattern (`quad_plus_xy` or `quad_cross_xy`) during the **drive window** $t\in[t_s,t_e]$.  
3) **Deform** the RT skeleton: inter‑cube distances change and store elastic energy (this is the GW “strain energy” in the model).  
4) **Couple** to local rigidity: CT ropes constrain motion and suppress unphysical compressive shortcuts (one‑sided tension law).  
5) **(Optional) Gate/backreact** on a chosen global plane: RT links crossing the plane are modulated by $s_{ij}(\phi)$ and, if enabled, the lattice feeds back into $\phi$ with stiffness $\kappa_{\mathrm{back}}$.  
6) **Turn the drive off** at $t=t_e$. From now on the evolution is free decay (Sec. 6.1.5).  
7) **Propagate**: the disturbance travels through the RT network; boundary absorbers (if enabled) prevent artificial reflections.  
8) **Read out** two orthogonal polarizations as linear functionals (Sec. 6.2) and project them onto detector channels (Sec. 6.4).

**Why `det_rot_deg` exists (diagnostic, not “fitting”).**  
A detector‑frame rotation by $\theta_{\mathrm{det}}$ mixes the two basis responses. In the simplest linear picture,
$$
\begin{pmatrix} h_+^{\mathrm (det)} \\ h_\times^{\mathrm (det)} \end{pmatrix}
=
\begin{pmatrix}
\cos 2\theta_{\mathrm{det}} & \sin 2\theta_{\mathrm{det}} \\
-\sin 2\theta_{\mathrm{det}} & \cos 2\theta_{\mathrm{det}}
\end{pmatrix}
\begin{pmatrix} h_+ \\ h_\times \end{pmatrix}.
$$
So a 45° check is a **sanity test**: if the simulator truly produces a two‑polarization response, rotating the detector basis must redistribute power between the two channels. If “cross” stays identically zero under rotation, the issue is in the **SIM symmetry** or **readout operator**, not in the sky projection.

**Address map (GW sector).**  
GW ringdown is **RT‑addressed** (external links); the auxiliary plane (if enabled) is a *global slice controller* that can gate/backreact RT crossings. This is distinct from:

- Weak: **edge‑addressed** holonomy/phase memory,
- Strong: **bulk‑addressed** desynchronization/jitter (complex response),
- EM: **junction‑addressed** stiffness filtering.

Let $i$ index all lattice nodes (corners and bubbles). Each node has position $\mathbf{x}_i(t)=\mathbf{x}^{(0)}_i+\mathbf{u}_i(t)$, velocity $\mathbf{v}_i(t)$, and (for simplicity) a common mass $m$ (code allows a scalar mass-like normalization).

The node-level equations of motion are:
$$
m\,\ddot{\mathbf{u}}_i
=
-\gamma\,\mathbf{v}_i
+\sum_{(i,j)\in \mathcal{E}_{\mathrm{CT}}}\mathbf{F}^{\mathrm{CT}}_{i\leftarrow j}
+\sum_{(i,j)\in \mathcal{E}_{\mathrm{RT}}} s_{ij}(\phi)\,\mathbf{F}^{\mathrm{RT}}_{i\leftarrow j}
+\sum_{(i,j)\in \mathcal{E}_{\mathrm{REP}}}\mathbf{F}^{\mathrm{rep}}_{i\leftarrow j}
+\mathbf{F}^{\mathrm{drive}}_i(t),
$$
where:

- $\mathcal{E}_{\mathrm{CT}}$: CT (tension-only) edges (bubble–corner + intra-cube corner–corner).
- $\mathcal{E}_{\mathrm{RT}}$: RT (stretch-only spring) edges (inter-cube face couplers).
- $\mathcal{E}_{\mathrm{REP}}$: optional bubble–corner repulsion edges (REP1).
- $s_{ij}(\phi)\in[0,1]$: auxiliary-field gate scale applied only to RT links crossing the chosen plane (Sec. 2.5.5). For all other links $s_{ij}=1$.

All internal pairwise forces obey Newton’s third law and are applied along the separation unit vector $\hat{\mathbf{n}}_{ij}$.

#### 6.1.1 Code-faithful CT force law (one-sided rope)

For a CT link $\ell=(i,j)$ with parameters $(T_\ell,c_\ell,\varepsilon_\ell)$:
$$
\mathbf{F}^{\mathrm{CT}}_{i\leftarrow j}
=
\max\!\left(0,\;T_\ell\,\tanh\!\frac{d_{ij}}{\varepsilon_\ell}\;+\;c_\ell\,(\Delta\mathbf{v}_{ij}\!\cdot\!\hat{\mathbf{n}}_{ij})\right)\hat{\mathbf{n}}_{ij},
\quad
d_{ij}=\|\mathbf{x}_j-\mathbf{x}_i\|.
$$
The $\max(0,\cdot)$ clamp enforces **no compression**.

#### 6.1.2 Code-faithful RT force law (slack + stretch restoring)

For an RT link $e=(i,j)$ with $(L_{0,e},k_e,p_e,c_e,T_{0,e})$ and stretch $s_{ij}=d_{ij}-L_{0,e}$:
$$
T^{\mathrm{RT}}(s_{ij})=
T_{0,e}+\mathbf{1}_{s_{ij}>0}\,k_e\,s_{ij}^{p_e},
\qquad
\mathbf{F}^{\mathrm{RT}}_{i\leftarrow j}
=
\max\!\left(0,\;T^{\mathrm{RT}}(s_{ij})\;+\;c_e(\Delta\mathbf{v}_{ij}\!\cdot\!\hat{\mathbf{n}}_{ij})\right)\hat{\mathbf{n}}_{ij}.
$$
Thus RT links behave like a rope with baseline tension $T_0$, plus a spring-like restoring term only under extension.

#### 6.1.3 Inter-cube coupling topology (why “16 links per face” matters)

Let two cubes share a face. Each face contains 4 corner nodes on cube A and 4 on cube B. 
With `rt_face_diagonals` enabled, we include four 4-corner matchings that together generate the full $4\times4$ connectivity (16 links). This enforces discrete symmetry of face coupling and prevents accidental anisotropies from “partial” coupling patterns.

#### 6.1.4 Auxiliary-field gate $s_{ij}(\phi)$

On the chosen interface plane, the auxiliary field $\phi$ lives on plane cells. For a plane-crossing RT link $e$, we assign it to a plane cell and set
$$
s_{ij}(\phi)=g(\phi_{\mathrm{cell}}),\qquad
g(\phi)=\frac{1}{1+\exp\{-\beta(|\phi|-\phi_0)\}},
$$
or a hard-threshold form when `--gate_hard` is enabled. In TT2 mode the amplitude $|\phi|=\sqrt{\phi_+^2+\phi_\times^2}$ is used.

#### 6.1.5 Two-phase ringdown protocol (drive ON → free decay)

For GW falsification we explicitly separate:

- **Drive window** $t\in[t_s,t_e]$: apply $\mathbf{F}^{\mathrm{drive}}(t)$ (ringdown-drive envelope).
- **Free-decay window** $t>t_e$: set $\mathbf{F}^{\mathrm{drive}}(t)=0$ and compare only the free evolution to GW ringdown data.

This prevents “forced response” contamination and makes the comparison conceptually aligned with black-hole QNM ringdown (free decay after excitation).

### 6.2 Plus/cross excitation and readout as linear functionals

We generate two basis responses by running the same substrate with two orthogonal quadrupole drives in the $x\text{–}y$ plane:

- `drive_pattern=quad_plus_xy` → produces a basis waveform we label $h_+^{(0)}(t)$,
- `drive_pattern=quad_cross_xy` → produces a basis waveform we label $h_\times^{(0)}(t)$.

In the simplest linear regime, the measured “template” channels are linear functionals of the simulated state:
$$
h_+(t)=\langle \mathbf{r}_+,\mathbf{u}(t)\rangle,\qquad h_\times(t)=\langle \mathbf{r}_\times,\mathbf{u}(t)\rangle,
$$
where $\mathbf{u}(t)$ is the stacked displacement vector and $\mathbf{r}_+,\mathbf{r}_\times$ are readout vectors determined by the chosen readout operator.

**Gate-0 degeneracy and how we broke it.** Early “gate-0” checks showed near-perfect colinearity between the nominal plus/cross CSVs (a symmetry/degeneracy problem), making sky/polarization inference impossible. Two robust symmetry-breaking mechanisms were implemented/used:

1) **Physical mixing knobs inside the SIM:** tensor-mode full coupling, anisotropic $\mathbf{K}_{\mathrm{mat}}$ / $\mathbf{C}_{\mathrm{mat}}$ and optional gyro-coupling.

2) **Split readout (AB differential):** define two readouts (A,B) and use
$$
h^{AB}_+(t)=h^A_+(t)-h^B_+(t),\qquad h^{AB}_\times(t)=h^A_\times(t)-h^B_\times(t).
$$
This yielded a low-correlation (near-orthogonal) plus/cross basis at gate-0.

### 6.3 HYBRID mixing and making $\lambda$ “physical”

When split-readout produces a weak but useful “mixing channel” $h^{AB}_\times(t)$, we used a hybrid construction
$$
h_\times(t)=h^{(0)}_\times(t)+\lambda\,h^{AB}_\times(t),
$$
with $\lambda$ initially explored as a tuning knob.

To avoid an ad-hoc free parameter in a publication context, there are two defensible routes:

**A) Preferable (cleaner): remove HYBRID; generate mixing directly in the SIM.**

Use **physical** couplings (`gyro_gain`, full tensor coupling, off-diagonal stiffness/damping, revised readout) to produce a well-conditioned $(h_+,h_\times)$ basis *without* post-hoc $\lambda$.

**B) If HYBRID is kept: choose $\lambda$ deterministically from SIM-only orthogonalization.**

On a fixed gate-0 window $W$ (e.g. $t\in[0,0.04]$ s), define the mean-removed inner product
$$
\langle a,b\rangle_W\equiv\sum_{t\in W}\big(a(t)-\bar a\big)\big(b(t)-\bar b\big).
$$
Choose $\lambda$ by enforcing $\langle h_\times,h_+\rangle_W=0$:
$$
\lambda^* = -\frac{\langle h_\times^{(0)},\,h_+\rangle_W}{\langle h_\times^{AB},\,h_+\rangle_W}.
$$
This makes $\lambda$ a **deterministic, data-independent** number derived only from the SIM outputs.

In the small-mixing regime one can further calibrate $\lambda\approx K\,g_0$ by measuring $\lambda^*$ over a grid of gyro gains $g_0$.

### 6.4 Detector projection: antenna patterns and time delays

Given sky position $(\alpha,\delta)$ and polarization angle $\psi$, the predicted strain in detector $d$ is
$$
h_d(t)=F^d_+(\alpha,\delta,\psi)\,h_+(t-\tau_d)+F^d_\times(\alpha,\delta,\psi)\,h_\times(t-\tau_d),
$$
with:

- $F^d_+,F^d_\times$ the standard interferometer antenna pattern factors,
- $\tau_d$ the geometrical arrival-time delay for detector $d$ relative to a reference (computed from the propagation direction and detector locations).

**Polarization is a basis choice (do not “optimize” it).**  
A change of polarization frame by $\psi$ mixes $h_+$ and $h_\times$ by a $2\psi$ rotation (Stokes $Q/U$ analogy). Therefore a dense $\psi$ scan can silently become a *template search*. In this work we treat $\psi$ as an **extrinsic gauge choice** and handle it in a preregistered way:

- We either **fix** $\psi$ to a single preregistered value (default),
- or report an **ablations set** $\psi\in\{0^\circ,45^\circ\}$ (and optionally $90^\circ$) purely as a sanity check.  
No “best‑$\psi$” selection is performed.

In our runner, the projection inputs are produced either by:

- explicit $(F_+,F_\times)$ inputs per detector, or
- `--auto_antenna --sky_ra_deg --sky_dec_deg --pol_psi_deg` (computes $F_+,F_\times$ and uses `center_guess_gps` for the Earth-rotation phase).

For GW150914 and GW151226, median $(\alpha,\delta)$ values were extracted from GWTC-1 PE samples (Overall posterior) and used as fixed inputs. The polarization angle is **not** taken from PE (not present in those fields); it is treated as the preregistered extrinsic choice described above.

### 6.5 Ringdown-only statistic and off-source p-values

We compare the model to bandpassed/whitened strain data in a ringdown window
$[t_0+t_{\mathrm{start}},\;t_0+t_{\mathrm{start}}+t_{\mathrm{dur}}]$
with configurable analysis bands and fixed anchor lags.

For each detector we compute a correlation score (Pearson correlation of windowed sequences). We then form two summary statistics:

- **Average absolute correlation**
$$
\mathrm{abs\_corr\_avg}=\frac{1}{N_d}\sum_d |\mathrm{corr}_d|,
$$

- **Minimum absolute correlation**
$$
\mathrm{min\_abs\_corr}=\min_d |\mathrm{corr}_d|.
$$

Off-source (null) samples are generated by selecting $N$ background windows around the event time (excluding a guard region), recomputing these metrics, and counting exceedances relative to the on-source thresholds.

Let $k_{\mathrm{abs}}$ be the number of off-source samples with $\mathrm{abs\_corr\_avg}\ge \mathrm{abs\_corr\_avg}^{\mathrm{event}}$, and similarly $k_{\min}$ for $\mathrm{min\_abs\_corr}$.

Define
$$
p_{\mathrm{abs}}=\frac{k_{\mathrm{abs}}+1}{N+1},\qquad p_{\min}=\frac{k_{\min}+1}{N+1}.
$$
For a stricter “all detectors good simultaneously” tail test, define
$$
k_{\mathrm{joint}}=\operatorname{card}\Big\{\mathrm{abs\_corr\_avg}\ge \mathrm{abs\_thr}\ \wedge\ \mathrm{min\_abs\_corr}\ge \mathrm{min\_thr}\Big\},
$$
with thresholds set by the on-source values, and
$$
p_{\mathrm{joint}}=\frac{k_{\mathrm{joint}}+1}{N+1}.
$$
When $k_{\mathrm{joint}}=0$, this reports a **finite upper bound** $p_{\mathrm{joint}}\lesssim 1/(N+1)$.

### 6.6 “Artefact vs real” diagnostics (required for publication)

Two quick tests separate genuine joint-tail structure from statistic/quantization artefacts:

**Test A — allow small model-lag freedom.** Increase `--max_model_lag_s` (e.g. 0.002–0.004 s). If a previously “zero” $p_{\mathrm{joint}}$ becomes nonzero and stable, the earlier result was likely dominated by a too-discrete lag grid.

**Test B — increase `--time_scales`.** Set `--time_scales` to 2–3. This increases the diversity of null samples and reduces “blockiness”. If $p_{\mathrm{joint}}$ changes drastically, interpretation must emphasize statistic-definition sensitivity.

**Example diagnostic outcome (GW170814, HYBRID $\lambda\sim10^9$).**

A run with fixed lag and `time_scales=1` produced $k_{\mathrm{joint}}=0$ even at $N=100000$, while marginals gave $p_{\mathrm{abs}}\sim 0.05$ and $p_{\min}\sim 0.06$. Off-source samples showed many “near misses” in which $\mathrm{abs\_corr\_avg}$ saturated just below threshold, strongly suggesting discretization/quantization effects.

Re-running with `--max_model_lag_s 0.002` restored a nonzero joint tail (e.g. $p_{\mathrm{joint}}\approx 0.014$ at $N=20000$) while keeping $\mathrm{min\_abs\_corr}$ comparatively strong. In contrast, `time_scales=2` (TS2) strongly reduced on-source scores and yielded non-significant $p_{\mathrm{joint}}$, consistent with TS1 being the physically appropriate scale for GW170814.

**Note on $\psi$-dependence (GW150914, HYBRID).** In exploratory scans of $\psi$ using the HYBRID basis, $p_{\mathrm{joint}}$ showed modest but structured variation (with a $90^\circ$ periodicity expected from the $F_+/F_\times$ rotation), reaching $\mathcal{O}(10^{-2})$ in the best cases. This contrasts with earlier $\psi$-invariant results obtained when the SIM plus/cross readout was nearly colinear (gate-0), highlighting the need for a genuinely 2D polarization basis before attempting polarization/localization claims.

### 6.7 What this does (and does not) imply about localization

**Claim level note (important):** the results in §6 are discussed as **detection-grade template evidence**, *not* as a finalized sky-localization measurement.

A robust match in $p_{\mathrm{abs}}$, $p_{\min}$, or $p_{\mathrm{joint}}$ is evidence that the **template family** captures real correlated structure.

However, **precise sky localization** is a separate and harder requirement. Localization depends primarily on time-delay geometry and antenna response degeneracies; even standard LIGO-Virgo localizations are broad regions, not points.

In this framework, a localization claim would require at minimum:

- fixing the plus/cross basis degeneracy (so $\psi$ matters),
- scanning $(\alpha,\delta,\psi)$ on a grid and verifying a stable maximum,
- demonstrating robustness to lag freedom, time_scales, band choices, and multiple-testing penalties.

For the present draft we treat localization as a **pipeline extension** rather than a primary claim.

## 7. Dark matter sector (SPARC/RAR)

**Objective.** Test whether a unified-equation-inspired environment modulation can reproduce the SPARC/RAR relation with strong out-of-sample behavior, compared to a baryon-only baseline.

**What was achieved in this draft.** The dataset, likelihood, model family, and CLI mapping are specified to make runs reproducible.
**Mechanism sketch (what “DM” means in this substrate).** 
The DM/RAR module is *not* framed as “a new particle halo”. In the CurvedCube picture, a galaxy is a long‑baseline, many‑junction object that can impose a **cumulative stress** on the **Global Lock Plane** (the same reference manifold used for localization/gauge continuity). That stress modifies the *effective transport geometry* experienced by baryonic tracers, i.e. it shifts an effective metric $g_{\mathrm{eff}}$ on large scales.

A minimal way to state the hypothesis without over-committing is:
$$
g_{\mathrm{obs}}(r)=\mathcal{F}\big(g_{\mathrm{bar}}(r);\;\Sigma_{\mathrm{lock}}(r)\big),\qquad
\Sigma_{\mathrm{lock}}(r)\equiv \text{(integrated lock‑plane stress proxy)},
$$
where $\Sigma_{\mathrm{lock}}$ is computed from baryonic configuration and the substrate response rule (environment/lock coupling). The *claim under test* is simply whether a preregistered $\mathcal{F}$ yields the observed RAR with strong out‑of‑sample performance.

> Status (honest): the **mechanistic interpretation** above is the intended physical reading of why a galaxy can look “over‑gravitating” without non‑baryonic mass. The present draft section is a **pipeline‑defined falsification test**; it becomes a physics claim only after the updated geometry version is re‑run and the preregistered comparisons are passed.

**What remains.** Add a compact result table (best-fit A, α, env params; χ²/ndof; held-out validation) and a sensitivity study for priors and systematics (distance inclinations, error inflation, etc.).

This section adds the galaxy-scale **DM/RAR (SPARC)** validation track. The goal is to test whether the same “baseline × modulation” discipline used in the weak/strong/EM tracks can reproduce the observed radial-acceleration relation with strong **out-of-sample** performance.

### 7.1 Dataset and likelihood
We use a SPARC RAR point CSV (project-produced) containing, at minimum:

- identifiers and radii: `galaxy`, `r_kpc`
- observed kinematics: `v_obs_kms`, `e_v_kms`
- baryon components: `v_gas_kms`, `v_disk_kms`, `v_bul_kms`, and combined `v_bar_kms`
- accelerations: `g_obs_mps2`, `g_bar_mps2`
- uncertainty proxy: `sigma_log10_gobs` (used by the pipeline’s chi-square)
- optional: `env_scale` (not required for the galaxy-closed DM results reported here)

The pipeline evaluates goodness-of-fit through a weighted chi-square (log-space where applicable):
$$
\chi^2 = \sum_i \frac{(d_i - m_i)^2}{\sigma_i^2}.
$$

### 7.2 GEO modulation model and fitting protocol (`geo_add_const`)
We use the `geo_add_const` modulation scanned on a 2D grid in $(A,\alpha)$ with a fixed reference scale $g_0=1.2\times 10^{-10}$. Predictions are implemented as baryonic baseline plus a constrained geometric correction:
$$
g_\mathrm{pred}(g_\mathrm{bar}) = g_\mathrm{bar} + \Delta g_\mathrm{geo}(g_\mathrm{bar};A,\alpha,g_0),
$$
in the code-faithful form used by the DM scripts.

#### 7.2.1 DM mechanism (galaxy scale): Global-lock-plane stress → effective acceleration

This section is the **mechanistic** bridge for the DM/RAR track: the halo effect is not a new particle, but a **collective elastic response** of the same lattice used elsewhere.

**3D picture (static).**

- Space is a volume filled by CurvedCubes.
- Neighbor cubes are tied by **external RT threads** (distance‑dependent tension; “springs”).
- Each cube’s bubble state is anchored to the global reference via **internal links** (the same “locking” concept used for localization).
- Parallel global planes are **not** connected by direct wires; plane‑to‑plane coupling is *mediated through the cube lattice* (RT network).

**What baryons do.**
A baryonic mass distribution provides a stress source for the RT spring network. In the weak‑field regime, we treat the baryon‑only acceleration $g_{\mathrm{bar}}(r)$ as the observable proxy for this stress.

**What the lattice does in response.**
The RT network transmits that stress over large distances. Because the planes/anchors are tied to the cubes, a large‑scale stress field produces a slow, coherent shift of the locking reference across the galaxy. Operationally, this appears as an **effective metric deformation**
$$
g_{\mu\nu}\;\to\;g^{\mathrm{eff}}_{\mu\nu}(r),
$$
which an orbiting tracer reads as an extra inward acceleration component $\Delta g_{\mathrm{geo}}$.

**What we test (RAR form).**
We compress the above into the RAR mapping used in code:
$$
g_{\mathrm{pred}}(g_{\mathrm{bar}}) \;=\; g_{\mathrm{bar}} + \Delta g_{\mathrm{geo}}(g_{\mathrm{bar}};A,\alpha,g_0).
$$

- $g_0$ is a fixed transition scale in this draft (canonical value $1.2\times 10^{-10}\,\mathrm{m/s^2}$).
- $A$ sets the amplitude of the plane‑stress response.
- $\alpha$ sets the sharpness/shape of the transition from the baryon‑dominated to stress‑dominated regime.

**Anti-circularity note (why “environment” is not a cheat).**
A known failure mode is to define the environment from $v(r)$ or $g_{\mathrm{obs}}(r)$ (which would be circular in RAR). The DM track therefore uses either:
1) an *external* galaxy label (e.g., a single $v_{\mathrm{flat}}$ proxy) treated as fixed metadata, or
2) a self‑consistent fixed‑point update where the environment is recomputed from the model’s own $g_{\mathrm{pred}}$ until convergence.
Both prevent “using $v$ to explain $v$”.

#### 7.2.2 “Animation” storyboard for DM (plane‑stress picture)

Frame A — **Baryons set $g_{\mathrm{bar}}(r)$.** This is the only direct input from the galaxy.

Frame B — **RT springs deform.** External threads change tension with distance; the deformation propagates outward through the cube network.

Frame C — **Planes inherit stress (mediated).** No plane‑to‑plane wires: the lattice transmits the displacement, so parallel planes shift relative phase/spacing through the cubes.

Frame D — **Anchors update local lock reference.** Each cube’s internal anchor feels the slowly varying global shift; the local “rest condition” is altered.

Frame E — **Tracer reads $g_{\mathrm{pred}}=g_{\mathrm{bar}}+\Delta g_{\mathrm{geo}}$.** The extra term is the macroscopic expression of the accumulated stress field.

Frame F — **Saturation/closure (optional).** If the UV completion is enabled (Sec. 7.3), a stiffness+gate prevents runaway response in extreme‑stress tails and forces galaxy‑closed behavior.

**Protocol.**

- **Grid scan:** evaluate $\chi^2$ across the $(A,\alpha)$ grid and select the minimum.
- **K-fold CV:** repeat 5-fold CV and report held-out (test) $\Delta\chi^2$ improvements. We additionally repeat with multiple random seeds for robustness.

### 7.3 Thread-network UV completion (STIFF+GATE; galaxy-closed autocalibration)
We include an optional thread-network UV completion with nonlinear stiffness and a gate. A per-point stress proxy $S$ is mapped to:

- nonlinear stiffness
$$
S_{\mathrm{eff}}(S)=k_2 S^2 + k_4 S^4
$$

- gate
$$
g(S_{\mathrm{eff}})=\frac{x^p}{1+x^p},\qquad x=\frac{S_{\mathrm{eff}}(S)}{S_0}.
$$

The effective environment factor is applied schematically as:
$$
\mathrm{env}_{\mathrm{final}} = 1 + g\,(\mathrm{env}_{\mathrm{thread}}-1),
$$
so that $g\to 0$ implies **decoupling** and $g\to 1$ implies the thread-network can become fully active (reserved for extreme-stress tracks).

**Galaxy-closed autocalibration.**
Parameters are autocalibrated from SPARC so that the gate is closed at the galaxy high-stress tail (canonical:
$P_{hi}=99.9$, $\varepsilon_{gal}=10^{-6}$, $p=4$, $k_2=1$, $S_c=10 S_{hi}$, $k_4=k_2/S_c^2$).
A representative calibration printout is:
`S_hi=1210.02`, `Sc=12100.2`, `S0=4.67634e+07`, `k4=6.82991e-09`, `gate(S_hi)=1e-06`.

### 7.4 Results (single-fit, CV, ablations)
- **Full-dataset single-fit:** $\chi^2_{base}=945.842938$, $\chi^2_{best}=180.520348$ at $A=0.177827941$, $\alpha=0.001$, giving $\Delta\chi^2=765.322589$.
- **Cross-validation (seed-robust):** 5-fold CV repeated over 3 seeds (15 folds) yields pooled test $\Delta\chi^2 = 153.1\pm 30.0$ (median 147.7, range [114.5, 226.4]) with stable best-grid modes ($A\approx 0.1778$, $\alpha=0.001$).
- **Ablation (`thread` vs `none`):** with galaxy-closed autocalibration, `env_model thread` and `env_model none` yield indistinguishable CV outcomes, confirming the UV completion decouples at galaxy scale and the DM/RAR improvement is driven by the GEO modulation itself.

**Caution on “σ” language.**
Large $\Delta\chi^2$ improvements are suggestive, but mapping them to “σ significance” requires additional assumptions (nested likelihood, effective degrees-of-freedom, correct noise model). We report $\Delta\chi^2$ directly.

#### 7.4.1 Locked prereg verdict (scan-free rerun; fixed $A,\alpha$; seed=2026)

To remove the common ambiguity between a mere script-success and a true performance verdict, we define a **scan-free** prereg check for the DM/SPARC track:

- **Fixed parameters (frozen):** $A=0.1778279410$, $\alpha=0.001$ (chosen from the stable mode seen across prior CV seeds, then frozen).
- **Holdout protocol:** 5-fold CV with `seed=2026`.
- **Verdict rule:** **performance pass** iff *all* folds satisfy $\Delta\chi^2_{\mathrm{test}}>0$, where  
$$
  \Delta\chi^2_{\mathrm{test}}\equiv \chi^2_{\mathrm{base},test}-\chi^2_{\mathrm{geo},test}.
$$

- **Auxiliary-DOF ablation (informational, not required for the performance verdict):** run both `env_model thread` (STIFF+GATE galaxy-closed) and `env_model none`. If they match, the UV completion is effectively decoupled at galaxy scale and the improvement is driven by the GEO modulation itself.

**Rapora / jüri diline tek satır DM verdict (copy-paste)**

DM (SPARC/RAR) — performance pass (scan-free): Fixed A=0.1778279410, α=0.001, kfold=5, seed=2026; all folds have Δχ²_test > 0. Thread/STIFFGATE decoupled in galaxy regime (gate@S_hi≈1e−6) and gives identical Δχ² as env_model=none → DM pass does not rely on auxiliary DOF.

**Locked run commands (no scan)**

*Project note.* Next, without touching DM, lock the **EM closing verdict** with the same discipline: single prereg run + explicit verdict threshold.

### 7.5 Systematics and robustness checklist (DM track)
Completed in this note:

- [x] k-fold CV with multiple seeds (15 folds total)
- [x] explicit ablation: `env_model thread` (galaxy-closed) vs `env_model none`
- [x] best-grid stability check (same $(A,\alpha)$ modes across seeds)

Recommended next checks before “final” publication:

- [ ] leave-one-galaxy-out CV (galaxy-level splits rather than point-level shuffles)
- [ ] “one galaxy, one vote” weighting to reduce dominance of dense galaxies
- [ ] alternate noise models: intrinsic scatter term; robust losses (Huber/Tukey)
- [ ] baryonic systematics: $\Upsilon_{disk/bulge}$, distance, inclination perturbations
- [ ] grid refinement stability (increase $n_A, n_\alpha$; verify mode persistence)
- [ ] compare against a standard RAR fitting form baseline (AIC/BIC-style)

### 7.6 Parameter definitions and CLI mapping (Dark matter / RAR)

This maps the DM-sector parameters and scan knobs to their CLI flags (Section 8.6).

| Paper symbol / name | Definition + purpose | Units | CLI flag (Section 8.6 example) |
|---|---|---|---|
| model | Choice of phenomenological model family (e.g., additive constant in the GEO term). | - | `--model geo_add_const` |
| g0 | Characteristic acceleration scale used by the RAR/RAR-like baseline. | m/s^2 | `--g0 1.2e-10` |
| g_bp | Bubble–plane coupling weight used in some engineering/phenomenology studies (not required for prereg sector verdicts). | - | (varies; often 0) |
| g_lp | Lock‑plane coupling weight used in some engineering/phenomenology studies (not required for prereg sector verdicts). | - | (varies; often 0) |
| env_model | Environment model family used to scale the GEO term (thread vs none). | - | `--env_model thread` |
| thread_S0 | Overall thread-field normalization (sets environment strength). | implementation-defined | `--thread_S0 1e6` |
| thread_gate_p | Gate exponent controlling saturation/turn-on sharpness. | dimensionless | `--thread_gate_p 4` |
| thread_k2, thread_k4 | Shape parameters controlling the thread response curve. | dimensionless | `--thread_k2 1.0 --thread_k4 10.0` |
| A | GEO amplitude: strength of plane‑stress response producing $\Delta g_{\mathrm{geo}}$. | dimensionless | `--A_min ... --A_max ... --nA ...` |
| alpha | GEO scale/shape: controls transition sharpness in $\Delta g_{\mathrm{geo}}(g_{\mathrm{bar}})$. | dimensionless | `--alpha_min ... --alpha_max ... --nAlpha ...` |
| points_csv | SPARC/RAR points table used for the DM likelihood. | - | `--points_csv .\\data\\sparc\\sparc_points.csv` |

## 7.A Engineering glossary (program terms from the logs; what is used here vs. what is planned)

This draft intentionally separates **(i) what is required for the preregistered sector tests reported here** from **(ii) additional engineering mechanisms** explored in the broader program. The items below are included to prevent “missing-mechanism” confusion when reading the `` history.

### 7.A.1 Topology and substrate terms

- **RT junction mesh (4×4=16)**: the complete corner-to-corner connectivity across a face contact between two cubes. **Used conceptually here** (Sec. 2.2 / 2.5) and in kernel design.

- **CT spokes (8)**: constant-tension bubble→corner links. **Used conceptually here** (Sec. 2.5) as the minimal way to couple a “reservoir” (bubble) into boundary transport.

- **Edge-frame threads (12 edges)** and **internal diagonals**: mechanistic constitutive choices for rigidity and bulk mixing. **Not required** for the reported sector fits; appear in mechanistic simulations in the codebase.

- **Bubble–corner repulsion**: a short-range conservative term preventing bubble collapse into corners (repulsion within $R_{\mathrm{rep}}$). **Included as an optional mechanistic term** (Sec. 2.5.4) for stability/localization intuition.

### 7.A.2 Auxiliary-layer (“gauge plane”) terms

- **Auxiliary field / extra DOF layer (“gauge plane”)**: a bookkeeping layer hosting phase/gate variables beyond ordinary displacement. **Central concept** in this draft (Sec. 1.2).

- **Global lock / reference plane**: the idea that a shared reference manifold plus ordered updates can yield emergent “time”. **Conceptual in this draft**; represented by ordered updates and gating, not a standalone operator module.

- **TT2 plane**: two-component transverse-traceless basis used in GW readout ($+/\times$). **Used in the GW module**, summarized here (Sec. 6).

### 7.A.3 Kernel dynamics terms

- **Holonomy / `du_phase`**: a way to convert an ordered complex profile $u(s)$ into a phase summary $\delta_{\mathrm{geo}}$. **Used** as the universal compression step (Sec. 2.2.3).

- **Phase-match / thread gate**: smooth windowing that suppresses incoherent transport as phase mismatch grows. **Used in spirit** (gate functions appear across sectors), and is the natural place where conditioning issues surface in EM.

- **Breathing mode / shared mode memory**: damped shared-mode terms explored as finite-time “memory” after disentanglement. **Not required** for the results in this draft; part of the broader research thread.

### 7.A.4 Implementation-status honesty

- The preregistered sector claims in this draft depend only on the **kernel summary** plus explicit bridge operators and likelihoods.
- Several deeper mechanistic ideas (full localization operator on a lock plane; fully coupled edge/bulk transport; complete derivations of $A_R$ vs $A_I$ from micro-transport) are **active research items** and are not asserted as “proven” here.

## 7.B Global parameter glossary + mechanism map (code-faithful; cross-sector)

This section is a *single source of truth* for the “letters” that appear throughout the paper **and** in the command-line logs. 
It is written to prevent the most common referee objection: “these parameters look like arbitrary fit knobs.”

**Discipline:** unless explicitly stated otherwise, every parameter below is treated as **pre-registered / fixed-choice** in the falsification runs (no scans, no “best-of” selection).

### 7.B.1 Disambiguations (avoid symbol collisions)

- **$ \kappa_{\mathrm{junc}} $**: junction stiffness / EM forward regulator (a physical penalty on misaligned or out-of-order face handshakes). 
- **$ \kappa_{\mathrm{gate}} $**: routing / phase‑match gate (a *consistency switch* controlling which transport components contribute). 
- **$ \kappa_{\mathrm{back}} $**: GW backreaction stiffness (controls how strongly the lattice reacts back onto the driver; appears in ringdown-only runs). 
- **$ \kappa_C \equiv {\mathrm{cond}}(C) $**: **covariance condition number** (purely statistical; not a physics parameter).
- **$ \alpha_{\mathrm{map}} $**: mapping scale in the EM/strong “log driver”. It is **not** the QED fine‑structure constant.
- The 16‑port index is written as **$p\in\{1,\dots,16\}$** (do *not* reuse $\alpha$ for a port label).

### 7.B.2 Mechanism map (where each force “lives”)

| Sector / effect | Address in CurvedCube | Primary operator | Typical observables |
|---|---|---|---|
| **Weak** | **Edge threads** (intra‑cube skeleton) | oriented holonomy / $\delta_{\mathrm{geo}}$ | $\nu$ appearance/disappearance spectra, $\delta_{\mathrm{CP}}$ proxy |
| **Strong** | **Bulk threads** (intra‑cube interior) | edge–bulk desynchronization $\Delta t$ → complex response | $\sigma_{\mathrm{tot}}(s)$, elastic forward amplitude $A_R+iA_I$ |
| **EM** | **Junctions** (inter‑cube face mesh) | junction filter $J(\tau;\kappa_{\mathrm{junc}})$ + env driver | Bhabha $d\sigma/dt$, forward regularization |
| **Gravity / GW** | **Inter‑cube RT strain** (distance‑dependent tension) | TT projection + backreaction | ringdown templates, detector $h_+,h_\times$ |
| **DM (SPARC/RAR)** | **Global lock-plane stress** (cumulative) | effective metric modulation $g_{\mathrm{eff}}$ | rotation curves, RAR residuals |

### 7.B.3 “Kernel knobs” (shared geometric layer)

| CLI | Symbol | Meaning (mechanism; code-faithful) | Units / conventions | Used in |
|---|---:|---|---:|---|
| `--A` | $A$ | Overall amplitude of the geometric auxiliary response (enters the transport profile/bridge as a multiplicative scale). | dimensionless | weak/strong/EM (and sometimes GW toy drives) |
| `--k_rt` | $k_{\mathrm{rt}}$ | Route-time discretization / number of phase samples for the transport loop (engineering knob; **not** a physics scale by itself). | integer | weak holonomy / du_phase |
| `--phi` | $\phi$ | Internal twist / chirality angle of bulk relative to edge frame (CP‑odd slot; also sets quadrature of the drive). | rad | weak + strong + EM |
| `--zeta` | $\zeta$ | Topological friction / damping rate on the transport response; in the weak/GW usage it controls phase-memory loss. (Interpretation as “effective geometric temperature” is discussed in §9.) | dimensionless | weak + GW + EM saturation laws |
| `--decoh_zeta` | $\zeta_{\mathrm{decoh}}$ | **Separate** decoherence knob applied in the Lindblad/dephasing map; should not contaminate the $A=0$ SM limit. | dimensionless | weak (density-matrix) |
| `--geo_phase_mode` | — | Which phase functional is used: `integral` (path integral) vs `endpoint` (end-point phase). | enum | weak/holonomy |
| `--geo_mode` / `--geo_dcp_mode` | — | Geometric summary functional: e.g. `du_phase` holonomy proxy. | enum | weak (predict $\delta_{\mathrm{CP}}^{\mathrm{geo}}$) |
| `--template` | — | Transport template family (e.g. `cos`); defines $u(s)$ basis used to compute $|c_1|$, $\delta_{\mathrm{geo}}$. | enum | weak/strong/EM |
| `--kernel` | — | Selects the transport kernel implementation (e.g. `rt` route‑time kernel used in CurvedCube runs). | enum | weak/strong/EM |
| `--geo_action` | — | Selects which geometric action operator is applied (e.g. mech/fullphys variants in the codebase). | enum | weak/strong/EM |

### 7.B.4 Weak-sector propagation knobs (density-matrix unified equation)

| CLI | Symbol | Meaning | Units | Notes |
|---|---:|---|---:|---|
| `--L0_km` | $L_0$ | Geometric baseline scale used by `omega_from_geometry` to set $\omega_{\mathrm{geom}}$. | km | Logs show both $\omega=\pi/L_0$ and $\omega=2\pi/L_0$ conventions; **must be preregistered**. |
| `--omega0_geom` | $\omega_{\mathrm{geom}}$ | Geometry-derived angular wavenumber used by the transport drive. | 1/km | Derived from $L_0$; see note above. |
| `--omega` | $\omega$ | Override for $\omega_{\mathrm{geom}}$ when `omega0_geom=free`. | 1/km | `free` is allowed only in prereg plans. |
| `--rho` | $\rho$ | Matter density used for MSW potential. | g/cm³ | weak only |
| `--Ye` | $Y_e$ | Electron fraction used for MSW potential. | dimensionless | weak only |
| `--ordering` | — | Mass ordering (`NO`/`IO`). | enum | weak only |
| `--kappa_gate` | $\kappa_{\mathrm{gate}}$ | Phase-match / routing gate (switch or soft weight). | dimensionless | weak; also appears in geometry debugging |

**SM neutrino inputs (held fixed in falsification runs):** mixing angles and mass splittings (e.g. $ \sin^2\theta_{13},\sin^2\theta_{23},\Delta m^2 $) are treated as external Standard-Model inputs. 
Some utilities in the logs use CLI spellings like `--s2th23/--dm2/--dcp` (or legacy `--sin2_theta23/--dm2_32`), but these are **not** CurvedCube parameters and should not be scanned in this program.

**Derived weak summaries (not CLI knobs):**

- $u(s)$: transport profile along the baseline (kernel output). 
- $c_1$: complex first harmonic coefficient of $u(s)$ under the chosen template/basis. A concrete definition used by the “cos template” family is
$$
 c_1 \equiv \frac{1}{L}\int_0^{L} u(s)\,e^{-i\omega s}\,ds,
$$
 with $|c_1|$ used as a stability/strength diagnostic (implementation follows the code’s discrete sum).

- $\delta_{\mathrm{geo}}$ / $\delta_{\mathrm{CP}}^{\mathrm{geo}}$: oriented holonomy phase proxy computed from $u(s)$ (the “prediction” object in scan‑free runs).

### 7.B.5 Strong/EM “environment scaling” (the clock; not an energy label)

The logs use `env_mode` / `env_scale` to produce the observed $ \log(s) $ or eikonal-like buildup **without claiming the cube “knows the beam energy.”** 
Interpretation used here: **interaction frequency** with the global lock reference (“clock ticks”) sets an effective strength of repeated junction interrogation.

| CLI | Symbol | Meaning | Used in |
|---|---:|---|---|
| `--env_mode` | — | Environment driver type: `none`, `log`, `eikonal`, … | strong + EM |
| `--env_scale` | ${\mathrm{env}\_scale}$ | Strength factor multiplying the geometric response; interpreted as “effective interrogation count.” | strong + EM |

### 7.B.6 EM/Strong bridge-shaping knobs (when present)

These appear in the EM bridge (and in some strong-energy scans), controlling how the kernel output is mapped into a multiplicative deformation.

| CLI | Symbol | Meaning (code-faithful) | Notes |
|---|---:|---|---|
| `--alpha` | $\alpha_{\mathrm{map}}$ | Log-response scale used inside the driver $f=\alpha_{\mathrm{map}}\ln(\cdot)$. | Not QED $\alpha$. |
| `--n` | $n$ | Power-law exponent used when the driver includes $(E/E_0)^n$-type scaling. | Must be fixed prereg. |
| `--E0` | $E_0$ | Reference energy for power-law scaling. | Same units as $E$. |
| `--R_max` | $R_{\max}$ | Saturation cap for a response map $R=R_{\max}(1-e^{-\zeta|f|})$. | dimensionless |
| `--kappa_junc` | $\kappa_{\mathrm{junc}}$ | Junction stiffness in the junction filter $J(\tau;\kappa_{\mathrm{junc}})$. | EM forward regulator. |
| `--center_mode` | — | Centering / anchoring mode for the EM deformation: e.g. `pivot_cos` (recommended) vs legacy mean-subtraction. | enum | Forbids “DC wins”. |
| `--cos_pivot` | $x_{\mathrm{pivot}}$ | Pivot anchor point for centering (used: $x_{\mathrm{pivot}}=0.72$, mid/forward boundary). | dimensionless | EM prereg anchor. |
| `--shape_only` | — | Legacy group-mean subtraction anchor. **Do not combine** with `center_mode=pivot_cos` (can reintroduce mid/forward sign tension). | switch | EM legacy. |
| `--group_mode` | — | Grouping protocol for shared nuisance $\beta_g$ (e.g. `block` = per-energy block). | enum | EM. |
| `--beta_nonneg` | — | Enforce $\beta_g\ge 0$ to prevent unphysical group normalizations. | switch | EM. |
| `--freeze_betas` | — | Freeze $\beta_g$ from train when evaluating holdouts (prevents renormalization leakage). | switch | EM prereg holdouts. |
| `--baseline_group_col` | — | Column name (e.g. `group_id`) linking baseline bins to energy blocks. | string | EM baseline import. |
| `--geo_structure` | $s_{\mathrm{struct}}$ | Structure sign/type (e.g. diag/offdiag). | Engineering switch. |
| `--geo_gen` | $g_{\mathrm{gen}}$ | Generator scalar (lam1..lam4). | Engineering switch. |

### 7.B.7 Optional “breath/thread” dynamic modules (weak-sector extensions)

When the code is run with explicit breathing or thread relaxation channels, the following knobs appear. 
They are treated as **extensions** and must be preregistered to avoid parameter fishing.

| CLI | Symbol | Meaning | Used in |
|---|---:|---|---|
| `--breath_B` | $B_{\mathrm{breath}}$ | Amplitude of bubble “breathing” mode. | weak extensions |
| `--breath_w0` | $\omega_{\mathrm{breath}}$ | Frequency of breathing mode (often tied to $\omega_{\mathrm{geom}}$). | weak extensions |
| `--breath_gamma` | $\gamma_{\mathrm{breath}}$ | Damping of breathing mode. | weak extensions |
| `--thread_C` | $C_{\mathrm{thread}}$ | Amplitude of thread relaxation mode. | weak extensions |
| `--thread_w0` | $\omega_{\mathrm{thread}}$ | Frequency of thread relaxation mode. | weak extensions |
| `--thread_gamma` | $\gamma_{\mathrm{thread}}$ | Damping of thread relaxation mode. | weak extensions |
| `--thread_weight_app/dis` | — | Channel weights for appearance/disappearance mapping. | weak extensions |

### 7.B.8 GW ringdown-only knobs (detector + backreaction)

| CLI | Symbol | Meaning | Units |
|---|---:|---|---:|
| `--det_rot_deg` | $\theta_{\mathrm{det}}$ | Readout basis rotation (diagnostic): mixes $+/\times$ as in a 2$\theta$ polarization rotation; used to test whether “cross” is genuinely absent or only a projection artifact. | deg |
| `--time_scales` | — | Discrete time-scale hypotheses for ringdown response (preregistered grid). | s |
| `--max_model_lag_s` | — | Maximum allowed lag between template and data (preregistered; no scanning beyond). | s |
| `--center_guess_gps` | — | Initial GPS-time center guess for alignment (analysis parameter; preregistered). | s |
| `--offsource_n` | — | Number of off-source windows for background / null calibration. | — |
| `--source_mode` | — | Dataset/event selection mode (analysis parameter). | enum |
| `--analysis_band` / `--anchor_band` | — | Frequency window used for fit/anchor normalization. | Hz |
| `--drive_gain` | $g_{\mathrm{drive}}$ | Forced‑phase drive amplitude (Phase‑A). For ringdown comparison, analysis uses Phase‑B (drive OFF) so $g_{\mathrm{drive}}$ is not a fit knob. | — |
| *(various)* | $\kappa_{\mathrm{back}}$ | Backreaction stiffness (GW gating runs): strength of lattice→plane feedback that modulates RT crossings; $\kappa_{\mathrm{back}}=0$ disables feedback (pure drive), larger values enforce stronger plane‑locked response. | — |

### 7.B.9 Auxiliary gauge-plane / extra-DOF layer (GW gating runs)

Some GW configurations enable an auxiliary DOF layer (“gauge plane”) with its own PDE-like relaxation:

| CLI | Symbol | Meaning | Notes |
|---|---:|---|---|
| `--enable_gauge_plane` | — | Enables the auxiliary DOF layer. | switch |
| `--plane_axis` / `--plane_cz` / `--plane_mode` | — | Orientation and mode selection for the auxiliary layer. | enum/ints |
| `--c_phi` | $c_\phi$ | Coupling coefficient of the auxiliary phase field. | dimensionless |
| `--gamma_phi` | $\gamma_\phi$ | Damping of the auxiliary phase field. | dimensionless |
| `--kappa_shear` | $\kappa_{\mathrm{shear}}$ | Shear stiffness in the auxiliary layer PDE. | dimensionless |
| `--gate_threshold` | — | Gate threshold for hard/soft opening. | dimensionless |

## 8. Performance run commands (current)

**Project root (workdir):** `C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git`  
**Rule:** The word **pass** is used **only** for **performance**.

---

#### Summary (performance-only)

- **WEAK:** **performance pass**
- **STRONG:** **performance pass** *(rho tension exists, but net improvement is positive)*
- **EM:** **not a performance pass** *(closure ok; Delta chi2 = 0 in both branches)*
- **DM:** **performance pass**
- **MS:** **performance pass** *(internal_only strict run and full ablation both passed)*
- **LIGO:** **performance pass** *(canonical exact branch; locally re-confirmed at OFF20K exact; OFF100K is optional stronger rerun)*

---

#### Global criteria used (performance)

- **WEAK:** `TOTAL SCORE > 0`
- **STRONG:** net `Delta chi2 total > 0` (sigma_tot + rho combined)
- **DM:** `telemetry.all_folds_delta_test_positive = true` (k-fold test improvement)
- **MS:** prereg final verdict `PASS` (performance) and dynamics stateful integrity true
- **LIGO:** canonical exact GW170814 branch has strong null p-metrics (key: `p_joint_abs_and_minabs`)

---

### 1) WEAK — performance

#### Why performance pass
Observed in-session:
- `TOTAL SCORE = 0.489377` (positive)

#### Run command
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

py -3 .\score_nova_minos_t2k_penalty.py `
  --runner .\nova_mastereq_forward_kernel_BREATH_THREAD_v2.py `
  --pack_nova .\nova_channels.json `
  --pack_minos .\minos_channels.json `
  --runner_args "--kernel rt --k_rt 180 --A -0.002 --alpha 0.7 --n 0 --E0 1 --omega0_geom fixed --phi 1.57079632679 --zeta 0.05 --rho 2.6 --kappa_gate 0 --T0 1 --mu 0 --eta 0 --breath_B 0.3 --breath_w0 0.0038785 --breath_gamma 0.2 --thread_C 1.5 --thread_w0 -1 --thread_gamma 0.1 --thread_weight_app 0 --thread_weight_dis 1" `
  --t2k_penalty_cli .\t2k_penalty_cli.py `
  --t2k_profiles .\t2k_release_extract\t2k_frequentist_profiles.json `
  --hierarchy NH `
  --rc wRC `
  --s2th23 0.55 `
  --dm2 0.0025 `
  --dcp -1.5
```

---

### 2) STRONG — performance

#### Why performance pass
In-session verified:
- sigma_tot: `pp dchi2 = +3.235630`, `pbarp dchi2 = +0.209162`
- rho: `dchi2 = -0.6558912131`
- **Net:** `Delta chi2 total = +2.7889007869` (positive)

#### Run commands
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git
New-Item -ItemType Directory -Force .\LOCAL_RUNS\STRONG | Out-Null

# sigma_tot NULL
py -3 .\strong_sigma_tot_energy_scan_v2.py `
  --data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --channel both `
  --A 0 `
  --env_mode none `
  --out .\LOCAL_RUNS\STRONG\sigmatot_NULL.csv `
  --chi2_out .\LOCAL_RUNS\STRONG\sigmatot_NULL_chi2.json

# sigma_tot GEO
py -3 .\strong_sigma_tot_energy_scan_v2.py `
  --data .\data\hepdata\pdg_sigma_tot_clean_for_runner.csv `
  --channel both `
  --A -0.003 `
  --env_mode eikonal `
  --template cos `
  --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 `
  --c1_abs 0.725147 `
  --out .\LOCAL_RUNS\STRONG\sigmatot_GEO_Aneg003.csv `
  --chi2_out .\LOCAL_RUNS\STRONG\sigmatot_GEO_Aneg003_chi2.json

# rho NULL
py -3 .\strong_rho_energy_scan_v3.py `
  --data .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --channel both `
  --A 0 `
  --env_mode none `
  --out .\LOCAL_RUNS\STRONG\rho_NULL.csv `
  --chi2_out .\LOCAL_RUNS\STRONG\rho_NULL_chi2.json

# rho GEO
py -3 .\strong_rho_energy_scan_v3.py `
  --data .\data\hepdata\pdg_rho_clean_for_runner.csv `
  --channel both `
  --A -0.003 `
  --env_mode eikonal_amp `
  --sqrts_ref_GeV 13000 `
  --delta_geo_ref -1.315523 `
  --c1_abs 0.725147 `
  --template cos `
  --out .\LOCAL_RUNS\STRONG\rho_GEO_Aneg003.csv `
  --chi2_out .\LOCAL_RUNS\STRONG\rho_GEO_Aneg003_chi2.json
```

---

### 3) EM — not a performance pass (closure ok)

#### Why not a performance pass
Both branches have `Delta chi2 = 0`:
- Bhabha: `chi2_SM == chi2_GEO`
- MuMu: `chi2_SM == chi2_GEO`

#### Run commands (for record)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git
New-Item -ItemType Directory -Force .\LOCAL_RUNS\EM | Out-Null

# Bhabha
py -3 .\em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py `
  --pack .\data\hepdata\lep_bhabha_pack.json `
  --cov total `
  --A 0 `
  --out .\LOCAL_RUNS\EM\bhabha_pred.csv `
  --out_json .\LOCAL_RUNS\EM\bhabha_summary.json

# MuMu
py -3 .\em_mumu_forward_shapeonly_env_guarded_freezebetas_groupaware.py `
  --pack .\data\hepdata\lep_mumu_pack.json `
  --cov total `
  --A 0 `
  --out .\LOCAL_RUNS\EM\mumu_pred.csv `
  --out_json .\LOCAL_RUNS\EM\mumu_summary.json
```

---

### 4) DM — performance

#### Precondition (bundle fix already done)
`thread_env_model.py` must exist at the project root.

#### Why performance pass
Rerun produces `dm_cv_thread_STIFFGATE_summary.json` with:
- `telemetry.all_folds_delta_test_positive = true`

#### Run command
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git
New-Item -ItemType Directory -Force .\LOCAL_RUNS\DM | Out-Null

py -3 .\run_dm_paper_run.py `
  --out_dir .\LOCAL_RUNS\DM\dm_paper_pass_A01778_a0001 `
  --points_csv .\data\sparc\sparc_points.csv `
  --kfold 5 `
  --seed 2026 `
  --A 0.1778279410 `
  --alpha 0.001
```

---

### 5) MS — performance

#### A) internal_only strict run — performance pass

##### Why performance pass
Final prereg file shows:
- `final_verdict = "PASS"` (performance)
- `C1_psuccess = true`
- `C2_mad = true`
- `C3_thirdarm = true`

Aggregator shows:
- `prereg_all_pass = true`
- `dynamics_stateful_all = true`

##### Run commands (internal_only; validated)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

$runId = "ms_strict_raw_common_local"

New-Item -ItemType Directory -Force ".\out\MS\$runId\internal_only\A1_B2" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\internal_only\A1_B3_holdout" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\internal_only\A2_B3_thirdarm" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\internal_only\final" | Out-Null

# A1_B2
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2\ModeB_points.csv `
  --out_dir ".\out\MS\$runId\internal_only\A1_B2" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation internal_only `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# A1_B3_holdout
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --out_dir ".\out\MS\$runId\internal_only\A1_B3_holdout" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation internal_only `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# A2_B3_thirdarm
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A2_B3\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --out_dir ".\out\MS\$runId\internal_only\A2_B3_thirdarm" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation internal_only `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# Finalizer
py -3 .\runners\finalize_particle_specific_goodppm_lock_from_runs_v1_0.py `
  --root . `
  --pair_b2_dir ".\out\MS\$runId\internal_only\A1_B2" `
  --pair_b3_dir ".\out\MS\$runId\internal_only\A1_B3_holdout" `
  --third_arm_dir ".\out\MS\$runId\internal_only\A2_B3_thirdarm" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --out_dir ".\out\MS\$runId\internal_only\final" `
  --good_ppm 3 `
  --window_ppm 30 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --mode_a_points .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv `
  --mode_b2_points .\data\MS\particle_specific_cytofull_A1_B2\ModeB_points.csv `
  --mode_b3_points .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --mode_a2_points .\data\MS\particle_specific_cytofull_A2_B3\ModeA_points.csv

# Aggregator
py -3 .\ms_dynamics_integrity_aggregate_v1_DROPIN.py --run_id $runId
```

#### B) full ablation — performance pass

##### Why performance pass
In-session validated:

###### Final prereg
- `final_verdict = "PASS"` (performance)
- `C1_psuccess = true`
- `C2_mad = true`
- `C3_thirdarm = true`

###### Aggregator
- `prereg_all_pass = true`
- `dynamics_stateful_all = true`

###### Telemetry
Across all three full arms:
- `ablation = "full"`
- `internal_dynamics_used = true`
- `thread_env_used = true`
- `stateful_steps_total = 527`

This confirms that the full branch passed with thread environment enabled.

##### Run commands (full; validated)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

$runId = "ms_strict_raw_common_full_local"

New-Item -ItemType Directory -Force ".\out\MS\$runId\full\A1_B2" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\full\A1_B3_holdout" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\full\A2_B3_thirdarm" | Out-Null
New-Item -ItemType Directory -Force ".\out\MS\$runId\full\final" | Out-Null

# A1_B2
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2\ModeB_points.csv `
  --out_dir ".\out\MS\$runId\full\A1_B2" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation full `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# A1_B3_holdout
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --out_dir ".\out\MS\$runId\full\A1_B3_holdout" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation full `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# A2_B3_thirdarm
py -3 .\ms_particle_specific_dynamic_runner_v1_0_DROPIN.py `
  --inputs .\data\MS\particle_specific_cytofull_A2_B3\ModeA_points.csv .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --out_dir ".\out\MS\$runId\full\A2_B3_thirdarm" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --baseline ModeA_points `
  --ablation full `
  --alpha 0.30 `
  --alpha_g_floor 0.25 `
  --window_ppm 30 `
  --good_ppm 3 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --prereg_observable raw_ppm `
  --drift_state_mode telemetry_only_commonbaseline `
  --require_stateful_dynamics

# Finalizer
py -3 .\runners\finalize_particle_specific_goodppm_lock_from_runs_v1_0.py `
  --root . `
  --pair_b2_dir ".\out\MS\$runId\full\A1_B2" `
  --pair_b3_dir ".\out\MS\$runId\full\A1_B3_holdout" `
  --third_arm_dir ".\out\MS\$runId\full\A2_B3_thirdarm" `
  --targets_csv .\data\MS\particle_specific_cytofull_A1_B2_direct\targets_used.csv `
  --out_dir ".\out\MS\$runId\full\final" `
  --good_ppm 3 `
  --window_ppm 30 `
  --tail3_ppm -300000 `
  --min_n 8 `
  --max_bins 8 `
  --mode_a_points .\data\MS\particle_specific_cytofull_A1_B2\ModeA_points.csv `
  --mode_b2_points .\data\MS\particle_specific_cytofull_A1_B2\ModeB_points.csv `
  --mode_b3_points .\data\MS\particle_specific_cytofull_A1_B2_direct\ModeB_holdout_points.csv `
  --mode_a2_points .\data\MS\particle_specific_cytofull_A2_B3\ModeA_points.csv

# Aggregator
py -3 .\ms_dynamics_integrity_aggregate_v1_DROPIN.py --run_id $runId
```

---

### 6) LIGO — performance (canonical exact branch)

#### Why performance pass (locally re-confirmed)
Exact OFF20K rerun produced:
- `p_joint_abs_and_minabs = 0.0`
- `p_abs_corr = 0.0295`
- `p_min_abs_corr = 0.0435`

#### Canonical exact OFF20K run command (validated)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

py -3 .\gw170814_ringdown_only_null_v1_FIXED_v7_consistency_3det_projected_peakalign_v6_fixedlags.py `
  --h1_hdf5 ".\data\gw\H-H1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --l1_hdf5 ".\data\gw\L-L1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --v1_hdf5 ".\data\gw\V-V1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --model_csv ".\out\LIGO\MODEL_BASIS_HYBRID_lam1e+09.csv" `
  --model_col_plus h_plus_proxy `
  --model_col_cross h_cross_proxy `
  --model_t0peak_col h_plus_proxy `
  --auto_event gw170814 `
  --center_guess_gps 1186741861.0 `
  --anchor_band 150,500 `
  --analysis_band 150,500 `
  --fixed_anchor_lag_s -0.008 `
  --fixed_anchor_lag_h1_v1_s 0.006 `
  --max_model_lag_s 0.0 `
  --ringdown_start_s 0.002 `
  --ringdown_dur_s 0.02 `
  --time_scales 1 `
  --psi_deg 45 `
  --seed 777 `
  --offsource_n 20000 `
  --no_sign_flip `
  --out_prefix ".\out\LIGO\gw170814_HYB_lam1e9_psi45_OFF20K_seed777_EXACT"
```

#### Optional: canonical exact OFF100K (stronger, slower)
```powershell
Set-Location C:\Dropbox\projects\new_master_equation_with_gauga_structure_test_git

py -3 .\gw170814_ringdown_only_null_v1_FIXED_v7_consistency_3det_projected_peakalign_v6_fixedlags.py `
  --h1_hdf5 ".\data\gw\H-H1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --l1_hdf5 ".\data\gw\L-L1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --v1_hdf5 ".\data\gw\V-V1_GWOSC_4KHZ_R1-1186741846-32.hdf5" `
  --model_csv ".\out\LIGO\MODEL_BASIS_HYBRID_lam1e+09.csv" `
  --model_col_plus h_plus_proxy `
  --model_col_cross h_cross_proxy `
  --model_t0peak_col h_plus_proxy `
  --auto_event gw170814 `
  --center_guess_gps 1186741861.0 `
  --anchor_band 150,500 `
  --analysis_band 150,500 `
  --fixed_anchor_lag_s -0.008 `
  --fixed_anchor_lag_h1_v1_s 0.006 `
  --max_model_lag_s 0.0 `
  --ringdown_start_s 0.002 `
  --ringdown_dur_s 0.02 `
  --time_scales 1 `
  --psi_deg 45 `
  --seed 777 `
  --offsource_n 100000 `
  --no_sign_flip `
  --out_prefix ".\out\LIGO\gw170814_HYB_lam1e9_psi45_OFF100K_seed777_EXACT"
```

## 9. Theoretical implications and philosophy: Topological Field Theory framing (future-work, topology-first)

> **Scope note:** This section is an interpretive / future-work framing. No explicit gauge group, fiber-bundle construction, or holonomy derivation is claimed in this version.

This framework is best read as a **topology-first field theory**: 
local physics is controlled by **connectivity, ordering, and transport holonomy** on an amorphous lattice, while metric-like effects appear through **inter‑cube distance-dependent tension**. 
**It is explicitly *not* an infinite self‑similar nesting model** (no infinite self‑similar nesting is assumed or required).

### 9.1 Topological universality across scales (micro ↔ macro)

The same unified-equation + bridge formalism applies across scales **because the substrate rules are topological**, not because the geometry repeats. 
Two limiting readings are used throughout the project:

**Weak (edge-addressed / holonomy-dominant):** long-baseline propagation is routed primarily along *Edge Threads*; the leading observable is an oriented-loop phase (holonomy) rather than bulk absorption. Operationally, this is why the weak sector modifies **phase** with minimal impact on amplitude compared to the bulk-addressed strong channel.

- **Micro (proton / QCD‑like regime)**: localized *knot / resonance* of transport and bulk tensioning within a small number of unit cells (bulk‑addressed; strong sector).
- **Macro (galaxy / DM‑like regime)**: collective, long‑range elastic deformation and lock‑plane stress integrated over very many junctions (RT‑addressed; gravity/DM).

### 9.2 Cosmological origin (physical origin mechanism; fixed substrate postulate)

- the lattice is amorphous (not crystalline),
- junction ordering can exist (non‑commutative composition),
- and scars/seams (thread classes) can be long‑lived.

This formation is the **direct physical cause** of (i) edge–bulk desynchronization (Jittering) and hence the complex response $A=A_R+iA_I$ in the strong sector, and (ii) ordered‑junction filtering with finite stiffness in the EM bridge.

We treat the early-universe **fusion / amorphization** statement as a **fixed substrate postulate** (a physical origin mechanism), not a tunable fit input. Its role is to justify **two concrete, testable local operators** used throughout this work: (i) *edge–bulk transport dispersion* on an amorphous manifold, which produces a receiver timing mismatch $\Delta t$ and hence a complex response $e^{-\Gamma\Delta t}e^{i\Omega\Delta t}$ (the operational source of $A_R$ / $A_I$ in the strong sector), and (ii) *ordered junction assembly with finite stiffness* $\kappa_{\mathrm{junc}}$, which filters non-causal / out-of-order configurations in the EM bridge. Thus the “origin” paragraph is not decorative: it is a **mechanistic rationale** for why these operators exist. We remain explicit that no cosmological parameter is scanned or fitted here; falsification is via sector observables under preregistered protocols.

No cosmological parameter from this postulate appears in any likelihood or scan; **only its local operator consequences are tested** against preregistered sector observables.

### 9.3 Dual‑tension mechanism (gravity vs gauge separation)

A key postulate is the **tension bifurcation**:

- **Inter‑cube (RT / external)**: tension adapts with distance → encodes metric/strain (gravity/GW channel).
- **Intra‑cube (edge + bulk internal)**: tension is invariant/quantized → preserves local gauge behavior against stretching.

This is the model’s mechanical answer to: “why do bound states not tear apart inside a gravitational potential?”

### 9.4 Thermodynamics of geometry (what $\zeta$ *means*, without overclaiming)

In the code, $\zeta$ is a **damping / phase‑memory loss rate**. 
A stronger interpretation (“geometric temperature”) is optional and should be read as:

- $\zeta$ behaves like an **effective temperature proxy** for an open‑system channel where information leaks into unresolved lattice micro‑DOF (a coarse‑grained thermodynamic sink).
- A falsifiable next step is to test whether a fluctuation–dissipation‑like relation can be derived or observed in controlled toy runs.

### 9.5 EM: “bulk polarization” as a geometric reinterpretation (interpretational layer)

Standard QED describes vacuum polarization via loop corrections / virtual pairs. 
This project’s mechanical vocabulary allows an alternative description:

- **Bulk polarization / bulk tensioning**: under EM‑relevant junction stress, the amorphous bulk deforms and the junction filter response changes.
- In practice (in this draft), the EM likelihood is still computed relative to a standard baseline; the “bulk polarization” language is a **mapping / interpretation**, not an extra fit term.

A hard falsification target for this interpretation is whether the model can reproduce *running-like* behavior (effective response changing with $t$ or $s$) **without** introducing extra free knobs beyond the prereg set.

### 9.6 Weak: mass ordering preference as a geometric compatibility question (hypothesis)

Empirically, the scan‑free runs show a preference pattern between NO and IO under fixed $(A,\phi,\zeta,k_{\mathrm{rt}},\kappa_{\mathrm{gate}})$ choices. 
A proposed geometric mechanism is:

- $\phi$ (chirality) aligns constructively with the NO gap structure but creates a larger effective phase‑mismatch / frictional loss for IO.

This is explicitly a **hypothesis**, not a proven theorem. 
Its falsification is straightforward: fix the prereg parameter point and repeat across multiple experiments/channels; if the preference flips arbitrarily, the mechanism fails.

### 9.7 Strong: unitarity sanity check (optical-theorem consistency)

The complex response used in the strong sector is read as an eikonal-like attenuation:

- negative $A_I$ corresponds to flux leaving the elastic channel,
- unitarity is respected when that flux is accounted for as inelastic production (black‑disk tendency at high energy).

This is treated as a **consistency constraint**, not an extra degree of freedom.

### 9.8 Gravity–EM coupling as lattice mechanics (what to claim, what not to claim)

The framework *permits* a mechanical coupling channel:

- GW/metric strain modulates inter‑cube distances → changes junction geometry → modifies EM junction filtering in principle.

This draft does **not** claim a detected effect; it only states the coupling as an allowed mechanism in the substrate picture. 
A publishable claim would require a prereg observational target and a controlled analysis window.

## 10. Summary and open tests

### 10.1 What the paper establishes now
- A single **unified-equation modulation interface** (parameters + CLI) reused across weak / strong / EM / DM / GW, explicitly extended with entanglement and photon bridge lines and a target-specific FT-ICR cross-domain branch.
- A **current performance-run section** (Sec. 8) with repo-root commands synchronized to the updated runbook for WEAK / STRONG / EM / DM / MS / LIGO.
- An explicit **performance-only scoreboard** that now separates sectors with a cleared locked criterion from sectors that are currently non-passing or outside the present scoring frame.

**Sector status snapshot (current performance revision).**  
This table is **performance-only**.  
- **performance pass** = the declared preregistered performance criterion is met on the stated real-data branch.  
- **not established** = the tested branch does not clear that performance criterion.  
- **not scored here** = the line remains in the draft for context, but it is outside the current performance scoreboard.

| Sector | Current status | Evidence in this document | Notes |
|---|---|---|---|
| Weak (T2K/NOvA/MINOS) | **performance pass** | Sec. 5.1 + Sec. 8 | Current locked combined score is positive (`TOTAL SCORE = 0.489377`). |
| Strong (sigma_tot + rho) | **performance pass** | Strong sector reruns + Sec. 8 | Net `Delta chi2` is positive after combining sigma_tot and rho; rho still carries tension. |
| EM (LEP Bhabha + MuMu) | **not established** | Sec. 3-4 + Sec. 8 | The tested Bhabha and MuMu branches both return `Delta chi2 = 0`; no current performance superiority is established. |
| GW / LIGO ringdown | **performance pass** | Sec. 6 + Sec. 8 | The canonical exact GW170814 branch is locally re-confirmed as a passing performance result. |
| DM / SPARC | **performance pass** | Sec. 7 + Sec. 8 | The locked DM rerun clears the k-fold positive-delta criterion. |
| FT-ICR mass spectrometry (target-specific) | **performance pass** | Sec. 4.9 + Sec. 8 | Both the `internal_only` strict branch and the `full` ablation branch pass the locked prereg criteria. |
| Entanglement (NIST CHSH audit) | **not scored here** | Sec. 4.10 | Retained as a bridge/audit line; not part of the current performance scoreboard. |
| Photon (birefringence accumulation) | **not scored here** | Sec. 4.11 | Retained as a bridge/scaffolding line; not part of the current performance scoreboard. |

### 10.2 What is not yet a hard claim
- **Sky localization** is still not claimed as a completed result; it remains a pipeline extension that would need its own dedicated robustness and multiple-testing accounting.
- **Entanglement** is not presented as a first-principles Bell-violation derivation; in this paper state it is an audit / bridge line only.
- **Photon birefringence** is not presented as a final calibrated cosmic-birefringence extraction; in this paper state it is a bridge / scaffolding line only.
- **FT-ICR mass spectrometry** is not a fundamental-particle claim in this draft; it remains a target-specific cross-domain robustness result.
- **EM** does not currently establish a performance pass in the tested branches, so the present EM reading must remain explicitly limited.
- Cross-sector “universal parameter” claims are not made until each **scored** sector has finalized paper-facing figures, tables, and robustness notes.
- The topological-field-theory discussion remains an interpretive / future-work framing, not a completed derivation.

### 10.3 Open tests required for a publishable v1
**Priority 1 - publication blockers**
- **EM:** either produce a genuinely positive preregistered performance branch or keep EM explicitly framed as a negative / not-established sector.
- **Paper structure:** finalize section ordering / numbering consistency and remove any remaining stale wording that implies the superseded older status framing.
- **Figures:** replace remaining placeholders with the current outputs for the sectors already on the performance scoreboard.

**Priority 2 - strengthens the paper substantially**
- **Weak:** run an independent validation of the preregistered `du_phase` rule on a separate public dataset or non-overlapping holdout.
- **LIGO:** add an optional exact OFF100K confirmation and extract a compact figure set from the already-working exact branch.
- **DM:** embed a compact figure / table summary from the current positive locked rerun.
- **FT-ICR:** keep the sector, but maintain the prose framing as target-specific cross-domain robustness and avoid over-extending the physical claim.

**Priority 3 - deeper theory (not required for the current release)**
- Derive the substrate-to-operator bridge (sector hooks) from explicit substrate coordinates / DOFs.
- Add dimensional-analysis support for the CT / RT dual-tension split.
- Strengthen sector-level microphysics derivations beyond surrogate `(n, sigma, v)` mappings.

**Data requirement note:** Most of the remaining paper-facing work can be completed with the current codebase and existing public datasets. The most likely extra public-data step is the independent weak-sector validation (and any optional new EM branch only if that path is actively pursued).

## Appendix A — Removed (portable paper edition)

Earlier drafts included verbatim console logs for local exploratory runs (including absolute machine paths).  
For portability and to avoid confusing **run_ok** with the actual **performance verdict**, those logs were removed from the paper.  
The repository’s `repro/logs/` and `repro/run_summary.csv` should be treated as the canonical provenance record.

## Appendix C. Auto-extracted CLI inventory from `` (completeness aid)

This appendix is generated from the full project-history log file and is included **only** to prevent “missing knob” confusion. 
**Physics-relevant flags are defined in §7.B.** Everything else is classified as analysis/control or I/O/debug.

- Unique CLI flags seen in project history: **710**
- Flags explicitly defined as physics knobs in §7.B: **55**
- Remaining flags (analysis/control + I/O/debug): **656**

### C.1 Most frequent physics flags (defined in §7.B)

- `A` (930)
- `zeta` (584)
- `phi` (582)
- `L0_km` (544)
- `k_rt` (470)
- `n` (458)
- `kappa_gate` (446)
- `rho` (439)
- `E0` (437)
- `source_mode` (412)
- `ordering` (386)
- `kernel` (378)
- `Ye` (342)
- `det_rot_deg` (339)
- `alpha` (315)
- `omega0_geom` (285)
- `omega` (252)
- `center_guess_gps` (248)
- `offsource_n` (246)
- `geo_action` (245)
- `time_scales` (241)
- `anchor_band` (241)
- `geo_phase_mode` (238)
- `max_model_lag_s` (233)
- `analysis_band` (232)

#### C.1.1 Global mechanism map (operator → lattice “address” → parameters)

This map is the **one-page mental model** of the framework. It makes explicit which operator lives where in the CurvedCube machine.

**Address map (where the physics lives):**

- **Weak (edge-addressed):** propagation on the rigid **edge threads** (skeleton) → **holonomy / Berry-phase memory**.
- **Strong (bulk-addressed):** propagation through the amorphous **bulk threads** → **edge–bulk desynchronization** (jitter) → complex response $A=A_R+iA_I$.
- **EM (junction-addressed):** **face handshake** at cube–cube junctions (the 16‑thread bus sliced by global planes) → stiffness filter $J(\tau;\kappa_{\mathrm{junc}})$ + prereg anchoring.
- **Gravity/DM (RT-addressed):** distance‑dependent tension of **external (inter‑cube) RT threads** + plane anchors → effective metric $g^{\mathrm{eff}}_{\mu\nu}$.

**Global planes (3D “slicers”):**

- Planes are global reference manifolds that **slice** junctions (vertical + horizontal families).
- **Plane ↔ cube connections exist**: internal/bulk anchor threads couple the bubble node to the plane reference (localization/identity).
- **Plane ↔ plane direct wires do not exist**: parallel planes couple **indirectly** via the intervening cube lattice (RT springs). Gravity/DM is this mediated stress propagation.

**Data-journey storyboard (single hop $A\to B$):**
1. A state leaves cube $A$ and approaches the face $A\leftrightarrow B$.
2. It splits into **fast edge path** (skeleton) and **slow bulk path** (amorphous interior).
3. At the face, the 16‑thread bus compares the vectoral boundary state across the **plane slice**.
4. The two components recombine: phase difference $\Delta t$ creates interference $\mathcal R(\Delta t)=e^{-\Gamma\Delta t}e^{i\Omega\Delta t}$.
5. The result is then filtered by the **addressed operator**:
   - weak: holonomy accumulation on edges;
   - strong: complex amplitude $A_R/A_I$ from desynchronization;
   - EM: stiffness $J(\tau;\kappa_{\mathrm{junc}})$ and pivot anchor;
   - gravity/DM: RT tension law feeding $g^{\mathrm{eff}}_{\mu\nu}$.

This resolves the common confusion: the **pattern** is produced by the **split‑path geometry (interference)**; the **success / rejection** is enforced by the **junction stiffness / gating threshold** (preregistered).

#### C.1.2 Global parameter glossary (physics knobs only; name → mechanism → operator → sector)

The following parameters are the ones that **change the physical operators** (not just I/O or plotting). They are the only “knobs” allowed to affect predictions.

| Symbol / name | CLI flag(s) (typical) | Mechanistic meaning | Operator location | Sector(s) | Units / domain |
|---|---|---|---|---|---|
| $A$ (complex response amplitude) | `--A` | Strength of geometric response; decomposes into $A_R,A_I$ via $\mathcal R(\Delta t)$. | bulk/edge recombination | Strong (and shared kernels) | dimensionless |
| $\alpha,n,E_0$ (env/clock law) | `--alpha --n --E0` | Interaction-frequency scaling $\mathcal N(s)$ (“the clock”), not an external environment. | accumulation axis | Strong / cross-sector scaling | dimensionless |
| `env_mode` | `--env_mode` | Choice of accumulation law family (e.g. `log`, `eikonal`). | accumulation axis | Strong | discrete mode |
| $s_M$ | `--s_M` | Reference energy scale in accumulation $\mathcal N(s)$. | accumulation axis | Strong | GeV$^2$ (as $s$) |
| $s_{\mathrm{ref}}$ | `--s_ref` | Normalization point for $\mathcal N(s)$ (typically a highest-energy anchor). | accumulation axis | Strong | GeV$^2$ (as $s$) |
| $k_{\mathrm{rt}}$ | `--k_rt` | RT kernel scale controlling neighbor coupling range/weight. | RT network | Weak/Strong/DM/GW (kernel-dependent) | dimensionless (kernel index) |
| $\phi$ (chirality/twist) | `--phi` | Internal twist of bulk threads relative to edge frame; CP/handedness source. | bulk geometry | Weak (CP), cross checks | radians |
| `geo_dcp_mode` | `--geo_dcp_mode` | Phase-extractor operator for holonomy: `du_phase` (connection/gradient), `u_phase` (ablation control). | edge/loop readout | Weak | discrete mode |
| $\zeta$ | `--zeta` | Topological friction / geometric temperature controlling damping/decoherence into the lattice. | surface/bulk dissipation | Weak + GW (+ strong damping) | dimensionless (rate proxy) |
| $\kappa_{\mathrm{gate}}$ | `--kappa_gate` | Gate/penalty stiffness (accept/reject threshold for mismatch). | gate functional | Weak (and general gating) | dimensionless |
| $\kappa_{\mathrm{junc}}$ | `--kappa_junc` (or legacy `kappa_j`) | Junction stiffness regulating forward EM; filters out-of-order/misaligned face handshakes. | junction filter $J(\tau;\kappa)$ | EM | dimensionless |
| $x_{\mathrm{pivot}}$ | `--cos_pivot` (+ `--center_mode pivot_cos`) | Pivot anchor for shape-only centering (prevents DC wins). | EM scoring convention | EM holdouts | dimensionless ($\cos\theta$) |
| $\omega_0^{\mathrm{geom}}$ | `--omega0_geom` | Geometry-fixed oscillation scale (e.g. $1/L_0$). | phase accumulator | Weak | 1/km |
| $\omega$ | `--omega` | Oscillation frequency when treated as explicit (non-fixed) input. | phase accumulator | Weak | 1/km |
| $L_0$ | `--L0_km` | Baseline scale for geometric frequency. | geometry | Weak | km |
| $\rho,Y_e$ | `--rho --Ye` | Matter profile (MSW-like) used in the forward model. | matter term | Weak | g/cm$^3$, dimensionless |
| $\zeta_{\mathrm{decoh}}$ | `--decoh_zeta` | Additional decoherence channel (kept zero unless prereg). | damping | Weak | dimensionless |
| $\kappa_{\mathrm{back}}$ | `--kappa_back` | Backreaction stiffness coupling plane-stress to metric response. | RT/plane stress | GW + DM | dimensionless |
| `det_rot_deg` | `--det_rot_deg` | Detector-frame rotation used only for polarization sanity checks (0°/45°). | readout map | GW | degrees |
| `sky_ra_deg` | `--sky_ra_deg` | Right ascension $\alpha$ used for detector projection (preregistered; no sky scan). | projection | GW | degrees |
| `sky_dec_deg` | `--sky_dec_deg` | Declination $\delta$ used for detector projection (preregistered; no sky scan). | projection | GW | degrees |
| `pol_psi_deg` | `--pol_psi_deg` | Polarization frame angle $\psi$ (preregistered gauge choice; report ablations only). | projection | GW | degrees |
| `ring_f0_hz` | `--ring_f0_hz` | Drive carrier frequency for the *excitation* burst (Phase A only; not matched to data). | drive | GW | Hz |
| `ring_tau_s` | `--ring_tau_s` | Exponential envelope time constant of the drive burst (Phase A). | drive | GW | s |
| `ring_t_end` | `--ring_t_end` | Drive end time $t_e$ defining the start of free decay (Phase B). | protocol | GW | s |
| `drive_gain` | `--drive_gain` | Drive amplitude used only in “forced→free” ringdown protocol; must be preregistered. | drive term | GW | dimensionless |

**Important audit rule:** any CLI option **not** in this table is to be read as analysis/I‑O/control unless it is explicitly promoted here with a physical operator and a prereg protocol.

#### C.1.3 Extended physics inventory from project logs (legacy / optional operators)

The command logs contain additional optional modules (used in some experiments but not required for the core prereg tests). We keep them listed so nothing is “lost”, but they must be explicitly preregistered before being used in any claim:

- **Breathing mode**: `breath_B`, `breath_w0`, `breath_gamma` (bulk oscillator added on top of $\mathcal R(\Delta t)$).
- **Thread mode**: `thread_C`, `thread_w0`, `thread_gamma`, `thread_weight_app`, `thread_weight_dis`, `thread_gate*` (auxiliary thread envelope / gating variants).
- **Shear stiffness family**: `kappa_shear`, `kappa_shear_post` (post-processing / shear regularizers).
- **Plane knobs** (addressing, not fitting): `enable_gauge_plane`, `plane_mode`, `plane_axis`, `plane_cz` (select which global plane family is used for slicing/locking in a given prereg run).

If a module is not used, it must be explicitly set to neutral (e.g., amplitude $=0$, gate disabled, or fixed defaults) to preserve falsifiability.

### C.2 Most frequent non-physics flags (analysis/control + I/O)

- `out` (855)
- `pack` (839)
- `out_csv` (750)
- `chi2_out` (419)
- `out_prefix` (353)
- `cov` (352)
- `model_csv` (294)
- `no_profile` (287)
- `h1_hdf5` (268)
- `seed` (261)
- `l1_hdf5` (256)
- `plot_png` (248)
- `baseline_csv` (236)
- `baseline_col` (228)
- `baseline_group_col` (220)
- `t_col` (211)
- `beta_nonneg` (206)
- `ringdown_start_s` (200)
- `ringdown_dur_s` (199)
- `model_col` (191)
- `shape_only` (186)
- `duration` (186)
- `nx` (184)
- `ny` (184)
- `model_t0peak_col` (181)

#### C.2.1 Non-physics flags that reviewers commonly misread as “hidden fit knobs” (definitions)

These flags do **not** change the CurvedCube physics operators (kernel, junction law, holonomy, dual‑tension rule). They only affect **how data are loaded, which columns are compared, how results are saved/visualized, or which *pre-registered* scoring convention is used**. 
**Audit rule:** if a flag is *not* listed as a physics knob in §7.B, it must be interpreted as analysis/control or I/O/debug.

| Flag | Category | What it changes (operational) | Why it is not a physics knob |
|---|---|---|---|
| `--pack` | Input/I‑O | Chooses the dataset pack (bins, errors, channels). | Selects *data*, not the model. The model operators are unchanged. |
| `--cov` | Analysis (scoring) | Which covariance to use (e.g., total/stat/sys if provided). | Changes χ² weighting/conditioning; physics parameters unchanged. |
| `--seed` | Reproducibility | RNG seed for stochastic parts (if any) / shuffling. | Ensures reproducibility; not an adjustable physical parameter. |
| `--shape_only` | Analysis (scoring) | Uses shape-only comparison (normalization removed). | A scoring convention, not a model degree of freedom. Must be preregistered. |
| `--no_profile` | Control | Disables profile-likelihood tooling / profile reads. | Removes an analysis feature; does not alter forward model. |
| `--baseline_csv` | Input/I‑O | Reads baselines from a CSV rather than inline pack fields. | Data plumbing; physical kernel unchanged. |
| `--baseline_col` | Input/I‑O | Column name for baseline values in CSV. | Parsing detail only. |
| `--baseline_group_col` | Input/I‑O | Groups baseline rows (e.g., channels). | Parsing/grouping; does not change physics. |
| `--t_col` | Input/I‑O | Column name for time arrays. | Parsing detail only. |
| `--model_col` | Analysis/I‑O | Column to compare as the model prediction. | Selects which output column is used; model generation unchanged. |
| `--model_csv` | Output/I‑O | Writes model predictions to a CSV file. | Output only. |
| `--out` / `--out_csv` / `--out_prefix` | Output/I‑O | Output path(s) and naming. | Output only. |
| `--chi2_out` | Output/I‑O | Writes χ² / score summary to file. | Output only. |
| `--plot_png` | Output/Viz | Saves plots to PNG. | Visualization only. |
| `--duration` | Control | Run duration for simulations / window length for analysis. | A windowing choice; must be fixed in prereg runs. Not a physics knob. |
| `--ringdown_start_s` | Analysis (windowing) | Start time of the ringdown window. | Window selection; must be preregistered and reported. |
| `--ringdown_dur_s` | Analysis (windowing) | Duration of ringdown analysis window. | Window selection; prereg/reporting item. |
| `--nx`, `--ny` | Numerics/Grid | Grid resolution for internal numerical representations. | Numerical accuracy knob; should be set for convergence, not fit. |

**Important:** some scripts may contain convenience flags like `*_grid`, `*_min`, `*_max` intended for parameter scans. **This paper’s falsification runs do not use scanning**; any scan-capable flag is treated as analysis tooling and is irrelevant unless explicitly invoked and disclosed in the run command lines.

#### C.2.2 Minimal disclosure checklist for preregistered runs

To make it unambiguous that non-physics flags are not “hidden fits”, each preregistered run should disclose (in the command line or table): 
`pack`, `cov`, `shape_only` (if used), windowing (`ringdown_*` if GW), and the exact output artifacts produced (`out*`, `chi2_out`, `plot_png`). 
Physics knobs remain the ones in §7.B only.

### C.3 Full non-physics flag lists (names only)

**Analysis/control (alphabetical):**
```text
A_I
A_R
A_grid
A_max
A_min
A_n
A_rep
A_tidal
Atruth
B
B_twist
C
D
Fcross_H1
Fcross_L1
Fcross_V1
Fplus_H1
Fplus_L1
Fplus_V1
GammaZ
H
H1_xarm_az_deg
L0
L1_xarm_az_deg
L_km
Nface
Nin
Omega0
S_amorph
S_rep
T0
TTCHK
T_body
T_cb
T_edge
T_face
V1_xarm_az_deg
X
abort_on_nan
absorb_thickness
aic_k
allow_unstable
alpha0
alpha_max
alpha_min
alpha_s
amorph_Rmax_frac
amorph_Rmin_frac
amorph_enable
amorph_etaR
amorph_g
amorph_gamma
amorph_q_clip
amorph_w0_hz
amorph_width
anchor_boundary
anis_rot_phi
app_fhc
app_rhc
append
archive
auto_antenna
auto_event
auto_time_delays
b0_fm
band
band_hi
band_lo
bandpass_hi
bandpass_lo
base_args
baseline
baseline_col
baseline_group_col
baseline_km
baseline_mode
bc
beta
beta_nonneg
bh_M
bh_factors
bhwide_in
bin_avg
bin_shift
bin_shift_app
bin_shift_dis
block_size
bmax_fm
breath_
bubble_mass
bubble_offset
bubble_rep_
bubble_rep_R
bubble_rep_R_derived
bubble_rep_coupling
bubble_rep_k
bubble_rep_mass_GeV
bubble_rep_p
c1_abs
c_bt
c_ct
c_diag
c_diag_
c_edge
c_edge_x
c_edge_y
c_edge_z
c_pin
c_rel
c_rot_deg
c_rt
c_rt_diag
c_rt_rot_deg
calibrate
center_cos
center_mode
channel
cos_sign
cov
crop_post
crop_pre
cross
cross0_col
crossAB_col
cross_col
ct_eps
ct_soft_eps
cube_size
curv_amp
curv_f0_hz
curv_phase_deg
curv_pulse
curv_shape
curv_t_end
curv_t_start
curv_tau_s
curvedcube_
curvedcube_Nface
curvedcube_Nin
dCP
dcp
dcp_key
debug
dec_deg
delta_cp
delta_geo_ref
dephase
det
det_points
det_tol
det_z
detectors
detproj_dec_deg
detproj_detectors
detproj_enable
detproj_mode
detproj_psi_deg
detproj_ra_deg
detproj_rotate_deg
dis_fhc_q1
dis_fhc_q2
dis_fhc_q3
dis_fhc_q4
dis_pred
dis_rhc_q1
dis_rhc_q2
dis_rhc_q3
dis_rhc_q4
dm2
dm2_21
dm2_32
drive_amp
drive_axis
drive_col
drive_env
drive_env_pow
drive_f0_hz
drive_f1_hz
drive_gate_only
drive_idx
drive_pattern
drive_t1
drive_type
drive_weight_norm
driver_col
dsmax
dt
duration
duration_s
dx
em_mode
enable_backreaction
energies
env_list
env_model
env_u
env_u0
env_z
eps_rep
eta
eta_amorph
eta_r
eta_transition
event
event_gps
event_tag
event_utc
evn
evn_line
f0
f0_hz
f_open
f_peak
f_ring_hz
ff_lam
fixed
fixed_anchor_lag_
fixed_anchor_lag_h1_v1_s
fixed_anchor_lag_s
fixed_t_peak_h1
fixedlags
fixedlags_offsource_label
fixedlags_offsource_ms
fixedlags_offsource_step_ms
force
force_scene_seconds
forward
freeze_betas
fs
fs_hz
fullphys_debug
fullphys_op
fullphys_scale
g0
g_bp
g_lp
gain
gain_A
gal_gate_eps
gal_hi_p
gamma
gamma21
gamma31
gamma32
gamma_absorb
gamma_bubble
gamma_corner
gamma_cube
gamma_n
gate_beta
gate_even_smooth_eps
gate_phi0
geo_amp
geo_model
glob
gmst_deg
group_col
group_id
group_key
group_mode
groups
gyro_gain
gyro_gain_corner
gyro_omega
gyro_omega_x
gyro_source_only
h1_hdf5
h_
h_fhc_1re_pred
h_fhc_1rmu_pred
h_rhc_1re_pred
h_rhc_1rmu_pred
help
hierarchy
ifo_list
impulse_amp
impulse_mode
impulse_sigma
in
include_negative
include_zero
init_amp
init_apply_to
init_kind
init_pattern
init_weight_norm
integrator
jitter
k_amorph
k_diag
k_diag_r
k_diag_t1
k_diag_t2
k_edge
k_edge_x
k_edge_y
k_edge_z
k_extra
k_pin
k_rep
k_rot_deg
k_rt_diag
k_rt_rot_deg
kappa
kappa_back
kappa_em
kappa_j
kappa_list
kappa_shear_post
kfold
l1_hdf5
labels
lag_search_s
lag_window_s
lambda_rep
mZ
m_bubble
m_corner
m_cube
m_q_GeV
make_offsource
max_abs_state
max_iter
max_lag_s
merger_width_s
min_points
mode
model
model_col
model_col_cross
model_col_h1
model_col_l1
model_col_plus
model_t0peak_col
mu
nA
nAlpha
n_generated
n_groups
nb
nds
needed
net_Ncell
net_bc_mult
net_bubble_mass
net_center
net_corner_mass
net_demean
net_dt_mode
net_kick
net_w_face
net_w_in
nevent
no_Z
no_abort_on_nan
no_env_scale
no_freeze_betas
no_offsource
no_pin_edges
no_shape_only
no_sign_flip
no_skip_missing
noise_scale
nseeds
nsteps
ntruth
nx
ny
nz
objective
offsource_guard_s
omega0
omega0_hz
omega_hz
omega_mult_col
omega_twist
p_diag
p_edge
p_rep
p_rt
pad_s
param
params
peak_col
peak_search_halfwin_s
penalty_minos
phi0
phi0_deg
phi_backreact_lambda
phi_max
phi_min
phi_snapshot_npy
pin_edges
plane_components
plus
plus_col
pol_psi_deg
pp_sign
print_effective_params
print_time_delays
probe
probe_
probe_n
probe_rot_deg
probe_tol
probe_z
proj_detectors
project_detectors
psd_guard_s
pseudo
psi
psi_deg
pull_bkg
pull_sig
python_exe
qmax_GeV
r0
r_over_Rs
r_soft
ra_deg
rc
rcond
refine
refit_grid
rep_coupling
rep_delta_r
rep_delta_t
rep_form
rep_mass
rep_neighbors
rep_r0
rep_t0_GeV2
require_positive
res
resume
rh
ridge_keep_quantile
ridge_method
ridge_power_keep_q
ridge_smooth
ring_amp
ring_end
ring_f0_hz
ring_f_hz
ring_mode
ring_phase
ring_phase_deg
ring_start
ring_t_end
ring_t_start
ring_tau_s
ringdown_drive
ringdown_dur_s
ringdown_freq_hz
ringdown_mode
ringdown_only
ringdown_start_s
ringdown_tau_s
rt_L0_scale
rt_T0
rt_face_diagonals
runner
runner_args
s2th12
s2th13
s2th23
s_map
sample_rate
samples
scene
search_halfwin_s
search_post
search_pre
seed
seed0
seg_halfwin_s
shape_only
show_top
sigma_tot_mb
sigma_tot_nb
sigma_total_pb
sin2_theta13
sin2_theta23
sin2w
sky_dec_deg
sky_phi_deg
sky_ra_deg
sky_theta_deg
smax_GeV
smin_GeV
source
source_center
source_radius
source_radius_xy
source_t_end
spacing
spin_axis
sqrt_s
sqrt_s_GeV
sqrts_ref_GeV
steps
stft_noverlap
stft_nperseg
strict_closed
substeps
sync_energy
systfrac
t0
t2k_penalty_cli
t2k_rc
t_col
t_merge_s
t_ref_GeV
t_ref_GeV2
t_rep_GeV2
t_total
tag
target_corr
target_inner_f_hz
target_mu
tau
tau_ms
tau_s
tcol
tensor_mode
theta
thr
threshold
tilt_gamma
tilt_per_group
tmax
tmin
top
train
use_body_diagonals
use_derived_r0
use_derived_t0
use_detectors
use_drive_derivative
use_env_scale
use_face_diagonals
use_gyro
use_reactor
use_sigma
v17_kappa_post
v1_hdf5
v_kms
vary
verbose
version
vref_kms
weight_is_pb
window_ms
workers
wtruth
zeta_max
zeta_min
```

**I/O + debug (alphabetical):**
```text
baseline_csv
c_out
c_out_x
c_out_y
c_out_z
chi2_out
cross_csv
csv
csvzip
cv_csv
data
data_bins_csv
data_root
err_log
fit_summary_json
galaxy_csv
geo_model_csv
h_fhc_1re_data
h_fhc_1rmu_data
h_rhc_1re_data
h_rhc_1rmu_data
holdout
holdout_cos_max
holdout_cos_min
holdout_fold
holdout_mode
in_csv
in_pack
indir
infile
inputs
json_out
k_out
k_out_x
k_out_y
k_out_z
keep_json
lep_bins_csv
logdir
minos_pack
model_csv
n_outer
n_threads
net_readout
no_profile
nova_pack
obs_dir
out
out_col
out_csv
out_dir
out_json
out_md
out_meas
out_prefix
out_sink
out_stride
outdir
outfile
output
pack
pack_minos
pack_nova
packs
penalty_holdout
plot_png
plus_csv
points_csv
pred_root
profiles
readout_angle_deg
readout_split
rho_data
root
rotmod_dir
runs_root
sigma_data
sim_csv
t2k_approx_pack
t2k_profiles
test_pack
thread_S0
thread_Sc_factor
thread_calibrate_from_galaxy
thread_eps
thread_gate_band
thread_gate_mode
thread_gate_p
thread_k2
thread_k4
thread_mode
thread_norm
thread_q
thread_r_weight_power
thread_xi
train_csv
with_internal_threads
write
zip
```

*Clarification:* This framework is **not an infinite self‑similar nesting model**; scale-coverage arises from topological universality of the lattice rules, not self-similar recursion.

## Future Work

### Figure completion note (no new data required)

Several sections include figure placeholders. These are not meant as missing evidence; they are an editorial backlog. All planned figures are generated from **already existing run outputs** (CSV summaries and previously produced plots). The journal-facing version will move the long CLI inventories to a technical supplement and will include the minimal figure set required to visually support (i) the strongest holdouts and (ii) the key unresolved lines still called out in the current draft.

### Independent validation for the *du_phase* variant (release-holdout, public datasets)

A remaining vulnerability is the *post‑hoc appearance* of selecting the **du_phase** variant over alternative phase-update variants. A fully independent, δ\_CP‑sensitive real‑data likelihood outside the NOvA/T2K/MINOS family is currently difficult to obtain in a clean, public, “drop‑in runner” format (many atmospheric releases are effectively δ\_CP‑flat, and DUNE is not yet real data). This is **not a blocker** for the present falsification‑first draft, but it is a clear strengthening target.

We therefore preregister the following **release‑holdout validation** plan that requires **no new experiment** (only an additional public release):

1. **Lock the du_phase rule and all one‑for‑all factors** (no tuning).  
2. Use the **already‑used releases as calibration** (e.g., earlier official T2K/NOvA/MINOS releases), and treat a **later official release** as a holdout.  
3. Re-run the same pipeline unchanged and report the holdout Δχ² shift and any qualitative changes in preferred regions.  

This is not “fully independent baseline physics,” but it directly tests whether the du_phase choice survives a **version‑independent** check when confronted with a different official release of the same experiment. If a genuinely δ\_CP‑sensitive independent public likelihood becomes available later, the same preregistered du_phase rule can be transported unchanged as an additional falsifier.

---

*Build/version: 2026-02-21 (v4_52; editorial: added inline g_bp/g_lp forward reference; MS real-data prereg lock unchanged).*