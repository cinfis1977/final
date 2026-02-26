#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bridge-E0 coincidence CSV audit (NO FIT)
- Audits setting/outcome balance and gap-conditioned occupancy
- Helps diagnose CHSH / entanglement shape artifacts before physics claims
"""
import argparse, csv, os, re, math
from collections import Counter, defaultdict

TIME_ALIASES = ["t","time","timestamp","t_unit","t_units","coinc_t","coinc_time","time_unit","time_units","coinc_idx","idx","index"]
ASET_ALIASES = ["a_set","alice_setting","setting_a","aset","a_setting","alice_set","sa","a_s"]
BSET_ALIASES = ["b_set","bob_setting","setting_b","bset","b_setting","bob_set","sb","b_s"]
AOUT_ALIASES = ["a_out","alice_outcome","outcome_a","aout","a_result","alice_result","oa","a_o"]
BOUT_ALIASES = ["b_out","bob_outcome","outcome_b","bout","b_result","bob_result","ob","b_o"]

def find_col(fieldnames, aliases):
    if not fieldnames:
        return None
    lower = {f.lower(): f for f in fieldnames}
    for a in aliases:
        if a.lower() in lower:
            return lower[a.lower()]
    # fallback contains match
    for f in fieldnames:
        fl = f.lower()
        for a in aliases:
            if a.lower() in fl:
                return f
    return None

def _clean(s):
    return str(s).strip()

def parse_set(v):
    s = _clean(v)
    if s == "":
        return None
    sl = s.lower()
    # direct
    if sl in ("0","1"):
        return int(sl)
    if sl in ("false","true"):
        return 1 if sl == "true" else 0
    # common tags
    if sl in ("a0","b0","s0","x","x0","h","left","l","zero"):
        return 0
    if sl in ("a1","b1","s1","y","x1","v","right","r","one"):
        return 1
    # try float
    try:
        fv = float(sl)
        if abs(fv - 0.0) < 1e-12:
            return 0
        if abs(fv - 1.0) < 1e-12:
            return 1
    except Exception:
        pass
    # regex: prefer terminal digit
    m = re.search(r'([01])\s*$', sl)
    if m:
        return int(m.group(1))
    # regex any isolated digit
    m = re.search(r'(?<!\d)([01])(?!\d)', sl)
    if m:
        return int(m.group(1))
    return None

def parse_out(v):
    s = _clean(v)
    if s == "":
        return None
    sl = s.lower()
    if sl in ("-1","+1","1","0"):
        if sl == "0":
            return -1
        return int(sl)
    if sl in ("false","true"):
        return 1 if sl == "true" else -1
    if sl in ("plus","+","p","pos","positive","up","u"):
        return +1
    if sl in ("minus","-","m","neg","negative","down","d"):
        return -1
    try:
        fv = float(sl)
        if abs(fv) < 1e-12:
            return -1
        if fv > 0:
            return +1
        if fv < 0:
            return -1
    except Exception:
        pass
    return None

def quantile_edges(vals, n_bins):
    vals_sorted = sorted(vals)
    m = len(vals_sorted)
    edges = []
    for i in range(n_bins + 1):
        if i == 0:
            edges.append(vals_sorted[0])
            continue
        if i == n_bins:
            edges.append(vals_sorted[-1])
            continue
        # nearest-rank style
        idx = int(round(i * (m - 1) / n_bins))
        edges.append(vals_sorted[idx])
    # make monotone strictly nondecreasing, handle duplicates naturally
    return edges

def linear_edges(vmin, vmax, n_bins):
    if n_bins <= 0:
        return [vmin, vmax]
    if vmax <= vmin:
        return [vmin] * n_bins + [vmax]
    step = (vmax - vmin) / n_bins
    return [vmin + i * step for i in range(n_bins)] + [vmax]

def log_edges(vmin_pos, vmax, n_bins):
    if vmin_pos <= 0 or vmax <= 0:
        raise ValueError("log_edges requires positive bounds")
    if vmax < vmin_pos:
        vmax = vmin_pos
    if n_bins <= 0:
        return [vmin_pos, vmax]
    if abs(vmax - vmin_pos) < 1e-15:
        return [vmin_pos] * n_bins + [vmax]
    l0 = math.log(vmin_pos)
    l1 = math.log(vmax)
    return [math.exp(l0 + (l1-l0)*i/n_bins) for i in range(n_bins)] + [vmax]

def assign_bin(x, edges):
    # returns [0, n_bins-1]
    n = len(edges) - 1
    if n <= 0:
        return 0
    if x <= edges[0]:
        return 0
    if x >= edges[-1]:
        return n - 1
    # binary search
    lo, hi = 0, n-1
    while lo <= hi:
        mid = (lo + hi) // 2
        if edges[mid] <= x < edges[mid+1]:
            return mid
        if x < edges[mid]:
            hi = mid - 1
        else:
            lo = mid + 1
    return n - 1

def chsh_from_rows(rows):
    # rows: list of (a_set,b_set,a_out,b_out)
    by_combo = {(0,0): [], (0,1): [], (1,0): [], (1,1): []}
    for a,b,ao,bo in rows:
        if (a,b) in by_combo:
            by_combo[(a,b)].append((ao,bo))
    Es = {}
    combo_counts = {}
    combo_out_counts = {}
    for c, obs in by_combo.items():
        npp = npm = nmp = nmm = 0
        for ao,bo in obs:
            if ao == 1 and bo == 1: npp += 1
            elif ao == 1 and bo == -1: npm += 1
            elif ao == -1 and bo == 1: nmp += 1
            elif ao == -1 and bo == -1: nmm += 1
        n = npp + npm + nmp + nmm
        combo_counts[c] = n
        combo_out_counts[c] = {"pp":npp,"pm":npm,"mp":nmp,"mm":nmm}
        if n > 0:
            Es[c] = (npp + nmm - npm - nmp) / n
        else:
            Es[c] = None
    if all(Es[c] is not None for c in [(0,0),(0,1),(1,0),(1,1)]):
        s_signed = Es[(0,0)] + Es[(0,1)] + Es[(1,0)] - Es[(1,1)]
        s_abs = abs(s_signed)
    else:
        s_signed = None
        s_abs = None
    return Es, combo_counts, combo_out_counts, s_signed, s_abs

def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--gap_bins", type=int, default=24)
    ap.add_argument("--log_gap_bins", action="store_true")
    ap.add_argument("--out_dir", default="out")
    ap.add_argument("--prefix", default="coinc_audit")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    summary_csv = os.path.join(args.out_dir, f"{args.prefix}_summary_v1.csv")
    setting_csv = os.path.join(args.out_dir, f"{args.prefix}_setting_counts_v1.csv")
    outcome_csv = os.path.join(args.out_dir, f"{args.prefix}_outcome_counts_v1.csv")
    gap_csv = os.path.join(args.out_dir, f"{args.prefix}_gap_setting_bins_v1.csv")
    debug_txt = os.path.join(args.out_dir, f"{args.prefix}_debug_v1.txt")

    rows_raw = []
    parse_stats = Counter()
    with open(args.in_csv, "r", encoding="utf-8", errors="replace", newline="") as f:
        rdr = csv.DictReader(f)
        fns = rdr.fieldnames or []
        t_col = find_col(fns, TIME_ALIASES)
        a_set_col = find_col(fns, ASET_ALIASES)
        b_set_col = find_col(fns, BSET_ALIASES)
        a_out_col = find_col(fns, AOUT_ALIASES)
        b_out_col = find_col(fns, BOUT_ALIASES)
        if not all([t_col,a_set_col,b_set_col,a_out_col,b_out_col]):
            missing = []
            if not t_col: missing.append("time")
            if not a_set_col: missing.append("a_set")
            if not b_set_col: missing.append("b_set")
            if not a_out_col: missing.append("a_out")
            if not b_out_col: missing.append("b_out")
            raise RuntimeError(f"Missing required columns (aliases not found): {', '.join(missing)}. Fieldnames={fns}")

        for i, r in enumerate(rdr):
            parse_stats["rows_total"] += 1
            try:
                t = float(str(r.get(t_col, "")).strip())
                if not math.isfinite(t):
                    raise ValueError("nonfinite t")
            except Exception:
                parse_stats["bad_t"] += 1
                continue
            a_set = parse_set(r.get(a_set_col, ""))
            b_set = parse_set(r.get(b_set_col, ""))
            a_out = parse_out(r.get(a_out_col, ""))
            b_out = parse_out(r.get(b_out_col, ""))
            if a_set is None: parse_stats["bad_a_set"] += 1
            if b_set is None: parse_stats["bad_b_set"] += 1
            if a_out is None: parse_stats["bad_a_out"] += 1
            if b_out is None: parse_stats["bad_b_out"] += 1
            if None in (a_set,b_set,a_out,b_out):
                parse_stats["rows_skipped_parse"] += 1
                continue
            rows_raw.append((t,a_set,b_set,a_out,b_out))
            parse_stats["rows_kept"] += 1

    # sort by time; compute gap-valid rows by current row with previous time
    rows_raw.sort(key=lambda x: x[0])
    rows_gap = []
    zero_gap = 0
    neg_gap = 0
    for i in range(1, len(rows_raw)):
        t_prev = rows_raw[i-1][0]
        t = rows_raw[i][0]
        gap = t - t_prev
        if gap < 0:
            neg_gap += 1
            continue
        if gap == 0:
            zero_gap += 1
        _, a_set, b_set, a_out, b_out = rows_raw[i]
        rows_gap.append((gap,a_set,b_set,a_out,b_out))

    # global counts (gap-valid rows)
    setting_counts = Counter((a,b) for _,a,b,_,_ in rows_gap)
    combo_rows = [(a,b,ao,bo) for _,a,b,ao,bo in rows_gap]
    Es, combo_counts, combo_out_counts, s_signed, s_abs = chsh_from_rows(combo_rows)

    # gap bins
    gaps = [g for g,_,_,_,_ in rows_gap]
    gap_mode_used = "none"
    edges = []
    if len(gaps) > 0:
        gmin = min(gaps); gmax = max(gaps)
        n_bins = max(4, int(args.gap_bins))
        if args.log_gap_bins:
            gpos = [g for g in gaps if g > 0]
            if len(gpos) >= max(10, n_bins):
                edges = log_edges(min(gpos), max(gpos), n_bins)
                gap_mode_used = "log"
            else:
                edges = quantile_edges(gaps, n_bins)
                gap_mode_used = "quantile_fallback_from_log"
        else:
            edges = linear_edges(gmin, gmax, n_bins)
            gap_mode_used = "linear"
        if not edges:
            edges = linear_edges(gmin, gmax, n_bins)
            gap_mode_used = "linear_fallback"
    else:
        gap_mode_used = "empty"

    # bin occupancy
    bin_counts_total = Counter()
    bin_counts_combo = defaultdict(Counter)  # bin -> combo count
    for g,a,b,ao,bo in rows_gap:
        if not edges:
            continue
        bi = assign_bin(g, edges)
        bin_counts_total[bi] += 1
        bin_counts_combo[bi][(a,b)] += 1

    # write setting counts
    setting_rows = []
    total_gap_valid = len(rows_gap)
    for a in [0,1]:
        for b in [0,1]:
            n = setting_counts.get((a,b), 0)
            frac = (n/total_gap_valid) if total_gap_valid else float("nan")
            setting_rows.append([f"{a}{b}", a, b, n, frac])
    write_csv(setting_csv, ["combo","a_set","b_set","count_gap_valid","fraction_gap_valid"], setting_rows)

    # write outcome counts per combo
    out_rows = []
    for a in [0,1]:
        for b in [0,1]:
            d = combo_out_counts.get((a,b), {"pp":0,"pm":0,"mp":0,"mm":0})
            n = combo_counts.get((a,b), 0)
            E = Es.get((a,b), None)
            out_rows.append([f"{a}{b}", a,b,n,d["pp"],d["pm"],d["mp"],d["mm"], "" if E is None else E])
    write_csv(outcome_csv, ["combo","a_set","b_set","N","N_pp","N_pm","N_mp","N_mm","E_ab"], out_rows)

    # write gap x setting occupancy
    gap_rows = []
    if edges:
        n_bins = len(edges) - 1
        for bi in range(n_bins):
            n = bin_counts_total.get(bi, 0)
            c00 = bin_counts_combo[bi].get((0,0),0)
            c01 = bin_counts_combo[bi].get((0,1),0)
            c10 = bin_counts_combo[bi].get((1,0),0)
            c11 = bin_counts_combo[bi].get((1,1),0)
            if n > 0:
                f00,f01,f10,f11 = c00/n, c01/n, c10/n, c11/n
            else:
                f00=f01=f10=f11=float("nan")
            gap_rows.append([bi, edges[bi], edges[bi+1], n, c00,c01,c10,c11, f00,f01,f10,f11])
    write_csv(gap_csv, ["bin_idx","gap_lo","gap_hi","N","c00","c01","c10","c11","f00","f01","f10","f11"], gap_rows)

    # summary
    n00 = combo_counts.get((0,0),0); n01 = combo_counts.get((0,1),0); n10 = combo_counts.get((1,0),0); n11 = combo_counts.get((1,1),0)
    min_combo = min([n00,n01,n10,n11]) if rows_gap else 0
    max_combo = max([n00,n01,n10,n11]) if rows_gap else 0
    imbalance_ratio = (min_combo/max_combo) if max_combo>0 else 0.0
    write_csv(summary_csv, [
        "in_csv","rows_total","rows_kept","rows_gap_valid","bad_t","bad_a_set","bad_b_set","bad_a_out","bad_b_out",
        "zero_gap","neg_gap","gap_min","gap_max","gap_bins_req","gap_bins_used","gap_mode_used",
        "n00","n01","n10","n11","min_over_max_combo_ratio",
        "E00","E01","E10","E11","S_signed","S_abs"
    ], [[
        args.in_csv,
        parse_stats.get("rows_total",0), parse_stats.get("rows_kept",0), len(rows_gap),
        parse_stats.get("bad_t",0), parse_stats.get("bad_a_set",0), parse_stats.get("bad_b_set",0),
        parse_stats.get("bad_a_out",0), parse_stats.get("bad_b_out",0),
        zero_gap, neg_gap,
        (min(gaps) if gaps else ""), (max(gaps) if gaps else ""),
        args.gap_bins, (len(edges)-1 if edges else 0), gap_mode_used,
        n00,n01,n10,n11,imbalance_ratio,
        (Es.get((0,0),"") if Es.get((0,0),None) is not None else ""),
        (Es.get((0,1),"") if Es.get((0,1),None) is not None else ""),
        (Es.get((1,0),"") if Es.get((1,0),None) is not None else ""),
        (Es.get((1,1),"") if Es.get((1,1),None) is not None else ""),
        (s_signed if s_signed is not None else ""),
        (s_abs if s_abs is not None else "")
    ]])

    # debug txt (human-readable)
    lines = []
    lines.append("=== COINCIDENCE CSV AUDIT (Bridge-E0 prep, NO FIT) ===")
    lines.append(f"in_csv={args.in_csv}")
    lines.append(f"detected_cols: time={t_col} a_set={a_set_col} b_set={b_set_col} a_out={a_out_col} b_out={b_out_col}")
    lines.append(f"rows_total={parse_stats.get('rows_total',0)} rows_kept={parse_stats.get('rows_kept',0)} rows_gap_valid={len(rows_gap)}")
    lines.append(f"parse_bad: bad_t={parse_stats.get('bad_t',0)} bad_a_set={parse_stats.get('bad_a_set',0)} bad_b_set={parse_stats.get('bad_b_set',0)} bad_a_out={parse_stats.get('bad_a_out',0)} bad_b_out={parse_stats.get('bad_b_out',0)} skipped={parse_stats.get('rows_skipped_parse',0)}")
    lines.append(f"gaps: zero_gap={zero_gap} neg_gap={neg_gap} min={min(gaps) if gaps else 'NA'} max={max(gaps) if gaps else 'NA'}")
    lines.append(f"gap_binning: req={args.gap_bins} used={(len(edges)-1 if edges else 0)} mode={gap_mode_used}")
    lines.append("")
    lines.append("setting_counts_gap_valid:")
    for a in [0,1]:
        for b in [0,1]:
            n = combo_counts.get((a,b), 0)
            frac = (n/len(rows_gap)) if rows_gap else 0.0
            lines.append(f"  n{a}{b}={n} ({frac:.6f})")
    lines.append(f"min_over_max_combo_ratio={imbalance_ratio:.6f}")
    if imbalance_ratio < 0.20:
        lines.append("WARNING: severe setting-combo imbalance detected (min/max < 0.20).")
    if imbalance_ratio < 0.05:
        lines.append("WARNING: extreme setting-combo imbalance detected (min/max < 0.05).")
    lines.append("")
    lines.append("outcome_counts_by_combo (pp,pm,mp,mm) and E_ab:")
    for a in [0,1]:
        for b in [0,1]:
            d = combo_out_counts.get((a,b), {"pp":0,"pm":0,"mp":0,"mm":0})
            E = Es.get((a,b), None)
            lines.append(f"  {a}{b}: pp={d['pp']} pm={d['pm']} mp={d['mp']} mm={d['mm']}  E={E if E is not None else 'NA'}")
    lines.append(f"global_CHSH: S_signed={s_signed if s_signed is not None else 'NA'} S_abs={s_abs if s_abs is not None else 'NA'}")
    lines.append("")
    lines.append("gap_bin_occupancy (first 40 bins max):")
    for bi, row in enumerate(gap_rows[:40]):
        _, glo, ghi, n, c00,c01,c10,c11, f00,f01,f10,f11 = row
        lines.append(f"  bin#{bi:02d} [{glo},{ghi}] N={n} | 00={c00} 01={c01} 10={c10} 11={c11} | f11={f11 if isinstance(f11,float) else 'NA'}")
    # bins with worst 11 occupancy
    if gap_rows:
        nonzero = [r for r in gap_rows if r[3] > 0]
        sorted_worst = sorted(nonzero, key=lambda r: (r[7], r[3]))  # c11 then N
        lines.append("")
        lines.append("worst_bins_by_c11 (up to 10):")
        for r in sorted_worst[:10]:
            bi, glo, ghi, n, c00,c01,c10,c11, f00,f01,f10,f11 = r
            lines.append(f"  bin#{bi:02d} N={n} c11={c11} f11={f11:.6f} edges=[{glo},{ghi}]")
    lines.append("")
    lines.append(f"OUT_SUMMARY={summary_csv}")
    lines.append(f"OUT_SETTING={setting_csv}")
    lines.append(f"OUT_OUTCOME={outcome_csv}")
    lines.append(f"OUT_GAPBINS={gap_csv}")

    with open(debug_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("=== COINCIDENCE CSV AUDIT (NO FIT) ===")
    print(f"IN_CSV      : {args.in_csv}")
    print(f"Rows        : total={parse_stats.get('rows_total',0)} kept={parse_stats.get('rows_kept',0)} gap_valid={len(rows_gap)}")
    if gaps:
        print(f"Gaps        : min={min(gaps)} max={max(gaps)} bins={len(edges)-1} mode={gap_mode_used}")
    print(f"Settings    : n00={n00} n01={n01} n10={n10} n11={n11}  min/max={imbalance_ratio:.6f}")
    if s_abs is not None:
        print(f"GLOBAL_CHSH : S_signed={s_signed:.9f}  |S|={s_abs:.9f}")
    else:
        print("GLOBAL_CHSH : unavailable (missing combo)")
    print(f"SUMMARY_CSV : {summary_csv}")
    print(f"SETTING_CSV : {setting_csv}")
    print(f"OUTCOME_CSV : {outcome_csv}")
    print(f"GAPBINS_CSV : {gap_csv}")
    print(f"DEBUG_TXT   : {debug_txt}")

if __name__ == "__main__":
    main()
