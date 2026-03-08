from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict


def chi2_poisson_deviance(obs: list[float], pred: list[float], floor: float = 1e-12) -> float:
    tot = 0.0
    for o, p in zip(obs, pred):
        o = float(o)
        p = max(float(p), float(floor))
        if o > 0:
            tot += 2.0 * (p - o + o * math.log(o / p))
        else:
            tot += 2.0 * (p - o)
    return float(tot)


def load_gksl_csv(path: str) -> dict[str, tuple[list[float], list[float], list[float]]]:
    by: dict[str, list[tuple[int, float, float, float]]] = defaultdict(list)
    with open(path, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            ch = str(row.get("channel", ""))
            if not ch:
                continue
            i = int(float(row.get("i", "0") or 0))
            obs = float(row.get("obs", "nan"))
            sm = float(row.get("pred_sm", "nan"))
            geo = float(row.get("pred_geo", "nan"))
            by[ch].append((i, obs, sm, geo))

    out: dict[str, tuple[list[float], list[float], list[float]]] = {}
    for ch, rows in by.items():
        rows = sorted(rows, key=lambda t: t[0])
        out[ch] = ([t[1] for t in rows], [t[2] for t in rows], [t[3] for t in rows])
    if not out:
        raise RuntimeError("No rows read from CSV")
    return out


def apply_shape(mode: str, obs: list[float], pred_sm: list[float], pred_geo: list[float]) -> tuple[list[float], list[float]]:
    if mode == "none":
        return pred_sm, pred_geo
    obs_sum = sum(max(x, 0.0) for x in obs)
    sm_sum = sum(max(x, 1e-12) for x in pred_sm)
    geo_sum = sum(max(x, 1e-12) for x in pred_geo)

    if mode == "per_channel":
        s_sm = obs_sum / sm_sum if sm_sum > 0 else 1.0
        s_geo = obs_sum / geo_sum if geo_sum > 0 else 1.0
        return [x * s_sm for x in pred_sm], [x * s_geo for x in pred_geo]

    if mode == "per_channel_common":
        s = obs_sum / sm_sum if sm_sum > 0 else 1.0
        return [x * s for x in pred_sm], [x * s for x in pred_geo]

    raise ValueError(f"unknown mode={mode}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--floor", type=float, default=1e-12)
    args = ap.parse_args()

    data = load_gksl_csv(args.csv)
    modes = ["none", "per_channel", "per_channel_common"]

    for mode in modes:
        tot_sm = 0.0
        tot_geo = 0.0
        deltas: dict[str, float] = {}
        for ch, (obs, sm, geo) in data.items():
            sm2, geo2 = apply_shape(mode, obs, sm, geo)
            c_sm = chi2_poisson_deviance(obs, sm2, floor=float(args.floor))
            c_geo = chi2_poisson_deviance(obs, geo2, floor=float(args.floor))
            deltas[ch] = c_sm - c_geo
            tot_sm += c_sm
            tot_geo += c_geo
        delta_total = tot_sm - tot_geo
        pos = sum(1 for v in deltas.values() if v > 0)

        print(f"mode={mode}  TOTAL_SM={tot_sm:.6f}  TOTAL_GEO={tot_geo:.6f}  DELTA={delta_total:.6f}  pos_channels={pos}")
        for ch in sorted(deltas):
            print(f"  {ch}: dchi2={deltas[ch]:.6f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
