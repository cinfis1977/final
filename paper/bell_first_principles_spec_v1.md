# bell_first_principles_spec_v1

## 0. Purpose

This document defines the **implementation contract** for the next entanglement-sector build:

> a **first-principles dynamic Bell forward model** that produces model-side Bell observables
> without data-derived templates, slot seeding, or target-run calibration.

This is **not** yet a claim that the model is already correct.
It is the specification for the **next canonical build target**.

The immediate goal is to move the entanglement sector from:

- CHSH audit
- memory diagnostic
- data-side CH/Eberhard audit

to:

- locked model-side Bell forward prediction
- no-fit multi-run / multi-window evaluation

---

## 1. Current sector boundary (already established)

The current repo state for Entanglement is:

1. **CHSH/NIST audit wrapper**
   - observed \(|S| = 2.455041357825164\)
   - current executable null is a **decorrelation surrogate null** centered near 0
   - this is an **audit / benchmark path**, not a Bell-bound significance proof

2. **Preregistered memory-statistic diagnostic**
   - current rerun gave:
     - `z_p95 = 1.9363439433203153`
     - `z_worst = 1.9914293684831685`
   - this is an empirical-template / holdout diagnostic
   - this is **not** a first-principles Bell derivation

3. **Data-side CH/Eberhard audit**
   - current fully re-verified paper-facing branch = `slots 4–8`
   - verified overall \(J\):
     - `01_11 -> 550`
     - `02_54 -> 176`
     - `03_43 -> 151`

These three lines are useful and remain valid.
But none of them is yet the required **model-side Bell forward predictor**.

---

## 2. Scope of this spec

This spec covers:

- state representation
- dynamical evolution
- measurement map
- Bell observable construction
- interface / IO contract
- no-fit restrictions
- telemetry and audit outputs
- locked evaluation matrix

This spec does **not** yet prove that the chosen dynamics is the true physical mechanism.
It defines the **canonical implementation target** for the next iteration.

---

## 3. Primary target observable

### 3.1 Primary observable
The primary Bell observable for the first first-principles build is:

\[
J \equiv N(++|ab) - N(+0|ab') - N(0+|a'b) - N(++|a'b')
\]

and its model-side probability version:

\[
J_{\mathrm{model}}^{(p)} \equiv
P(++|ab) - P(+0|ab') - P(0+|a'b) - P(++|a'b')
\]

For a run with observed valid-setting trial counts
\[
N_{ab},\; N_{ab'},\; N_{a'b},\; N_{a'b'}
\]
the count-level predicted statistic is:

\[
J_{\mathrm{model}} =
N_{ab}\,P(++|ab)
-
N_{ab'}\,P(+0|ab')
-
N_{a'b}\,P(0+|a'b)
-
N_{a'b'}\,P(++|a'b')
\]

### 3.2 Secondary observable
The secondary observable is CHSH:

\[
S_{\mathrm{model}} = E_{ab}^{\mathrm{model}} + E_{ab'}^{\mathrm{model}} + E_{a'b}^{\mathrm{model}} - E_{a'b'}^{\mathrm{model}}
\]

with

\[
E_{xy}^{\mathrm{model}} = \sum_{u,v\in\{+1,-1\}} uv \, P(u,v|x,y)
\]

The first implementation target is **J-first**.
CHSH is retained as a consistency / secondary diagnostic.

---

## 4. Locked evaluation matrix

### 4.1 Primary runs
The first locked run family is:

- `01_11`
- `02_54`
- `03_43`

### 4.2 Primary windows
The locked window matrix is:

- `slot6`
- `slots5-7`
- `slots4-8`

### 4.3 Paper-facing embedded branch
For current paper-facing evidence, only `slots 4–8` is treated as fully re-verified.
But the forward-model scorecard must target the **full 3-run × 3-window matrix**.

---

## 5. Chosen state representation

### 5.1 Canonical state space
The first implementation target will use a **two-qubit density matrix**

\[
\rho \in \mathbb{C}^{4\times4}
\]

in the computational basis

\[
\{|00\rangle, |01\rangle, |10\rangle, |11\rangle\}
\]

with:

- Hermiticity: \(\rho^\dagger = \rho\)
- unit trace: \(\mathrm{Tr}\,\rho = 1\)
- positivity: \(\rho \succeq 0\)

### 5.2 Why this choice
This is chosen because:

- it is the minimal Bell-sector state space that can express two-party correlations explicitly
- it permits direct Lindblad / GKSL evolution
- it supports explicit measurement-operator construction
- it avoids data-template shortcuts

### 5.3 Important boundary
This choice is an **implementation choice**, not yet a proof that the full physical substrate reduces exactly to a two-qubit effective model.
If needed later, this can be replaced by a higher-dimensional reduced state.
But v1 will lock to the two-qubit form.

---

## 6. Propagation / evolution variable

### 6.1 Canonical evolution parameter
For v1, the evolution parameter is a dimensionless event-scale variable

\[
\lambda
\]

interpreted as the model’s internal progression coordinate across the effective interaction / memory interval.

### 6.2 Allowed external dependence
The model may depend on externally supplied, **non-target-fitted** variables such as:

- coincidence-gap bin metadata
- setting-pair label
- globally locked detector/environment metadata
- globally locked coherence / damping hyperparameters

### 6.3 Forbidden dependence
The model may **not** use:

- target-run fitted \(A,\tau,S_\infty\)-style empirical templates
- run-specific slot seeds
- target-run parameter back-solving from observed \(J\) or \(S\)
- direct copying of observed probabilities

---

## 7. Dynamical equation

The canonical v1 dynamics is:

\[
\frac{d\rho}{d\lambda}
=
-i\,[H(\lambda; \Theta), \rho]
+
\mathcal{D}[\rho; \Theta]
\]

where \(\Theta\) denotes the globally locked parameter set.

### 7.1 Hamiltonian decomposition
The Hamiltonian is decomposed as:

\[
H(\lambda; \Theta)
=
H_0
+
H_{\mathrm{couple}}(\lambda; \Theta)
+
H_{\mathrm{bias}}(\lambda; \Theta)
\]

with the intended roles:

- \(H_0\): baseline local two-qubit energy structure
- \(H_{\mathrm{couple}}\): shared correlation / coupling generator
- \(H_{\mathrm{bias}}\): optional locked asymmetry / environment term

### 7.2 Dissipator
The dissipator is:

\[
\mathcal{D}[\rho; \Theta]
=
\sum_k \gamma_k(\lambda; \Theta)
\left(
L_k \rho L_k^\dagger
-
\frac{1}{2}\{L_k^\dagger L_k,\rho\}
\right)
\]

with locked Lindblad operators \(L_k\) and locked nonnegative rates \(\gamma_k\).

### 7.3 Minimum required channels
The v1 implementation must support at least:

1. **dephasing**
2. **amplitude-loss / damping**
3. **optional common-mode memory decay**

### 7.4 Mandatory implementation property
If all \(\gamma_k = 0\), the solver must reduce to the closed unitary path.

---

## 8. Measurement map

### 8.1 Settings
For each trial setting pair \((x,y)\in\{a,a'\}\times\{b,b'\}\), define local measurement operators:

- \(M^A_{x,+}\), \(M^A_{x,0}\)
- \(M^B_{y,+}\), \(M^B_{y,0}\)

where:

- \(+\) = detected / event-positive
- \(0\) = no-detect / complementary event

### 8.2 Joint probabilities
The joint event probabilities are:

\[
P(\mu,\nu|x,y)
=
\mathrm{Tr}\!\left[
\left(M^A_{x,\mu}\otimes M^B_{y,\nu}\right)\rho_{xy}^{\mathrm{out}}
\right]
\]

for \(\mu,\nu \in \{+,0\}\).

### 8.3 Required outputs
The implementation must produce at minimum:

- \(P(++|ab)\)
- \(P(+0|ab')\)
- \(P(0+|a'b)\)
- \(P(++|a'b')\)

and, for secondary CHSH diagnostics, enough probabilities to build
\(E_{ab},E_{ab'},E_{a'b},E_{a'b'}\).

### 8.4 Boundary
The measurement map must be model-generated.
It must **not** be filled in from observed frequencies.

---

## 9. Model IO contract

The first implementation should support a function with this conceptual interface:

```python
compute_bell_probabilities(run_ctx: dict, params: dict) -> dict
```

### Required inputs
`run_ctx` may include:

- `run_id`
- `window`
- `settings_counts`
- `gap_metadata`
- optional locked environment metadata

### Required outputs
The returned dict must contain at least:

```python
{
  "P_pp": {"00": ..., "01": ..., "10": ..., "11": ...},
  "P_p0": {"00": ..., "01": ..., "10": ..., "11": ...},
  "P_0p": {"00": ..., "01": ..., "10": ..., "11": ...},
  "J_model_prob": ...,
  "J_model_count": ...,
  "S_model": ...,
  "__telemetry__": {...},
  "__state_audit__": {...},
  "__provider_label__": "BELL_FIRSTPRINCIPLES_V1"
}
```

### Mandatory telemetry
Telemetry must include:

- locked parameter hash
- solver step count
- whether positivity repair / projection was needed
- final trace error
- final min eigenvalue
- active dissipator rates

---

## 10. Forbidden shortcuts

The following are explicitly forbidden in v1:

1. **No target-run fitting**
   - no fitting to observed \(J\)
   - no fitting to observed \(S\)

2. **No memory-template reuse**
   - no use of empirically calibrated \(A,\tau,S_\infty\)-style template from the target run

3. **No slot seeding**
   - no slot6-based back-inference that is later expanded to wider windows

4. **No observed-probability injection**
   - model probabilities cannot be copied or algebraically reconstructed from observed frequencies

5. **No run-specific manual nudges**
   - one locked parameter file must be used across the evaluation matrix

These are hard requirements.
If any is violated, the result is **not** a first-principles Bell forward result.

---

## 11. Parameter lock

A separate file

- `bell_params_locked_v1.json`

must contain the globally locked parameter set.

### Mandatory contents
- parameter values
- version string
- creation note
- SHA-256 hash
- date
- statement that no target-run fit was used

The hash from this file must be written into all evaluation outputs.

---

## 12. Required implementation sequence

### Step 1
Write:

- `bell_first_principles_spec_v1.md`  ← this document

### Step 2
Implement:

- `bell_dynamic_forward_model_v1.py`

### Step 3
Add synthetic mechanism gate:

- `test_bell_forward_mechanism_v1.py`

This test asks:

> Can the chosen locked model produce Bell-direction signal at all in synthetic controlled conditions?

If the answer is **no**, stop and revise the mechanism before touching real-data scorecards.

### Step 4
Freeze:

- `bell_params_locked_v1.json`

### Step 5
Run first real-data eval:

- `run_bell_first_principles_eval_v1.py`

Primary first run:
- `03_43`
- `slots 4–8`

### Step 6
Run full matrix scorecard:

- `BELL_FIRSTPRINCIPLES_SCORECARD_v1.csv`
- `BELL_FIRSTPRINCIPLES_SCORECARD_v1.md`

---

## 13. Acceptance gates

### Gate A — mathematical integrity
The solver must maintain:

- Hermiticity within tolerance
- trace \(\approx 1\)
- positivity within tolerance

### Gate B — synthetic Bell-direction viability
On synthetic controlled examples, the model must demonstrate that Bell-direction signal generation is possible.

### Gate C — no-fit audit
All outputs must show:
- same parameter hash
- no target-run fit
- no observed-probability injection

### Gate D — real-data sign consistency
In the first full matrix run, the minimum expectation is:

- sign agreement with observed \(J\) across the locked matrix

This is a **minimum gate**, not yet the final performance-pass declaration.

### Gate E — final performance-pass candidate
Only after a locked scorecard exists may the project define a true performance-pass criterion for the entanglement Bell forward sector.

---

## 14. What this spec does NOT claim

This document does **not** claim that:

- the entanglement physics is already solved
- the current repo already has this model
- the current memory diagnostic is the same thing as this model
- the current CHSH audit is the same thing as this model
- the current data-side CH/Eberhard audit is the same thing as this model

This document only defines the **next canonical implementation target**.

---

## 15. Immediate next action

The next file to write is:

- `bell_dynamic_forward_model_v1.py`

but only after confirming that the chosen two-qubit GKSL state-space and measurement-map contract above is accepted as the v1 canonical target.
