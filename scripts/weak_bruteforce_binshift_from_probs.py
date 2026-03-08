from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def shift_bins(arr: np.ndarray, shift: int) -> np.ndarray:
    arr = np.asarray(arr, float)
    if shift == 0:
        return arr.copy()
    out = np.zeros_like(arr)
    if shift > 0:
        out[shift:] = arr[:-shift]
    else:
        out[:shift] = arr[-shift:]
    return out


def chi2_poisson_deviance(obs: np.ndarray, pred: np.ndarray, floor: float = 1e-12) -> float:
    obs = np.asarray(obs, float)
    pred = np.asarray(pred, float)
    pred = np.maximum(pred, float(floor))

    term = pred - obs
    m = obs > 0
    term[m] = pred[m] - obs[m] + obs[m] * np.log(obs[m] / pred[m])
    return float(2.0 * np.sum(term))


def safe_ratio(num: np.ndarray, den: np.ndarray, floor: float = 1e-6) -> np.ndarray:
    den2 = np.where(np.abs(den) < floor, np.sign(den) * floor, den)
    den2 = np.where(np.abs(den2) < floor, floor, den2)
    return num / den2


@dataclass(frozen=True)
class ChannelPack:
    name: str
    ctype: str
    n_sig_sm: np.ndarray


@dataclass(frozen=True)
class ChannelBase:
    name: str
    obs: np.ndarray
    p_sm: np.ndarray
    p_geo: np.ndarray
    bkg: np.ndarray


def load_pack(pack_path: Path) -> dict[str, ChannelPack]:
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    out: dict[str, ChannelPack] = {}
    for ch in pack.get("channels", []):
        if not isinstance(ch, dict):
            continue
        name = str(ch.get("name"))
        ctype = str(ch.get("type"))
        bins = ch.get("bins", {})
        n_sig_sm = np.asarray(bins.get("N_sig_sm", []), dtype=float)
        if name and n_sig_sm.size > 0:
            out[name] = ChannelPack(name=name, ctype=ctype, n_sig_sm=n_sig_sm)
    if not out:
        raise RuntimeError("No channels with bins.N_sig_sm found in pack")
    return out


def load_base_csv(csv_path: Path) -> dict[str, ChannelBase]:
    # Expected columns: channel,i,obs,bkg,P_sm,P_geo
    # (plus many others)
    import csv

    rows_by_ch: dict[str, list[dict[str, str]]] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ch = str(row.get("channel", ""))
            if not ch:
                continue
            rows_by_ch.setdefault(ch, []).append(row)

    out: dict[str, ChannelBase] = {}
    for ch, rows in rows_by_ch.items():
        # sort by bin index i
        rows_sorted = sorted(rows, key=lambda r: int(float(r.get("i", "0") or 0)))
        obs = np.array([float(r.get("obs", "nan")) for r in rows_sorted], dtype=float)
        p_sm = np.array([float(r.get("P_sm", "nan")) for r in rows_sorted], dtype=float)
        p_geo = np.array([float(r.get("P_geo", "nan")) for r in rows_sorted], dtype=float)
        bkg = np.array([float(r.get("bkg", "0") or 0.0) for r in rows_sorted], dtype=float)

        if not (obs.size == p_sm.size == p_geo.size):
            raise RuntimeError(f"Base CSV channel={ch} has inconsistent lengths")

        out[ch] = ChannelBase(name=ch, obs=obs, p_sm=p_sm, p_geo=p_geo, bkg=bkg)

    if not out:
        raise RuntimeError("No channel rows found in base CSV")

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Bruteforce WEAK bin shifts offline using fixed GKSL probabilities")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--base_csv", required=True, help="GKSL output CSV with P_sm/P_geo, typically shift=0")
    ap.add_argument("--shift_min", type=int, default=-6)
    ap.add_argument("--shift_max", type=int, default=6)
    ap.add_argument("--epsilon", type=float, default=0.5, help="Delta lock threshold")
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--pred_floor", type=float, default=1e-12)

    args = ap.parse_args()

    pack = load_pack(Path(args.pack))
    base = load_base_csv(Path(args.base_csv))

    # Only use channels that exist in both.
    common = sorted(set(pack.keys()) & set(base.keys()))
    if not common:
        raise RuntimeError("No overlapping channels between pack and base_csv")

    # Ensure consistent bin counts
    for ch in common:
        n_pack = int(pack[ch].n_sig_sm.size)
        n_base = int(base[ch].obs.size)
        if n_pack != n_base:
            raise RuntimeError(f"Bin mismatch for {ch}: pack={n_pack} base_csv={n_base}")

    rows = []
    for s_app in range(int(args.shift_min), int(args.shift_max) + 1):
        for s_dis in range(int(args.shift_min), int(args.shift_max) + 1):
            chi2_sm_total = 0.0
            chi2_geo_total = 0.0
            pos_count = 0
            deltas = {}

            for ch in common:
                cpack = pack[ch]
                cbase = base[ch]

                sig = cpack.n_sig_sm
                if cpack.ctype == "appearance":
                    sig2 = shift_bins(sig, int(s_app))
                else:
                    sig2 = shift_bins(sig, int(s_dis))

                # Match GKSL runner legacy contract (non-rate-kernel mode):
                #   pred_sm  = sig_sm + bkg
                #   pred_geo = sig_sm * (P_geo/P_sm) + bkg
                ratio = safe_ratio(cbase.p_geo, cbase.p_sm, floor=1e-6)
                pred_sm = sig2 + cbase.bkg
                pred_geo = sig2 * ratio + cbase.bkg

                c2_sm = chi2_poisson_deviance(cbase.obs, pred_sm, floor=float(args.pred_floor))
                c2_geo = chi2_poisson_deviance(cbase.obs, pred_geo, floor=float(args.pred_floor))
                d = float(c2_sm - c2_geo)
                deltas[ch] = d
                if d > 0:
                    pos_count += 1
                chi2_sm_total += float(c2_sm)
                chi2_geo_total += float(c2_geo)

            delta_total = float(chi2_sm_total - chi2_geo_total)
            ok = (delta_total >= float(args.epsilon)) and (pos_count >= 3)

            row = {
                "shift_app": int(s_app),
                "shift_dis": int(s_dis),
                "chi2_sm_total": float(chi2_sm_total),
                "chi2_geo_total": float(chi2_geo_total),
                "delta_total": float(delta_total),
                "pos_channels": int(pos_count),
                "lock_ok": bool(ok),
            }
            for ch in common:
                row[f"delta_{ch}"] = float(deltas[ch])
            rows.append(row)

    # Rank: first lock_ok, then lowest geo_total, then highest delta
    def key(r: dict) -> tuple:
        return (
            0 if r["lock_ok"] else 1,
            float(r["chi2_geo_total"]),
            -float(r["delta_total"]),
            -int(r["pos_channels"]),
        )

    rows_sorted = sorted(rows, key=key)

    # Write CSV
    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    import csv

    fieldnames = list(rows_sorted[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_sorted)

    # Print best 5 summary
    best = rows_sorted[:5]
    print("Top candidates (sorted):")
    for r in best:
        print(
            f"shift_app={r['shift_app']:>2} shift_dis={r['shift_dis']:>2} "
            f"chi2_geo={r['chi2_geo_total']:.3f} delta={r['delta_total']:.3f} "
            f"pos={r['pos_channels']} lock_ok={r['lock_ok']}"
        )

    # Also report best-by-delta if none satisfy lock
    if not any(bool(r["lock_ok"]) for r in rows_sorted):
        by_delta = sorted(rows, key=lambda r: (-float(r["delta_total"]), float(r["chi2_geo_total"])))
        r = by_delta[0]
        print("No rows satisfy lock; best-by-delta:")
        print(
            f"shift_app={r['shift_app']} shift_dis={r['shift_dis']} "
            f"chi2_geo={r['chi2_geo_total']:.3f} delta={r['delta_total']:.3f} pos={r['pos_channels']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
