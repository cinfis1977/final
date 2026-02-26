import argparse, os, sys, csv
import itertools
import numpy as np

try:
    import h5py
except Exception as e:
    print('ERROR: h5py import failed:', e)
    sys.exit(1)


def find_dataset(h5, path_candidates):
    for p in path_candidates:
        if p in h5:
            return np.asarray(h5[p]), p
    return None, None


def list_attrs(obj):
    out = {}
    try:
        for k, v in obj.attrs.items():
            try:
                vv = v.tolist() if hasattr(v, 'tolist') else v
            except Exception:
                vv = str(v)
            out[str(k)] = str(vv)
    except Exception:
        pass
    return out


def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def combo_counts(a_set, b_set, mask=None):
    m = np.ones_like(a_set, dtype=bool) if mask is None else mask
    return {
        (0,0): int(np.sum(m & (a_set==0) & (b_set==0))),
        (0,1): int(np.sum(m & (a_set==0) & (b_set==1))),
        (1,0): int(np.sum(m & (a_set==1) & (b_set==0))),
        (1,1): int(np.sum(m & (a_set==1) & (b_set==1))),
    }


def combo_balance(counts):
    vals = list(counts.values())
    mx = max(vals) if vals else 0
    mn = min(vals) if vals else 0
    return float(mn)/float(mx) if mx>0 else 0.0


def chsh_from_rows(a_set, b_set, a_out, b_out, mask):
    S = 0.0
    varS = 0.0
    counts = {}
    ok = True
    for ai in (0,1):
        for bi in (0,1):
            mm = mask & (a_set==ai) & (b_set==bi)
            n = int(np.sum(mm))
            counts[f'n{ai}{bi}'] = n
            if n < 2:
                ok = False
                continue
            prod = (a_out[mm] * b_out[mm]).astype(np.int16)
            E = float(np.mean(prod))
            varE = float(max(0.0, 1.0 - E*E) / max(1, n-1))
            coeff = -1.0 if (ai==1 and bi==1) else 1.0
            S += coeff * E
            varS += varE
    sigS = float(np.sqrt(varS)) if varS>0 else 0.0
    return ok, S, sigS, counts


def observed_bits(vals):
    vals = np.asarray(vals)
    nz = vals[vals != 0]
    if nz.size == 0:
        return [], {}
    uu = nz.astype(np.uint64, copy=False)
    or_all = np.bitwise_or.reduce(uu)
    bits = [b for b in range(64) if ((int(or_all) >> b) & 1)]
    freq = {}
    for b in bits:
        mask = (uu & (np.uint64(1) << np.uint64(b))) != 0
        freq[b] = int(np.sum(mask))
    return bits, freq


def make_setting_decode_candidates(raw):
    raw = np.asarray(raw)
    ux = sorted(int(x) for x in np.unique(raw))
    cands = []

    def add(name, arr):
        try:
            out = np.asarray(arr, dtype=np.int8)
            if out.shape != raw.shape:
                return
            uu = np.unique(out)
            if set(int(x) for x in uu.tolist()) <= {0,1} and len(uu)==2:
                cands.append((name, out))
        except Exception:
            return

    if len(ux) == 2:
        lo, hi = ux
        add(f'sorted_unique[{lo},{hi}]', np.where(raw==lo,0,1))

    for v in ux[:16]:
        add(f'eq_{v}', (raw==v).astype(np.int8))
        add(f'gt_{v}', (raw>v).astype(np.int8))

    if ux and max(ux) <= (1<<20):
        rr = raw.astype(np.int64)
        for b in range(16):
            add(f'bit{b}', ((rr >> b) & 1).astype(np.int8))
        add('parity', (rr & 1).astype(np.int8))

    uniq = {}
    for name, arr in cands:
        key = arr.tobytes()
        if key not in uniq:
            uniq[key] = (name, arr)
    return list(uniq.values()), ux


def pick_best_setting_decode(a_raw, b_raw):
    a_cands, a_ux = make_setting_decode_candidates(a_raw)
    b_cands, b_ux = make_setting_decode_candidates(b_raw)
    rows = []
    best = None
    for an, aa in a_cands:
        for bn, bb in b_cands:
            cc = combo_counts(aa, bb)
            bal = combo_balance(cc)
            valid = 1 if min(cc.values()) > 0 else 0
            rows.append({
                'a_decode': an, 'b_decode': bn,
                'n00': cc[(0,0)], 'n01': cc[(0,1)], 'n10': cc[(1,0)], 'n11': cc[(1,1)],
                'bal': f'{bal:.9f}', 'valid': valid
            })
            key = (valid, bal)
            if best is None or key > best[0]:
                best = (key, an, bn, aa, bb, cc, bal)
    return {
        'a_unique': a_ux, 'b_unique': b_ux,
        'a_decode': best[1], 'b_decode': best[2],
        'a_set': best[3], 'b_set': best[4],
        'counts': best[5], 'bal': best[6],
        'ranking_rows': rows,
    }


def side_outcome_from_pair(click_vals, bit_lo, bit_hi):
    uu = click_vals.astype(np.uint64, copy=False)
    mlo = (uu & (np.uint64(1) << np.uint64(bit_lo))) != 0
    mhi = (uu & (np.uint64(1) << np.uint64(bit_hi))) != 0
    valid = np.logical_xor(mlo, mhi)
    out = np.zeros(click_vals.shape[0], dtype=np.int8)
    out[mlo & ~mhi] = -1
    out[mhi & ~mlo] = +1
    return valid, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--h5', required=True)
    ap.add_argument('--out_dir', default='out')
    ap.add_argument('--prefix', default='nist_h5bitpair_audit')
    ap.add_argument('--top_bits', type=int, default=12)
    ap.add_argument('--min_rows', type=int, default=200)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    pfx = os.path.join(args.out_dir, args.prefix)
    debug_lines = []

    with h5py.File(args.h5, 'r') as h5:
        a_click, a_click_path = find_dataset(h5, ['/alice/clicks', 'alice/clicks'])
        b_click, b_click_path = find_dataset(h5, ['/bob/clicks', 'bob/clicks'])
        a_set_raw, a_set_path = find_dataset(h5, ['/alice/settings', 'alice/settings'])
        b_set_raw, b_set_path = find_dataset(h5, ['/bob/settings', 'bob/settings'])
        if any(x is None for x in [a_click, b_click, a_set_raw, b_set_raw]):
            raise RuntimeError('Missing canonical datasets /alice|bob/{clicks,settings}')
        n = min(len(a_click), len(b_click), len(a_set_raw), len(b_set_raw))
        a_click = np.asarray(a_click[:n])
        b_click = np.asarray(b_click[:n])
        a_set_raw = np.asarray(a_set_raw[:n])
        b_set_raw = np.asarray(b_set_raw[:n])
        debug_lines.append('=== NIST HDF5 CLICK BITPAIR AUDIT (NO FIT) ===')
        debug_lines.append(f'H5={args.h5}')
        debug_lines.append(f'paths: a_click={a_click_path} b_click={b_click_path} a_set={a_set_path} b_set={b_set_path}')
        debug_lines.append(f'attrs[a_click]={list_attrs(h5[a_click_path])}')
        debug_lines.append(f'attrs[b_click]={list_attrs(h5[b_click_path])}')
        debug_lines.append(f'attrs[a_set]={list_attrs(h5[a_set_path])}')
        debug_lines.append(f'attrs[b_set]={list_attrs(h5[b_set_path])}')

    pick = pick_best_setting_decode(a_set_raw, b_set_raw)
    a_set = pick['a_set']; b_set = pick['b_set']
    setrank_csv = pfx + '_settings_decode_ranking_v1.csv'
    write_csv(setrank_csv, pick['ranking_rows'], ['a_decode','b_decode','n00','n01','n10','n11','bal','valid'])
    debug_lines.append(f"settings_raw_unique: alice={pick['a_unique'][:20]} bob={pick['b_unique'][:20]}")
    debug_lines.append(f"settings_pick: a={pick['a_decode']} b={pick['b_decode']} bal={pick['bal']:.9f} counts={pick['counts']}")

    both_nz = (a_click != 0) & (b_click != 0)
    a_bits, a_freq = observed_bits(a_click[both_nz])
    b_bits, b_freq = observed_bits(b_click[both_nz])
    a_bits_sorted = sorted(a_bits, key=lambda b: (-a_freq.get(b,0), b))
    b_bits_sorted = sorted(b_bits, key=lambda b: (-b_freq.get(b,0), b))
    a_bits_top = a_bits_sorted[:args.top_bits]
    b_bits_top = b_bits_sorted[:args.top_bits]

    debug_lines.append(f'rows_total={n} both_nonzero={int(np.sum(both_nz))}')
    debug_lines.append('alice_top_bits=' + ', '.join([f'b{b}:{a_freq[b]}' for b in a_bits_top]))
    debug_lines.append('bob_top_bits=' + ', '.join([f'b{b}:{b_freq[b]}' for b in b_bits_top]))

    bitfreq_rows = []
    for side, bits, freq in [('alice', a_bits_sorted, a_freq), ('bob', b_bits_sorted, b_freq)]:
        for rank, b in enumerate(bits, start=1):
            bitfreq_rows.append({'side':side, 'rank':rank, 'bit':b, 'count_nonzero_subset':freq[b]})
    bitfreq_csv = pfx + '_click_bitfreq_v1.csv'
    write_csv(bitfreq_csv, bitfreq_rows, ['side','rank','bit','count_nonzero_subset'])

    idx = np.where(both_nz)[0]
    a_click_nz = a_click[idx]
    b_click_nz = b_click[idx]
    a_set_nz = a_set[idx]
    b_set_nz = b_set[idx]

    pair_rows = []
    total_eval = 0
    for ab0, ab1 in itertools.combinations(a_bits_top, 2):
        a_valid, a_out = side_outcome_from_pair(a_click_nz, ab0, ab1)
        if int(np.sum(a_valid)) < args.min_rows:
            continue
        for bb0, bb1 in itertools.combinations(b_bits_top, 2):
            b_valid, b_out = side_outcome_from_pair(b_click_nz, bb0, bb1)
            m = a_valid & b_valid
            rows = int(np.sum(m))
            if rows < args.min_rows:
                continue
            cc = combo_counts(a_set_nz, b_set_nz, m)
            bal = combo_balance(cc)
            ok_chsh, S, sigS, _ = chsh_from_rows(a_set_nz, b_set_nz, a_out, b_out, m)
            pair_rows.append({
                'a_bits': f'{ab0},{ab1}', 'b_bits': f'{bb0},{bb1}', 'rows': rows,
                'bal': f'{bal:.9f}',
                'n00': cc[(0,0)], 'n01': cc[(0,1)], 'n10': cc[(1,0)], 'n11': cc[(1,1)],
                'all4': 1 if min(cc.values())>0 else 0,
                'S_chsh': f'{S:.9f}' if ok_chsh else '',
                'sigS': f'{sigS:.9f}' if ok_chsh else '',
                'snr': f'{(abs(S)/sigS):.6f}' if (ok_chsh and sigS>0) else '',
            })
            total_eval += 1

    pair_rows_sorted = sorted(pair_rows, key=lambda r: (int(r['all4']), float(r['bal']), int(r['rows'])), reverse=True)
    pair_csv = pfx + '_bitpair_ranking_v1.csv'
    write_csv(pair_csv, pair_rows_sorted, ['a_bits','b_bits','rows','bal','n00','n01','n10','n11','all4','S_chsh','sigS','snr'])

    summary = [{
        'rows_total': n,
        'rows_both_nonzero': int(np.sum(both_nz)),
        'settings_a_decode': pick['a_decode'],
        'settings_b_decode': pick['b_decode'],
        'settings_allrows_bal': f"{pick['bal']:.9f}",
        'a_bits_considered': ','.join(str(x) for x in a_bits_top),
        'b_bits_considered': ','.join(str(x) for x in b_bits_top),
        'pair_candidates_evaluated': total_eval,
        'top_pair_a_bits': pair_rows_sorted[0]['a_bits'] if pair_rows_sorted else '',
        'top_pair_b_bits': pair_rows_sorted[0]['b_bits'] if pair_rows_sorted else '',
        'top_pair_rows': pair_rows_sorted[0]['rows'] if pair_rows_sorted else '',
        'top_pair_bal': pair_rows_sorted[0]['bal'] if pair_rows_sorted else '',
    }]
    write_csv(pfx + '_summary_v1.csv', summary, list(summary[0].keys()))

    debug_lines.append(f'pair_candidates_evaluated={total_eval}')
    for r in pair_rows_sorted[:20]:
        debug_lines.append(
            f"TOP a_bits={r['a_bits']} b_bits={r['b_bits']} rows={r['rows']} bal={r['bal']} combos=({r['n00']},{r['n01']},{r['n10']},{r['n11']}) S={r['S_chsh']} sigS={r['sigS']}"
        )
    debug_path = pfx + '_debug_v1.txt'
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(debug_lines))

    print('=== NIST HDF5 CLICK BITPAIR AUDIT (NO FIT) ===')
    print(f'H5          : {args.h5}')
    print(f'Rows        : total={n} both_nonzero={int(np.sum(both_nz))}')
    print(f"SettingsPick: a={pick['a_decode']} b={pick['b_decode']}  all_rows_bal={pick['bal']:.9f}")
    print(f'Bits(top)   : alice={a_bits_top} bob={b_bits_top}')
    print(f'Pairs eval  : {total_eval}')
    if pair_rows_sorted:
        t = pair_rows_sorted[0]
        print(f"TOP_PAIR    : a_bits={t['a_bits']} b_bits={t['b_bits']} rows={t['rows']} bal={t['bal']} combos=({t['n00']},{t['n01']},{t['n10']},{t['n11']})")
    print(f'DEBUG_TXT   : {debug_path}')
    print(f'BITFREQ_CSV : {bitfreq_csv}')
    print(f'PAIR_CSV    : {pair_csv}')
    print(f'SETRANK_CSV : {setrank_csv}')


if __name__ == '__main__':
    main()
