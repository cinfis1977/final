#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ch_model_prob_provider_v1.py

Bu dosya MODEL-FAITHFUL kısım: CH/Eberhard için model olasılıklarını üretecek.

Scorecard şu fonksiyonu çağırır:
    compute_probabilities(run_ctx) -> dict

run_ctx içinde:
- run_id: "03_43", "01_11", ...
- slots: [6] veya [4,5,6,7,8]
- bitmask_hex: "0x20", "0xf8", ...
- N_valid_by_setting: {"00":..., "01":..., "10":..., "11":...}
- trials_valid: toplam valid trial
- h5_path: provenance
- params: (opsiyonel) model_params.json içinden gelen dict

DÖNÜŞ zorunluluğu:
- "P_pp": {"00":..., "01":..., "10":..., "11":...}   # P(++ | setting)

ve aşağıdakilerden BR:
(A) "P_A_plus" ve "P_B_plus" ver:
    P_p0 = P_A_plus - P_pp
    P_0p = P_B_plus - P_pp
(B) doğrudan "P_p0" ve "P_0p" ver.

NOT: Burada toy/proxy üretme. Gerçek GKSL/microphysics state zincirinden türet.
"""
from __future__ import annotations
from typing import Dict, Any


def compute_probabilities(run_ctx: Dict[str, Any]) -> Dict[str, Any]:
    # TODO: Burayı senin gerçek modelinle dolduracağız.
    # Şimdilik açık ve net şekilde durduruyoruz (cheat yok).
    raise NotImplementedError(
        "Model provider implement edilmedi. "
        "compute_probabilities(run_ctx) içinde model-faithful P_pp ve (P_A_plus,P_B_plus) "
        "veya (P_p0,P_0p) üretmelisin."
    )
