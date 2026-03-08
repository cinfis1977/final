#!/usr/bin/env python3
# prereg_entanglement_memory_from_coinc_csv_v1_2_DROPIN.py
# Bridge-E0 prereg (NO FIT) on coincidence CSV
# v1.2 adds:
# - Global CHSH sanity check
# - NullGapShuffle
# - NullOutcomeShuffle (within setting pair)
# - deterministic bin fallback ladder

import argparse, csv, io, math, os, random, statistics
from typing import List, Dict, Tuple, Optional

# ------------------ parsing helpers ------------------

TIME_ALIASES = ["t","time","timestamp","t_unit","t_units","tidx","coinc_t","coinc_time","tick","ticks","coinc_idx","index","idx"]
ASET_ALIASES = ["a_set","alice_setting","setting_a","a_setting","aset","sa","alice_set","a"]
BSET_ALIASES = ["b_set","bob_setting","setting_b","b_setting","bset","sb","bob_set","b"]
AOUT_ALIASES = ["a_out","alice_outcome","outcome_a","aout","oa","alice_out","a_result","a_res"]
BOUT_ALIASES = ["b_out","bob_outcome","outcome_b","bout","ob","bob_out","b_result","b_res"]

def pick_col(cols: List[str], aliases: List[str]) -> Optional[str]:
    lut = {c.strip().lower(): c for c in cols}
    for a in aliases:
        if a.lower() in lut:
            return lut[a.lower()]
    # loose contains fallback
    for c in cols:
        cl = c.strip().lower()
        for a in aliases:
            aa = a.lower()
            if aa in cl or cl in aa:
                return c
    return None

def parse_outcome(v) -> Optional[int]:
    s = str(v).strip()
    if s == "":
        return None
    # numeric
    try:
        x = float(s)
        if x == 1:
            return +1
        if x == 0:
            return -1
        if x == -1:
            return -1
        # integer labels 1/2 -> map 1->-1,2->+1
        if x == 2:
            return +1
    except Exception:
        pass
    low = s.lower()
    if low in {"plus","+","p","up","u","true","t"}:
        return +1
    if low in {"minus","-","m","down","d","false","f"}:
        return -1
    return None

def parse_time(v) -> Optional[float]:
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None

def canon_binary_settings(vals: List[str]) -> Dict[str,int]:
    uniq = []
    seen = set()
    for x in vals:
        sx = str(x).strip()
        if sx not in seen:
            seen.add(sx)
            uniq.append(sx)
    if len(uniq) != 2:
        raise ValueError(f"Expected exactly 2 setting values, got {len(uniq)}: {uniq[:10]}")
    # numeric sort if possible else lexical
    def keyf(s):
        try:
            return (0, float(s))
        except Exception:
            return (1, s)
    uniq_sorted = sorted(uniq, key=keyf)
    return {uniq_sorted[0]: 0, uniq_sorted[1]: 1}

# ------------------ CHSH computations ------------------

def chsh_from_rows(rows: List[Tuple[int,int,int,int,float]], idxs: List[int]) -> Tuple[Optional[float], Optional[float], Dict[str,int], Dict[str,float]]:
    # rows entries: (a_set,b_set,a_out,b_out,gap)
    # Need all 4 setting pairs present
    sums = {(0,0):0.0,(0,1):0.0,(1,0):0.0,(1,1):0.0}
    sums2 = {(0,0):0.0,(0,1):0.0,(1,0):0.0,(1,1):0.0}
    counts = {(0,0):0,(0,1):0,(1,0):0,(1,1):0}
    for i in idxs:
        a,b,oa,ob,_ = rows[i]
        v = oa*ob
        sums[(a,b)] += v
        sums2[(a,b)] += v*v  # always 1 but keep generic
        counts[(a,b)] += 1
    if any(counts[k] == 0 for k in counts):
        return None, None, {f"n{k[0]}{k[1]}":counts[k] for k in counts}, {}
    E = {}
    VarE = {}
    for k in counts:
        n = counts[k]
        mu = sums[k]/n
        E[k]=mu
        if n <= 1:
            VarE[k] = float("inf")
        else:
            # sample variance of mean
            # var(sample) = (E[x^2]-mu^2)*n/(n-1), var(mean)=var(sample)/n
            ex2 = sums2[k]/n
            vs = max(0.0, (ex2 - mu*mu) * n / (n-1))
            VarE[k] = vs / n
    S = E[(0,0)] + E[(0,1)] + E[(1,0)] - E[(1,1)]
    VarS = VarE[(0,0)] + VarE[(0,1)] + VarE[(1,0)] + VarE[(1,1)]
    sigS = math.sqrt(VarS) if VarS == VarS and VarS >= 0 else float("inf")
    extra = {
        "E00":E[(0,0)],"E01":E[(0,1)],"E10":E[(1,0)],"E11":E[(1,1)],
        "sigS":sigS
    }
    return S, sigS, {f"n{k[0]}{k[1]}":counts[k] for k in counts}, extra

def percentile(vals: List[float], p: float) -> float:
    if not vals:
        return float("nan")
    s = sorted(vals)
    if p <= 0: return s[0]
    if p >= 100: return s[-1]
    pos = (len(s)-1) * (p/100.0)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi: return s[lo]
    w = pos - lo
    return s[lo]*(1-w) + s[hi]*w

# ------------------ binning ------------------

def build_edges(gaps: List[float], nbins: int, mode: str) -> List[float]:
    gmin = min(gaps)
    gmax = max(gaps)
    if gmax <= gmin:
        return [gmin, gmax+1e-9]
    edges = []
    if mode == "log":
        lo = max(gmin, 1e-12)
        if lo == gmax:
            lo = gmax/10 if gmax>0 else 1e-12
        l1 = math.log10(lo)
        l2 = math.log10(gmax)
        edges = [10**(l1 + (l2-l1)*i/nbins) for i in range(nbins+1)]
        edges[0] = gmin
        edges[-1] = gmax
    elif mode == "linear":
        edges = [gmin + (gmax-gmin)*i/nbins for i in range(nbins+1)]
    elif mode == "quantile":
        qs = [percentile(gaps, 100*i/nbins) for i in range(nbins+1)]
        edges = qs
        # make strictly nondecreasing and nudge duplicates
        for i in range(1, len(edges)):
            if edges[i] <= edges[i-1]:
                edges[i] = edges[i-1]
        if edges[-1] == edges[0]:
            edges[-1] = edges[0] + 1e-9
    else:
        raise ValueError(mode)
    # ensure strict last bound
    if edges[-1] == edges[0]:
        edges[-1] = edges[0] + 1e-9
    return edges

def assign_bin(x: float, edges: List[float]) -> int:
    # returns 0..nbins-1
    n = len(edges)-1
    if x <= edges[0]:
        return 0
    if x >= edges[-1]:
        return n-1
    lo, hi = 0, n-1
    while lo <= hi:
        mid = (lo+hi)//2
        if edges[mid] <= x < edges[mid+1]:
            return mid
        if x < edges[mid]:
            hi = mid-1
        else:
            lo = mid+1
    return n-1

def try_binning(rows, gaps, nbins, mode):
    edges = build_edges(gaps, nbins, mode)
    bins = [[] for _ in range(nbins)]
    for i, (_,_,_,_,g) in enumerate(rows):
        b = assign_bin(g, edges)
        bins[b].append(i)
    # compute CHSH per bin
    info = []
    n_pop = 0
    n_chsh = 0
    for bi in range(nbins):
        idxs = bins[bi]
        if idxs:
            n_pop += 1
        S, sigS, cnts, extra = chsh_from_rows(rows, idxs) if idxs else (None,None,{}, {})
        if S is not None and math.isfinite(S):
            n_chsh += 1
        gvals = [rows[j][4] for j in idxs] if idxs else []
        info.append({
            "bin": bi,
            "idxs": idxs,
            "n": len(idxs),
            "g_lo": edges[bi],
            "g_hi": edges[bi+1],
            "g_mid": (edges[bi]+edges[bi+1])/2.0,
            "g_mean": (sum(gvals)/len(gvals) if gvals else float("nan")),
            "S": S,
            "sigS": sigS,
            "cnts": cnts,
            "E": extra
        })
    return {"edges": edges, "bins": bins, "info": info, "n_pop": n_pop, "n_chsh": n_chsh}

def select_binning(rows, gaps, nbins_req, prefer_log, debug_lines):
    ladder = []
    first_mode = "log" if prefer_log else "linear"
    second_mode = "linear" if prefer_log else "log"
    for m in [first_mode, second_mode]:
        for nb in [nbins_req, max(10, nbins_req-2), max(8, nbins_req-4), 8, 6]:
            if nb >= 4:
                ladder.append((m, nb))
    for nb in [nbins_req, max(10, nbins_req-2), 8, 6]:
        if nb >= 4:
            ladder.append(("quantile", nb))
    seen = set()
    uniq = []
    for x in ladder:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    best = None
    for mode, nb in uniq:
        res = try_binning(rows, gaps, nb, mode)
        debug_lines.append(f"bin_try mode={mode} nbins={nb} populated={res['n_pop']} chsh={res['n_chsh']}")
        if best is None or res["n_chsh"] > best["n_chsh"] or (res["n_chsh"] == best["n_chsh"] and res["n_pop"] > best["n_pop"]):
            best = {"mode": mode, "nbins": nb, "res": res}
        # accept criterion: enough bins for tail+cal+hold
        if res["n_chsh"] >= 6:
            return {"mode": mode, "nbins": nb, "res": res}
    return best

# ------------------ model fit (no-fit 2-point calibration) ------------------

def finite(x): return x == x and abs(x) != float("inf")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--nbins", type=int, default=12)
    ap.add_argument("--log_gap_bins", action="store_true")
    ap.add_argument("--k_sigma", type=float, default=2.0)
    ap.add_argument("--out_csv", default="out/entanglement_memory_prereg_v1.csv")
    ap.add_argument("--out_bins_csv", default="out/entanglement_memory_bins_v1.csv")
    ap.add_argument("--out_debug_txt", default="out/entanglement_memory_debug_v1.txt")
    ap.add_argument("--null_gap_shuffle", action="store_true")
    ap.add_argument("--null_outcome_shuffle", action="store_true")
    ap.add_argument("--global_chsh_check", action="store_true")
    ap.add_argument("--null_reps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=12345)
    args = ap.parse_args()

    debug = []
    debug.append("=== ENTANGLEMENT MEMORY DEBUG (Bridge-E0 v1.2.1, NO FIT) ===")
    debug.append(f"in_csv={args.in_csv}")

    with open(args.in_csv, "r", encoding="utf-8", errors="replace", newline="") as f:
        rdr = csv.DictReader(f)
        if rdr.fieldnames is None:
            raise SystemExit("Input CSV has no header.")
        cols = list(rdr.fieldnames)
        rows_raw = list(rdr)

    tcol = pick_col(cols, TIME_ALIASES)
    acol = pick_col(cols, ASET_ALIASES)
    bcol = pick_col(cols, BSET_ALIASES)
    aocol = pick_col(cols, AOUT_ALIASES)
    bocol = pick_col(cols, BOUT_ALIASES)
    debug.append(f"cols={cols}")
    debug.append(f"detected_cols: t={tcol} a_set={acol} b_set={bcol} a_out={aocol} b_out={bocol}")
    if not all([tcol, acol, bcol, aocol, bocol]):
        miss = []
        for name, col in [("time",tcol),("a_set",acol),("b_set",bcol),("a_out",aocol),("b_out",bocol)]:
            if not col: miss.append(name)
        raise SystemExit("Missing required columns: " + ", ".join(miss))

    parsed_tmp = []
    bad_parse = 0
    a_set_vals = []
    b_set_vals = []
    for r in rows_raw:
        t = parse_time(r.get(tcol, ""))
        ao = parse_outcome(r.get(aocol, ""))
        bo = parse_outcome(r.get(bocol, ""))
        aS = str(r.get(acol, "")).strip()
        bS = str(r.get(bcol, "")).strip()
        if t is None or ao is None or bo is None or aS == "" or bS == "":
            bad_parse += 1
            continue
        parsed_tmp.append([t, aS, bS, ao, bo])
        a_set_vals.append(aS)
        b_set_vals.append(bS)
    if len(parsed_tmp) < 20:
        raise SystemExit(f"Too few parsed rows ({len(parsed_tmp)}). bad_parse={bad_parse}")

    amap = canon_binary_settings(a_set_vals)
    bmap = canon_binary_settings(b_set_vals)
    debug.append(f"setting_map_A={amap}")
    debug.append(f"setting_map_B={bmap}")

    # sort by time and compute inter-coincidence gap
    parsed_tmp.sort(key=lambda x: x[0])
    rows = []
    prev_t = None
    zero_gap = 0
    neg_gap = 0
    for rec in parsed_tmp:
        t, aS, bS, ao, bo = rec
        if prev_t is None:
            prev_t = t
            continue
        g = t - prev_t
        prev_t = t
        if g < 0:
            neg_gap += 1
            continue
        if g == 0:
            zero_gap += 1
        rows.append((amap[aS], bmap[bS], ao, bo, float(g)))
    if len(rows) < 100:
        raise SystemExit(f"Too few valid rows after gap construction ({len(rows)}).")
    gaps = [r[4] for r in rows]
    debug.append(f"N_valid={len(rows)} bad_parse={bad_parse} zero_gap={zero_gap} neg_gap_drop={neg_gap}")
    debug.append(f"gap_min={min(gaps)} gap_max={max(gaps)}")

    # Global CHSH check (always compute; print if flag on)
    all_idxs = list(range(len(rows)))
    S_global, sig_global, cnts_global, E_global = chsh_from_rows(rows, all_idxs)
    debug.append(f"global_chsh: S={S_global} sig={sig_global} counts={cnts_global} E={E_global}")

    # Binning selection fallback
    chosen = select_binning(rows, gaps, max(4,args.nbins), args.log_gap_bins, debug)
    mode_used = chosen["mode"]
    nbins_used = chosen["nbins"]
    res = chosen["res"]
    info = res["info"]
    chsh_bins = [b for b in info if b["S"] is not None and finite(b["S"]) and finite(b["sigS"])]

    if len(chsh_bins) < 4:
        # write debug before exit
        os.makedirs(os.path.dirname(args.out_debug_txt) or ".", exist_ok=True)
        with open(args.out_debug_txt, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(debug) + "\n")
        raise SystemExit(f"Too few populated CHSH bins ({len(chsh_bins)}). Increase rows or adjust binning.")

    # Tail bins for S_inf: use last k populated CHSH bins, adaptive
    k_tail = 2 if len(chsh_bins) >= 6 else 1
    tail_bins = chsh_bins[-k_tail:]
    S_inf = statistics.median([b["S"] for b in tail_bins])
    # sigma_Sinf from tail spread and sigS
    tail_vals = [b["S"] for b in tail_bins]
    if len(tail_vals) >= 2:
        mad = statistics.median([abs(x - statistics.median(tail_vals)) for x in tail_vals])
        sigma_tail_spread = 1.4826 * mad
    else:
        sigma_tail_spread = 0.0
    sigma_tail_meas = math.sqrt(sum((b["sigS"] if finite(b["sigS"]) else 0.0)**2 for b in tail_bins)) / max(1, len(tail_bins))
    sigma_Sinf = math.sqrt(sigma_tail_spread**2 + sigma_tail_meas**2)

    # calibration bins: choose two populated bins (prefer central adjacent pair), no-fit solve with signed->abs fallback
    core = chsh_bins[:-k_tail] if len(chsh_bins) > k_tail + 1 else chsh_bins[:]
    if len(core) < 2:
        core = chsh_bins[:2]

    mid_pair_start = max(0, (len(core)//2) - 1)
    if mid_pair_start + 1 >= len(core):
        mid_pair_start = len(core) - 2
    pair_candidates = []
    if len(core) >= 2:
        pair_candidates.append((core[mid_pair_start], core[mid_pair_start+1]))
        for i in range(len(core)-1):
            cand = (core[i], core[i+1])
            if cand[0]["bin"] == pair_candidates[0][0]["bin"] and cand[1]["bin"] == pair_candidates[0][1]["bin"]:
                continue
            pair_candidates.append(cand)

    solved = None
    # pass 1: signed mode (preserve sign of S-S_inf)
    for b1, b2 in pair_candidates:
        gg1 = b1["g_mean"] if finite(b1["g_mean"]) else b1["g_mid"]
        gg2 = b2["g_mean"] if finite(b2["g_mean"]) else b2["g_mid"]
        if gg2 <= gg1:
            b1, b2 = b2, b1
            gg1, gg2 = gg2, gg1
        dd1 = b1["S"] - S_inf
        dd2 = b2["S"] - S_inf
        if dd1 == 0 or dd2 == 0 or dd1*dd2 <= 0:
            continue
        rr = dd2 / dd1
        if not (finite(rr) and rr > 0 and rr < 1):
            continue
        tau_try = -(gg2 - gg1) / math.log(rr)
        if not finite(tau_try) or tau_try <= 0:
            continue
        A_try = dd1 / math.exp(-gg1 / tau_try)
        solved = {
            "mode": "signed", "cal_bins": [b1,b2], "g1": gg1, "g2": gg2,
            "d1": dd1, "d2": dd2, "tau_m": tau_try, "A": A_try
        }
        break

    # pass 2: absolute-envelope mode (deterministic rescue; still no-fit)
    if solved is None:
        for b1, b2 in pair_candidates:
            gg1 = b1["g_mean"] if finite(b1["g_mean"]) else b1["g_mid"]
            gg2 = b2["g_mean"] if finite(b2["g_mean"]) else b2["g_mid"]
            if gg2 <= gg1:
                b1, b2 = b2, b1
                gg1, gg2 = gg2, gg1
            dd1 = abs(b1["S"] - S_inf)
            dd2 = abs(b2["S"] - S_inf)
            if dd1 == 0 or dd2 == 0:
                continue
            rr = dd2 / dd1
            if not (finite(rr) and rr > 0 and rr < 1):
                continue
            tau_try = -(gg2 - gg1) / math.log(rr)
            if not finite(tau_try) or tau_try <= 0:
                continue
            A_try = dd1 / math.exp(-gg1 / tau_try)
            solved = {
                "mode": "abs", "cal_bins": [b1,b2], "g1": gg1, "g2": gg2,
                "d1": (b1["S"] - S_inf), "d2": (b2["S"] - S_inf), "tau_m": tau_try, "A": A_try
            }
            break

    if solved is None:
        os.makedirs(os.path.dirname(args.out_debug_txt) or ".", exist_ok=True)
        debug.append("nofit_solve_failed: no adjacent pair solved in signed or abs mode")
        with open(args.out_debug_txt, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(debug) + "\n")
        raise SystemExit("No-fit 2-point calibration failed (no solvable adjacent pair).")

    cal_mode = solved["mode"]
    cal_bins = solved["cal_bins"]
    g1 = solved["g1"]; g2 = solved["g2"]
    d1 = solved["d1"]; d2 = solved["d2"]
    tau_m = solved["tau_m"]; A = solved["A"]

    # holdout bins: all populated CHSH bins excluding tail and cal
    tail_ids = {b["bin"] for b in tail_bins}
    cal_ids = {b["bin"] for b in cal_bins}
    hold_bins = [b for b in chsh_bins if b["bin"] not in tail_ids and b["bin"] not in cal_ids]
    if len(hold_bins) < 2:
        os.makedirs(os.path.dirname(args.out_debug_txt) or ".", exist_ok=True)
        debug.append(f"holdout_too_small={len(hold_bins)}")
        with open(args.out_debug_txt, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(debug) + "\n")
        raise SystemExit(f"Too few holdout bins ({len(hold_bins)}).")

    # evaluate holdout z
    z_abs = []
    z_vals = []
    for b in hold_bins:
        g = b["g_mean"] if finite(b["g_mean"]) else b["g_mid"]
        sig = math.sqrt((b["sigS"] if finite(b["sigS"]) else 0.0)**2 + sigma_Sinf**2)
        if cal_mode == "signed":
            pred = S_inf + A * math.exp(-g / tau_m)
            z = (b["S"] - pred) / sig if sig > 0 else float("inf")
            b["pred"] = pred
        else:
            pred_env = A * math.exp(-g / tau_m)
            obs_env = abs(b["S"] - S_inf)
            z = (obs_env - pred_env) / sig if sig > 0 else float("inf")
            b["pred"] = pred_env
        b["z"] = z
        z_vals.append(z)
        z_abs.append(abs(z))

    z_p95 = percentile(z_abs, 95.0)
    z_worst = max(z_abs) if z_abs else float("nan")
    verdict = "PASS" if z_p95 <= args.k_sigma else "FAIL"

    # optional nulls
    rnd = random.Random(args.seed)
    null_gap_stats = {}
    null_out_stats = {}

    def run_once_with_modified(gaps_override=None, shuffle_outcomes_within=False):
        # construct modified rows using existing settings/outcomes
        mod_rows = [list(r) for r in rows]
        if gaps_override is not None:
            for i, g in enumerate(gaps_override):
                mod_rows[i][4] = g
        if shuffle_outcomes_within:
            groups = {(0,0):[],(0,1):[],(1,0):[],(1,1):[]}
            for i,r in enumerate(mod_rows):
                groups[(r[0],r[1])].append(i)
            for key, idxs in groups.items():
                aos = [mod_rows[i][2] for i in idxs]
                bos = [mod_rows[i][3] for i in idxs]
                rnd.shuffle(aos); rnd.shuffle(bos)
                for j,irow in enumerate(idxs):
                    mod_rows[irow][2] = aos[j]
                    mod_rows[irow][3] = bos[j]
        mgaps = [r[4] for r in mod_rows]
        chosen2 = select_binning([tuple(r) for r in mod_rows], mgaps, max(4,args.nbins), args.log_gap_bins, [])
        inf2 = chosen2["res"]["info"]
        ch2 = [b for b in inf2 if b["S"] is not None and finite(b["S"]) and finite(b["sigS"])]
        if len(ch2) < 6:
            return None
        k_tail2 = 2 if len(ch2) >= 6 else 1
        tail2 = ch2[-k_tail2:]
        S_inf2 = statistics.median([b["S"] for b in tail2])
        core2 = ch2[:-k_tail2] if len(ch2) > k_tail2 + 1 else ch2[:]
        if len(core2) < 2:
            return None
        mids = max(0, (len(core2)//2)-1)
        if mids+1 >= len(core2): mids = len(core2)-2
        pair_candidates = [(core2[mids], core2[mids+1])] + [(core2[i],core2[i+1]) for i in range(len(core2)-1)]
        solved = None
        for b1,b2 in pair_candidates:
            gg1 = b1["g_mean"] if finite(b1["g_mean"]) else b1["g_mid"]
            gg2 = b2["g_mean"] if finite(b2["g_mean"]) else b2["g_mid"]
            if gg2 <= gg1:
                continue
            dd1 = b1["S"] - S_inf2
            dd2 = b2["S"] - S_inf2
            if dd1 == 0 or dd2 == 0 or dd1*dd2 <= 0:
                continue
            rr = dd2/dd1
            if rr <= 0 or rr == 1.0:
                continue
            tau2 = -(gg2-gg1)/math.log(rr)
            if not finite(tau2) or tau2 <= 0:
                continue
            A2 = dd1 / math.exp(-gg1/tau2)
            solved = (S_inf2,tau2,A2,{b["bin"] for b in pair_candidates[0]},{tb["bin"] for tb in tail2})
            # use the solved pair actually selected
            solved = (S_inf2,tau2,A2,{b1["bin"],b2["bin"]},{tb["bin"] for tb in tail2})
            break
        if solved is None:
            return None
        S_inf2,tau2,A2,cal_ids2,tail_ids2 = solved
        zs=[]
        for b in ch2:
            if b["bin"] in cal_ids2 or b["bin"] in tail_ids2:
                continue
            g = b["g_mean"] if finite(b["g_mean"]) else b["g_mid"]
            pred = S_inf2 + A2*math.exp(-g/tau2)
            sig = b["sigS"] if finite(b["sigS"]) and b["sigS"]>0 else 1.0
            zs.append(abs((b["S"]-pred)/sig))
        if len(zs) < 2:
            return None
        return percentile(zs,95.0)

    if args.null_gap_shuffle:
        vals = []
        base_gaps = gaps[:]
        for _ in range(max(1,args.null_reps)):
            gcopy = base_gaps[:]
            rnd.shuffle(gcopy)
            z95 = run_once_with_modified(gaps_override=gcopy, shuffle_outcomes_within=False)
            if z95 is not None and finite(z95):
                vals.append(z95)
        null_gap_stats = {
            "n_ok": len(vals),
            "z95_median": (statistics.median(vals) if vals else float("nan")),
            "z95_p95": (percentile(vals,95.0) if vals else float("nan"))
        }
        debug.append(f"null_gap_shuffle={null_gap_stats}")

    if args.null_outcome_shuffle:
        vals = []
        for _ in range(max(1,args.null_reps)):
            z95 = run_once_with_modified(gaps_override=None, shuffle_outcomes_within=True)
            if z95 is not None and finite(z95):
                vals.append(z95)
        null_out_stats = {
            "n_ok": len(vals),
            "z95_median": (statistics.median(vals) if vals else float("nan")),
            "z95_p95": (percentile(vals,95.0) if vals else float("nan"))
        }
        debug.append(f"null_outcome_shuffle={null_out_stats}")

    # Write bins CSV
    os.makedirs(os.path.dirname(args.out_bins_csv) or ".", exist_ok=True)
    with open(args.out_bins_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "bin_index","g_lo","g_hi","g_mid","g_mean","n_bin",
            "n00","n01","n10","n11","E00","E01","E10","E11","S","sigS",
            "is_tail","is_cal","is_hold","pred_S","z_hold"
        ])
        for b in info:
            cnt = b["cnts"] if b["cnts"] else {}
            E = b["E"] if b["E"] else {}
            is_tail = 1 if b["bin"] in tail_ids else 0
            is_cal = 1 if b["bin"] in cal_ids else 0
            is_hold = 1 if any(h["bin"] == b["bin"] for h in hold_bins) else 0
            w.writerow([
                b["bin"]+1, b["g_lo"], b["g_hi"], b["g_mid"], b["g_mean"], b["n"],
                cnt.get("n00",""), cnt.get("n01",""), cnt.get("n10",""), cnt.get("n11",""),
                E.get("E00",""), E.get("E01",""), E.get("E10",""), E.get("E11",""),
                b["S"] if b["S"] is not None else "",
                b["sigS"] if b["sigS"] is not None else "",
                is_tail, is_cal, is_hold,
                b.get("pred",""), b.get("z","")
            ])

    # Write summary CSV
    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
    with open(args.out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "model","observable","N_valid","bad_parse","gap_min","gap_max","bins_req","bins_used","bin_mode",
            "tail_k","tail_n_rows","S_inf","sigma_Sinf",
            "cal_bin1","cal_bin2","cal_mode","tau_m","A",
            "n_hold_bins","z_p95","z_worst","k_sigma","VERDICT",
            "global_CHSH_S","global_CHSH_sigS","global_n00","global_n01","global_n10","global_n11",
            "null_gap_enabled","null_gap_reps","null_gap_ok","null_gap_z95_median","null_gap_z95_p95",
            "null_out_enabled","null_out_reps","null_out_ok","null_out_z95_median","null_out_z95_p95",
            "bins_csv","debug_txt"
        ])
        w.writerow([
            "Bridge-E0", "CHSH S vs inter-coincidence gap", len(rows), bad_parse, min(gaps), max(gaps), args.nbins, nbins_used, mode_used,
            k_tail, sum(tb["n"] for tb in tail_bins), S_inf, sigma_Sinf,
            cal_bins[0]["bin"]+1, cal_bins[1]["bin"]+1, cal_mode, tau_m, A,
            len(hold_bins), z_p95, z_worst, args.k_sigma, verdict,
            S_global, sig_global, cnts_global.get("n00",""), cnts_global.get("n01",""), cnts_global.get("n10",""), cnts_global.get("n11",""),
            int(args.null_gap_shuffle), args.null_reps, null_gap_stats.get("n_ok",""), null_gap_stats.get("z95_median",""), null_gap_stats.get("z95_p95",""),
            int(args.null_outcome_shuffle), args.null_reps, null_out_stats.get("n_ok",""), null_out_stats.get("z95_median",""), null_out_stats.get("z95_p95",""),
            args.out_bins_csv, args.out_debug_txt
        ])

    # Debug file
    debug.append(f"chosen_binning mode={mode_used} nbins={nbins_used} populated={res['n_pop']} chsh={res['n_chsh']}")
    debug.append(f"S_inf={S_inf} sigma_Sinf={sigma_Sinf} tail_bins={[b['bin']+1 for b in tail_bins]}")
    debug.append(f"cal_bins={[b['bin']+1 for b in cal_bins]} mode={cal_mode} g1={g1} g2={g2} d1={d1} d2={d2} tau_m={tau_m} A={A}")
    debug.append(f"hold_bins={[b['bin']+1 for b in hold_bins]}")
    debug.append(f"z_p95={z_p95} z_worst={z_worst} verdict={verdict}")
    for b in info:
        debug.append(
            "bin#{:02d} n={} g=[{:.6g},{:.6g}] gmean={:.6g} S={} sigS={} counts={} flags(tail={},cal={},hold={}) pred={} z={}".format(
                b["bin"]+1, b["n"], b["g_lo"], b["g_hi"], (b["g_mean"] if finite(b["g_mean"]) else float("nan")),
                ("{:.9g}".format(b["S"]) if b["S"] is not None else ""),
                ("{:.9g}".format(b["sigS"]) if b["sigS"] is not None else ""),
                b["cnts"], int(b["bin"] in tail_ids), int(b["bin"] in cal_ids),
                int(any(h["bin"]==b["bin"] for h in hold_bins)),
                ("{:.9g}".format(b.get("pred")) if finite(b.get("pred", float("nan"))) else ""),
                ("{:.9g}".format(b.get("z")) if finite(b.get("z", float("nan"))) else "")
            )
        )
    os.makedirs(os.path.dirname(args.out_debug_txt) or ".", exist_ok=True)
    with open(args.out_debug_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(debug) + "\n")

    # Console summary
    print("=== ENTANGLEMENT MEMORY PREREG (NO FIT) ===")
    print("model        : Bridge-E0   S(gap)=S_inf + A*exp(-gap/tau_m)")
    print("observable   : CHSH S vs inter-coincidence gap")
    print(f"N_valid      : {len(rows)} (bad_parse={bad_parse})")
    print(f"gap_range    : [{min(gaps)}, {max(gaps)}]   bins_req={args.nbins} bins_used={nbins_used} mode={mode_used} tail_over={sum(tb['n'] for tb in tail_bins)}")
    print(f"S_inf        : {S_inf:.10g} (from tail bins, k={k_tail})")
    print(f"cal bins     : #{cal_bins[0]['bin']+1}, #{cal_bins[1]['bin']+1}   mode={cal_mode}")
    print(f"tau_m        : {tau_m:.10g}  (time units of your t column)")
    print(f"A            : {A:.10g}")
    print(f"holdout bins : {len(hold_bins)}")
    print(f"z_p95        : {z_p95:.10g}")
    print(f"z_worst      : {z_worst:.10g}")
    print(f"RULE         : PASS if p95(|z_hold|) <= {args.k_sigma}")
    print(f"VERDICT      : {verdict}")
    if args.global_chsh_check:
        print(f"GLOBAL_CHSH  : S={S_global:.10g}  sigS={sig_global:.10g}  counts={cnts_global}")
    if args.null_gap_shuffle:
        print(f"NULL_GAP     : reps={args.null_reps} ok={null_gap_stats.get('n_ok',0)} z95_median={null_gap_stats.get('z95_median', float('nan'))} z95_p95={null_gap_stats.get('z95_p95', float('nan'))}")
    if args.null_outcome_shuffle:
        print(f"NULL_OUTCOME : reps={args.null_reps} ok={null_out_stats.get('n_ok',0)} z95_median={null_out_stats.get('z95_median', float('nan'))} z95_p95={null_out_stats.get('z95_p95', float('nan'))}")
    print(f"OUT_CSV      : {args.out_csv}")
    print(f"BINS_CSV     : {args.out_bins_csv}")
    print(f"DEBUG_TXT    : {args.out_debug_txt}")

if __name__ == "__main__":
    main()
