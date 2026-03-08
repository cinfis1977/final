#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ch_model_prob_provider_v1_TEMPLATE.py

You must implement:
    compute_probabilities(run_ctx) -> dict

Purpose
-------
Provide model-faithful probabilities needed to compute CH/Eberhard J_model for NIST runs.

The scorecard runner will call:

    probs = compute_probabilities(run_ctx)

Where run_ctx contains:
- run_id: "03_43", "01_11", ...
- slots: list[int] (1..16), e.g. [6] or [4,5,6,7,8]
- bitmask_hex: string (e.g., "0xf8")
- N_valid_by_setting: dict with keys "00","01","10","11" (valid trials counts)
- h5_path: path string for provenance (optional for your model)
- params: dict (from --params_json and/or defaults)

You must return a dict with keys:
- "P_pp": dict mapping setting keys "00","01","10","11" -> probability of joint detection (++)

and EITHER:
(A) return marginal detection probabilities and let scorecard derive +0 and 0+:
- "P_A_plus": dict mapping "00","01","10","11" -> P(D_A=1 | setting)
- "P_B_plus": dict mapping "00","01","10","11" -> P(D_B=1 | setting)

Then scorecard will compute:
  P_p0 = P_A_plus - P_pp
  P_0p = P_B_plus - P_pp
(with safety clipping to [0,1])

OR (B) return the CH terms directly:
- "P_p0": dict mapping "00","01","10","11" -> P(+0 | setting)
- "P_0p": dict mapping "00","01","10","11" -> P(0+ | setting)

Notes
-----
- This template intentionally contains NO toy physics. Implement it using your GKSL/microphysics.
- Keep it model-faithful: use your multi-input internal causal variables (decoherence, visibility,
  timing mismatch/jitter/gap proxy, etc.). Avoid collapsing everything to a single scalar proxy unless
  you explicitly mark it as toy and pass --toy_ok in the scorecard runner.

Suggested internal structure (one possible approach)
---------------------------------------------------
1) From your full-model dynamic state -> per-slot intensities:
   lambda_A_u(s|a,theta), lambda_B_u(s|b,theta), lambda_AB_c(s|a,b,theta)
2) Convert to per-window detection probabilities:
   P_pp(a,b) = 1 - Π_{s in S}(1 - (1-exp(-lambda_AB_c)))
   P_A_plus(a,b) = 1 - Π_{s in S}(1 - (1-exp(-lambda_AB_c)))*(1 - (1-exp(-lambda_A_u)))
   P_B_plus(a,b) = analogous

Return those dictionaries.

"""
from __future__ import annotations
from typing import Dict, Any, List


def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return model probabilities for this run/window.

    Expected output keys:
      - P_pp (required)
      - and either:
        - P_A_plus, P_B_plus
        OR
        - P_p0, P_0p
    """
    raise NotImplementedError(
        "Implement compute_probabilities(run_ctx) in ch_model_prob_provider_v1_TEMPLATE.py "
        "using your model to produce CH/Eberhard probabilities."
    )
