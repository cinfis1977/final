#!/usr/bin/env python3
# nist_hdf5_inspect_and_export_coinc_bridgeE0_v1_2_1_DROPIN.py
# Real-data helper for Bridge-E0 entanglement prereg
# Purpose: build coincidence-level CSV expected by prereg_entanglement_memory_from_coinc_csv_v1_DROPIN.py
# Source: NIST Bell test processed_compressed HDF5 (.build.hdf5)
# No fitting. This is a plumbing/export tool.

import argparse, csv, os, sys, math, urllib.request, ssl
from typing import Any, Dict, List, Optional, Tuple

try:
    import h5py  # type: ignore
    import numpy as np  # type: ignore
except Exception as e:
    print("ERROR: Missing dependency. Install with: py -3 -m pip install h5py numpy", file=sys.stderr)
    print(f"DETAIL: {e}", file=sys.stderr)
    sys.exit(2)

NIST_HDF5_URLS = {
    # run4 after timing fix (biased RNG)
    '01_11': 'https://s3.amazonaws.com/nist-belltestdata/belldata/processed_compressed/hdf5/2015_09_18/01_11_CH_pockel_100kHz.run4.afterTimingfix.dat.compressed.build.hdf5',
    # run4 after timing fix 2 (mode-lock issue near end)
    '02_54': 'https://s3.amazonaws.com/nist-belltestdata/belldata/processed_compressed/hdf5/2015_09_18/02_54_CH_pockel_100kHz.run4.afterTimingfix2.dat.compressed.build.hdf5',
    # run4 after fixing mode locking (common choice)
    '03_43': 'https://s3.amazonaws.com/nist-belltestdata/belldata/processed_compressed/hdf5/2015_09_18/03_43_CH_pockel_100kHz.run4.afterTimingfix2_afterfixingModeLocking.dat.compressed.build.hdf5',
}


def norm(s: str) -> str:
    return ''.join(ch for ch in (s or '').lower() if ch.isalnum())


def ensure_parent(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def download_file(url: str, out_path: str, timeout: int = 60) -> None:
    ensure_parent(out_path)
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r, open(out_path, 'wb') as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def h5_dtype_str(ds: h5py.Dataset) -> str:
    try:
        return str(ds.dtype)
    except Exception:
        return 'unknown'


def summarize_numeric_sample(arr: np.ndarray) -> Dict[str, Any]:
    flat = arr.reshape(-1)
    if flat.size == 0:
        return {'n': 0}
    # sample to avoid huge scans
    step = max(1, flat.size // 20000)
    smp = flat[::step]
    out: Dict[str, Any] = {'n': int(flat.size), 'sample_n': int(smp.size)}
    try:
        if np.issubdtype(smp.dtype, np.number):
            finite = smp[np.isfinite(smp)] if np.issubdtype(smp.dtype, np.floating) else smp
            out['min'] = float(np.min(finite)) if finite.size else None
            out['max'] = float(np.max(finite)) if finite.size else None
            uniq = np.unique(smp[:5000])
            out['uniq_head'] = [int(x) if np.issubdtype(type(x), np.integer) or isinstance(x, (np.integer,)) else float(x) for x in uniq[:20]]
    except Exception:
        pass
    return out


def inspect_hdf5(path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    datasets: List[Dict[str, Any]] = []
    lines: List[str] = []
    with h5py.File(path, 'r') as h5:
        def visitor(name: str, obj: Any):
            if isinstance(obj, h5py.Dataset):
                info: Dict[str, Any] = {
                    'path': '/' + name,
                    'shape': tuple(int(x) for x in obj.shape),
                    'ndim': int(obj.ndim),
                    'dtype': h5_dtype_str(obj),
                }
                try:
                    if obj.ndim >= 1 and obj.size > 0:
                        # small sample read only
                        if obj.ndim == 1:
                            n = min(int(obj.shape[0]), 50000)
                            arr = obj[:n]
                        elif obj.ndim == 2:
                            r = min(int(obj.shape[0]), 20000)
                            c = min(int(obj.shape[1]), 8)
                            arr = obj[:r, :c]
                        else:
                            # skip large higher dims summary
                            arr = None
                        if arr is not None and hasattr(arr, 'dtype') and np.issubdtype(arr.dtype, np.number):
                            info.update(summarize_numeric_sample(np.asarray(arr)))
                except Exception as e:
                    info['sample_err'] = str(e)
                datasets.append(info)
        h5.visititems(visitor)
    # pretty lines
    for d in sorted(datasets, key=lambda x: x['path']):
        lines.append(f"{d['path']} | shape={d['shape']} | dtype={d['dtype']} | ndim={d['ndim']}")
        extras = []
        for k in ['n','sample_n','min','max','uniq_head','sample_err']:
            if k in d:
                extras.append(f"{k}={d[k]}")
        if extras:
            lines.append('  ' + ' ; '.join(extras))
    return datasets, lines


def _side_score(name_norm: str, side: str) -> int:
    s = 0
    if side == 'a':
        if 'alice' in name_norm: s += 4
        if name_norm.startswith('a') or 'a_' in name_norm or 'settinga' in name_norm or 'clicka' in name_norm: s += 2
        if 'deta' in name_norm: s += 2
    else:
        if 'bob' in name_norm: s += 4
        if name_norm.startswith('b') or 'b_' in name_norm or 'settingb' in name_norm or 'clickb' in name_norm: s += 2
        if 'detb' in name_norm: s += 2
    return s


def choose_paths(dsets: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Filter numeric datasets with row-like structure
    cand = []
    for d in dsets:
        if d.get('ndim') not in (1,2):
            continue
        dtype = str(d.get('dtype','')).lower()
        if not any(x in dtype for x in ['int','uint','float','bool']):
            continue
        cand.append(d)

    # helper scores
    for d in cand:
        nn = norm(d['path'])
        d['_norm'] = nn
        sh = d['shape']
        rows = sh[0] if len(sh)>=1 else 0
        cols = sh[1] if len(sh)>=2 else 1
        d['_rows'] = int(rows)
        d['_cols'] = int(cols)
        d['_nvals'] = int(rows*cols)
        minv = d.get('min', None); maxv = d.get('max', None)
        d['_looks_setting'] = False
        d['_looks_clickmask'] = False
        if minv is not None and maxv is not None:
            try:
                if float(minv) >= -0.5 and float(maxv) <= 3.5:
                    d['_looks_setting'] = True
                if float(minv) >= 0 and float(maxv) <= 65535 and float(maxv) >= 1:
                    d['_looks_clickmask'] = True
            except Exception:
                pass

    out: Dict[str, Any] = {'detected': {}}

    # Packed 1D settings byte candidate (NIST cw45-style bits 0..3)
    best_packed = None
    best_packed_score = -10**9
    for d in cand:
        if d['_cols'] != 1:
            continue
        nn = d['_norm']
        score = 0
        minv = d.get('min', None); maxv = d.get('max', None)
        if 'setting' in nn or 'rng' in nn:
            score += 8
        if 'click' in nn or 'det' in nn:
            score -= 6
        try:
            if minv is not None and maxv is not None:
                if float(minv) >= 0 and float(maxv) <= 15:
                    score += 12
                elif float(minv) >= 0 and float(maxv) <= 255:
                    score += 2
        except Exception:
            pass
        if score > best_packed_score:
            best_packed_score = score
            best_packed = d['path']
    if best_packed is not None and best_packed_score >= 12:
        out['detected']['settings_packed'] = best_packed

    # Combined 2-col candidates first
    combined_settings = []
    combined_clicks = []
    for d in cand:
        if d['_cols'] != 2:
            continue
        nn = d['_norm']
        score_set = 0
        score_clk = 0
        if d['_looks_setting']:
            score_set += 5
        if d['_looks_clickmask']:
            score_clk += 4
        if 'setting' in nn: score_set += 8
        if 'rng' in nn: score_set += 4
        if 'click' in nn or 'det' in nn: score_clk += 8
        combined_settings.append((score_set, d))
        combined_clicks.append((score_clk, d))
    combined_settings.sort(key=lambda t: (t[0], t[1]['_rows']), reverse=True)
    combined_clicks.sort(key=lambda t: (t[0], t[1]['_rows']), reverse=True)

    if combined_settings and combined_settings[0][0] >= 8:
        out['detected']['settings_combined'] = combined_settings[0][1]['path']
    if combined_clicks and combined_clicks[0][0] >= 8:
        out['detected']['clicks_combined'] = combined_clicks[0][1]['path']

    # Per-side fallbacks
    for kind in ('settings','clicks'):
        for side in ('a','b'):
            best = None
            best_score = -10**9
            for d in cand:
                if d['_cols'] != 1:
                    continue
                nn = d['_norm']
                score = d['_rows'] // 100000  # prefer longer arrays weakly
                score += _side_score(nn, side)
                if kind == 'settings':
                    if d['_looks_setting']:
                        score += 8
                    if 'setting' in nn or 'rng' in nn:
                        score += 8
                    if 'click' in nn or 'det' in nn:
                        score -= 4
                else:
                    if d['_looks_clickmask']:
                        score += 8
                    if 'click' in nn or 'det' in nn:
                        score += 8
                    if 'setting' in nn or 'rng' in nn:
                        score -= 4
                # Avoid obvious non-event arrays
                if any(x in nn for x in ['anom','skip','delay','offset','radius','block','count','numsync','pps','gps']):
                    score -= 3
                if score > best_score:
                    best_score = score
                    best = d['path']
            out['detected'][f'{kind}_{side}'] = best
            out['detected'][f'{kind}_{side}_score'] = best_score

    # Event index / sync index candidate
    best = None; best_score = -10**9
    for d in cand:
        if d['_cols'] != 1:
            continue
        nn = d['_norm']
        score = 0
        if any(k in nn for k in ['sync','event','index','idx','syncnum','syncnumber','syncindex']): score += 8
        if any(k in nn for k in ['click','det','setting','rng']): score -= 3
        if d['_rows'] > 100000: score += 2
        if score > best_score:
            best_score = score; best = d['path']
    out['detected']['index'] = best if best_score >= 5 else None
    out['detected']['index_score'] = best_score

    return out


def read_dataset(h5: h5py.File, path: str) -> np.ndarray:
    return np.asarray(h5[path])



def map_setting_array(arr: np.ndarray) -> np.ndarray:
    a = np.asarray(arr).reshape(-1)
    # bool -> int
    if a.dtype == np.bool_:
        return a.astype(np.uint8)

    out = np.full(a.shape[0], 255, dtype=np.uint8)

    # direct common encodings
    try:
        out[a == 0] = 0
        out[a == 1] = 1
    except Exception:
        pass

    # Small-sample unique probe
    try:
        probe = a[: min(a.size, 200000)]
        if np.issubdtype(probe.dtype, np.number):
            pf = probe.astype(np.float64)
            pf = pf[np.isfinite(pf)]
            uniq_probe = sorted(set(int(x) for x in pf if abs(x - round(x)) < 1e-9))
        else:
            uniq_probe = []
    except Exception:
        uniq_probe = []

    # known one-hot style alternatives
    if np.any(out == 255):
        us = set(uniq_probe)
        if us and us <= {1, 2}:
            out[a == 1] = 0
            out[a == 2] = 1
        elif us and us <= {2, 4}:
            out[a == 2] = 0
            out[a == 4] = 1
        elif us and us <= {4, 16}:
            out[a == 4] = 0
            out[a == 16] = 1
        elif us and us <= {8, 32}:
            out[a == 8] = 0
            out[a == 32] = 1

    # Generic two-code mapping fallback (most frequent two integer codes)
    if np.any(out == 255):
        try:
            if np.issubdtype(a.dtype, np.number):
                af = a.astype(np.float64)
                af = af[np.isfinite(af)]
                ai = af.astype(np.int64)
                if np.allclose(af, ai, atol=0, rtol=0) and ai.size > 0:
                    vals, cnts = np.unique(ai, return_counts=True)
                    order = np.argsort(cnts)[::-1]
                    top = [int(vals[i]) for i in order[:4]]
                    # prefer non-negative codes; if >2 present, choose the two most frequent
                    top2 = top[:2]
                    if len(top2) == 2:
                        c0, c1 = sorted(top2)
                        out[a == c0] = 0
                        out[a == c1] = 1
        except Exception:
            pass

    return out


def decode_packed_settings(arr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    v = np.asarray(arr).reshape(-1)
    try:
        vf = v.astype(np.float64)
    except Exception:
        raise SystemExit("Packed settings array is non-numeric.")
    if not np.all(np.isfinite(vf)):
        raise SystemExit("Packed settings array contains non-finite values.")
    vi = vf.astype(np.int64)
    if not np.allclose(vf, vi, atol=0, rtol=0):
        raise SystemExit("Packed settings array is non-integer.")
    vi = vi & 0xFF

    # NIST cw45 documented packed settings bits:
    # bit0 Alice setting0, bit1 Alice setting1, bit2 Bob setting0, bit3 Bob setting1
    a0 = (vi & 0x01) != 0
    a1 = (vi & 0x02) != 0
    b0 = (vi & 0x04) != 0
    b1 = (vi & 0x08) != 0

    a_set = np.full(vi.shape[0], 255, dtype=np.uint8)
    b_set = np.full(vi.shape[0], 255, dtype=np.uint8)

    a_set[a0 & (~a1)] = 0
    a_set[a1 & (~a0)] = 1
    b_set[b0 & (~b1)] = 0
    b_set[b1 & (~b0)] = 1
    return a_set, b_set




def score_decoded_settings(a_set: np.ndarray, b_set: np.ndarray) -> Dict[str, Any]:
    a = np.asarray(a_set).reshape(-1)
    b = np.asarray(b_set).reshape(-1)
    n = int(min(a.size, b.size))
    if n <= 0:
        return {'n': 0, 'valid_n': 0, 'valid_frac': 0.0, 'combo_counts': [0,0,0,0], 'balance': 0.0, 'score': -1e9}
    a = a[:n].astype(np.int64, copy=False)
    b = b[:n].astype(np.int64, copy=False)
    valid = ((a == 0) | (a == 1)) & ((b == 0) | (b == 1))
    valid_n = int(np.count_nonzero(valid))
    valid_frac = (valid_n / n) if n > 0 else 0.0
    cc = [0, 0, 0, 0]
    if valid_n > 0:
        av = a[valid]; bv = b[valid]
        # use bincount for 2-bit code 2*a+b in {0,1,2,3}
        code = (av << 1) | bv
        bc = np.bincount(code, minlength=4)
        cc = [int(bc[0]), int(bc[1]), int(bc[2]), int(bc[3])]
    mx = max(cc) if cc else 0
    mn = min(cc) if cc else 0
    balance = (mn / mx) if mx > 0 else 0.0
    nonzero = sum(1 for c in cc if c > 0)
    # Deterministic score: prioritize valid fraction strongly, then combo balance
    score = (1000.0 * valid_frac) + (50.0 * balance) + (5.0 if nonzero == 4 else 0.0)
    return {
        'n': n,
        'valid_n': valid_n,
        'valid_frac': float(valid_frac),
        'combo_counts': cc,
        'balance': float(balance),
        'nonzero_combos': int(nonzero),
        'score': float(score),
    }


def choose_and_decode_settings(h5: h5py.File, det: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, str, List[Dict[str, Any]]]:
    cands: List[Tuple[str, Any]] = []
    # deterministic order: combined, separate, packed (packed can be a false positive on some files)
    if det.get('settings_combined'):
        cands.append(('combined_Nx2', det.get('settings_combined')))
    if det.get('settings_a') and det.get('settings_b'):
        cands.append(('separate_A_B', (det.get('settings_a'), det.get('settings_b'))))
    if det.get('settings_packed'):
        cands.append(('packed_bits_0to3', det.get('settings_packed')))

    tried: List[Dict[str, Any]] = []
    best = None
    best_score = -1e18

    for mode, payload in cands:
        try:
            if mode == 'combined_Nx2':
                arr = read_dataset(h5, str(payload))
                if arr.ndim != 2 or arr.shape[1] < 2:
                    raise RuntimeError(f"not Nx2 shape={getattr(arr,'shape',None)}")
                a_set = map_setting_array(arr[:,0])
                b_set = map_setting_array(arr[:,1])
                src_desc = str(payload)
            elif mode == 'separate_A_B':
                pa, pb = payload
                a_set = map_setting_array(read_dataset(h5, str(pa)))
                b_set = map_setting_array(read_dataset(h5, str(pb)))
                src_desc = f"{pa} | {pb}"
            elif mode == 'packed_bits_0to3':
                parr = read_dataset(h5, str(payload))
                a_set, b_set = decode_packed_settings(parr)
                src_desc = str(payload)
            else:
                continue

            sc = score_decoded_settings(a_set, b_set)
            rec: Dict[str, Any] = {'mode': mode, 'source': src_desc}
            rec.update(sc)
            tried.append(rec)
            if sc['score'] > best_score:
                best_score = float(sc['score'])
                best = (a_set, b_set, mode, rec)
        except Exception as e:
            tried.append({'mode': mode, 'source': str(payload), 'error': str(e), 'score': -1e18})
            continue

    if best is None:
        raise SystemExit('Could not decode settings from autodetected paths. Run with --inspect_only and pass explicit --settings_* paths.')

    a_best, b_best, mode_best, rec_best = best
    # Safety rail: if best valid fraction is still terrible, abort loudly.
    if float(rec_best.get('valid_frac', 0.0)) < 0.05:
        raise SystemExit(f"Decoded settings look invalid (valid_frac={rec_best.get('valid_frac'):.6f}) for all candidates. Inspect DEBUG_TXT and SCHEMA_TXT and override paths.")
    # include compact score hint in mode string
    mode_label = f"{mode_best} (valid={rec_best.get('valid_frac',0.0):.3f}, bal={rec_best.get('balance',0.0):.3f})"
    return np.asarray(a_best), np.asarray(b_best), mode_label, tried

def first_set_bit_slot(mask: int) -> int:
    # 1..16, returns 0 if no click
    if mask <= 0:
        return 0
    m = int(mask) & 0xFFFF
    if m == 0:
        return 0
    slot = 1
    while slot <= 16:
        if m & 1:
            return slot
        m >>= 1
        slot += 1
    return 0


def outcome_from_slot(slot: int, mode: str) -> int:
    if slot <= 0:
        return 0
    if mode == 'half':
        return -1 if slot <= 8 else +1
    if mode == 'parity':
        return -1 if (slot % 2 == 1) else +1
    # center split around 8.5 (same as half for integer slots, kept for explicitness)
    return -1 if slot <= 8 else +1


def coinc_selector_from_index(idx_arr: Optional[np.ndarray], n_aligned: int) -> Tuple[np.ndarray, str]:
    """Interpret idx_arr as coincidence-row selector when valid; else use legacy first-N rows."""
    if idx_arr is None:
        return np.arange(n_aligned, dtype=np.int64), 'legacy_no_index'

    arr = np.asarray(idx_arr).reshape(-1)
    if arr.size == 0:
        return np.arange(0, dtype=np.int64), 'legacy_empty_index'
    try:
        arrf = arr.astype(np.float64)
    except Exception:
        n = min(int(arr.size), int(n_aligned))
        return np.arange(n, dtype=np.int64), 'legacy_non_numeric_index'
    if not np.all(np.isfinite(arrf)):
        n = min(int(arr.size), int(n_aligned))
        return np.arange(n, dtype=np.int64), 'legacy_nonfinite_index'
    arri = arrf.astype(np.int64)
    if not np.allclose(arrf, arri, atol=0, rtol=0):
        n = min(int(arr.size), int(n_aligned))
        return np.arange(n, dtype=np.int64), 'legacy_nonint_index'

    if arri.min() >= 0 and arri.max() < n_aligned:
        return arri, 'coinc_index_zero_based'
    if arri.min() >= 1 and arri.max() <= n_aligned:
        return (arri - 1), 'coinc_index_one_based'

    n = min(int(arri.size), int(n_aligned))
    return np.arange(n, dtype=np.int64), 'legacy_index_out_of_range'


def main() -> None:
    ap = argparse.ArgumentParser(description='Inspect NIST processed HDF5 and export Bridge-E0 coincidence CSV (no fit).')
    ap.add_argument('--hdf5_path', default=r'data\nist\03_43_run4_afterfixingModeLocking.build.hdf5')
    ap.add_argument('--download_run', default='', choices=['', '01_11', '02_54', '03_43'])
    ap.add_argument('--force_redownload', action='store_true')
    ap.add_argument('--inspect_only', action='store_true')
    ap.add_argument('--schema_txt', default=r'out\nist_hdf5_schema_v1.txt')
    ap.add_argument('--debug_txt', default=r'out\nist_hdf5_export_debug_v1.txt')
    ap.add_argument('--out_csv', default=r'out\nist_run4_coincidences.csv')
    ap.add_argument('--coinc_only', action='store_true', help='Keep only rows where both sides have a click (default True in wrapper).')
    ap.add_argument('--outcome_mode', default='half', choices=['half','parity'], help='Map click slot to ±1. half=slots1-8->-1, 9-16->+1')
    # optional explicit overrides if autodetect is wrong
    ap.add_argument('--settings_path', default='')
    ap.add_argument('--settings_packed_path', default='')
    ap.add_argument('--clicks_path', default='')
    ap.add_argument('--a_settings_path', default='')
    ap.add_argument('--b_settings_path', default='')
    ap.add_argument('--a_clicks_path', default='')
    ap.add_argument('--b_clicks_path', default='')
    ap.add_argument('--index_path', default='')
    args = ap.parse_args()

    if args.download_run:
        url = NIST_HDF5_URLS[args.download_run]
        if args.force_redownload or (not os.path.exists(args.hdf5_path)):
            print(f'Downloading NIST processed HDF5 ({args.download_run}) -> {args.hdf5_path}')
            try:
                download_file(url, args.hdf5_path)
            except Exception as e:
                raise SystemExit(f'Failed to download HDF5 from NIST S3: {e}')

    if not os.path.exists(args.hdf5_path):
        raise SystemExit(f'HDF5 file not found: {args.hdf5_path}')

    print(f'Inspecting HDF5 schema: {args.hdf5_path}')
    dsets, schema_lines = inspect_hdf5(args.hdf5_path)
    ensure_parent(args.schema_txt)
    with open(args.schema_txt, 'w', encoding='utf-8') as f:
        f.write('=== NIST HDF5 SCHEMA INSPECTION (Bridge-E0 helper) ===\n')
        f.write(f'HDF5={args.hdf5_path}\n')
        f.write(f'Datasets={len(dsets)}\n\n')
        for ln in schema_lines:
            f.write(ln + '\n')
    print(f'SCHEMA_TXT = {args.schema_txt}')

    if args.inspect_only:
        print('inspect_only=True -> stopping before export.')
        return

    chosen = choose_paths(dsets)
    det = dict(chosen.get('detected', {}))

    # explicit overrides
    if args.settings_path:
        det['settings_combined'] = args.settings_path
    if args.settings_packed_path:
        det['settings_packed'] = args.settings_packed_path
    if args.clicks_path:
        det['clicks_combined'] = args.clicks_path
    for k_arg, k_det in [
        ('a_settings_path','settings_a'), ('b_settings_path','settings_b'),
        ('a_clicks_path','clicks_a'), ('b_clicks_path','clicks_b'), ('index_path','index')
    ]:
        v = getattr(args, k_arg)
        if v:
            det[k_det] = v

    with h5py.File(args.hdf5_path, 'r') as h5:
        # settings (adaptive, deterministic sanity-checked selection among decoded candidates)
        a_set, b_set, settings_decode_mode, settings_decode_trials = choose_and_decode_settings(h5, det)

        # clicks
        if det.get('clicks_combined'):
            carr = read_dataset(h5, det['clicks_combined'])
            if carr.ndim != 2 or carr.shape[1] < 2:
                raise SystemExit(f"clicks_combined is not Nx2: {det['clicks_combined']} shape={carr.shape}")
            a_click = np.asarray(carr[:,0]).reshape(-1)
            b_click = np.asarray(carr[:,1]).reshape(-1)
        else:
            if not det.get('clicks_a') or not det.get('clicks_b'):
                raise SystemExit('Could not auto-detect click arrays. Run with --inspect_only and pass --a_clicks_path / --b_clicks_path')
            a_click = np.asarray(read_dataset(h5, det['clicks_a'])).reshape(-1)
            b_click = np.asarray(read_dataset(h5, det['clicks_b'])).reshape(-1)

        # index (optional)
        idx_arr = None
        if det.get('index'):
            try:
                idx_arr = np.asarray(read_dataset(h5, det['index'])).reshape(-1)
            except Exception:
                idx_arr = None

    # Align full event arrays first, then select coincidence rows via idx_arr if it is a valid selector.
    n_aligned = min(len(a_set), len(b_set), len(a_click), len(b_click))
    if n_aligned < 1000:
        raise SystemExit(f'Too few aligned events in detected arrays: n_aligned={n_aligned}. Check schema and override dataset paths.')

    a_set = np.asarray(a_set[:n_aligned], dtype=np.uint8)
    b_set = np.asarray(b_set[:n_aligned], dtype=np.uint8)
    a_click = np.asarray(a_click[:n_aligned], dtype=np.int64)
    b_click = np.asarray(b_click[:n_aligned], dtype=np.int64)

    selector, selector_mode = coinc_selector_from_index(idx_arr, n_aligned)
    n = int(selector.size)
    if n < 1000:
        raise SystemExit(f'Too few selected rows after index interpretation: n={n}. selector_mode={selector_mode}')

    a_set = a_set[selector]
    b_set = b_set[selector]
    a_click = a_click[selector]
    b_click = b_click[selector]
    idx_arr = selector.astype(np.int64, copy=False)
    idx_source = ('generated_row_index' if selector_mode.startswith('legacy_no_index') else det.get('index', 'unknown'))

    # Build rows
    ensure_parent(args.out_csv)
    ensure_parent(args.debug_txt)

    bad_setting = 0
    kept = 0
    both_click = 0
    with open(args.out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['coinc_idx','a_set','b_set','a_out','b_out','a_clickmask','b_clickmask','a_slot','b_slot'])
        for i in range(n):
            asv = int(a_set[i]); bsv = int(b_set[i])
            if asv not in (0,1) or bsv not in (0,1):
                bad_setting += 1
                continue
            am = int(a_click[i]) & 0xFFFF
            bm = int(b_click[i]) & 0xFFFF
            a_slot = first_set_bit_slot(am)
            b_slot = first_set_bit_slot(bm)
            if am != 0 and bm != 0:
                both_click += 1
            if args.coinc_only and not (am != 0 and bm != 0):
                continue
            a_out = outcome_from_slot(a_slot, args.outcome_mode)
            b_out = outcome_from_slot(b_slot, args.outcome_mode)
            # If coinc_only=False and no-click exists, outcome 0 rows are skipped because prereg expects ±1; keep only valid outcomes
            if a_out not in (-1, +1) or b_out not in (-1, +1):
                continue
            w.writerow([int(idx_arr[i]), asv, bsv, a_out, b_out, am, bm, a_slot, b_slot])
            kept += 1

    # quick summaries
    with open(args.debug_txt, 'w', encoding='utf-8') as f:
        f.write('=== NIST HDF5 -> Bridge-E0 coincidence CSV export debug ===\n')
        f.write(f'hdf5_path={args.hdf5_path}\n')
        f.write(f'schema_txt={args.schema_txt}\n')
        f.write(f'out_csv={args.out_csv}\n')
        f.write(f'coinc_only={args.coinc_only}\n')
        f.write(f'outcome_mode={args.outcome_mode}\n')
        f.write(f'idx_source={idx_source}\n')
        f.write('--- autodetect ---\n')
        for k in sorted(det.keys()):
            f.write(f'{k}={det[k]}\n')
        f.write(f'settings_decode_mode={settings_decode_mode}\n')
        f.write('settings_decode_trials:\n')
        try:
            for _rec in settings_decode_trials:
                f.write(f"  {_rec}\n")
        except Exception:
            pass
        f.write('--- counts ---\n')
        f.write(f'n_aligned={n_aligned}\n')
        f.write(f'selected_rows={n}\n')
        f.write(f'selector_mode={selector_mode}\n')
        f.write(f'bad_setting_rows={bad_setting}\n')
        f.write(f'both_click_rows={both_click}\n')
        f.write(f'exported_rows={kept}\n')
        f.write('--- caveat ---\n')
        f.write('Outcome mapping is protocol-convention dependent. Default outcome_mode=half maps click-slot 1..8 -> -1 and 9..16 -> +1.\n')
        f.write('This is a deterministic no-fit mapping for Bridge-E0 plumbing; if your NIST analysis pipeline defines a different ±1 mapping, use that export instead.\n')

    print('=== NIST HDF5 -> Bridge-E0 coincidence CSV export (NO FIT) ===')
    print(f'HDF5       : {args.hdf5_path}')
    print(f'SCHEMA_TXT : {args.schema_txt}')
    print(f'DEBUG_TXT  : {args.debug_txt}')
    print(f'OUT_CSV    : {args.out_csv}')
    print(f'Rows       : exported={kept}  both_click_total={both_click}  selected={n}  aligned={n_aligned}')
    print(f'SettingDec : {settings_decode_mode}')
    print(f'Selector   : {selector_mode}  idx_source={idx_source}')
    try:
        cc = {'n00':0,'n01':0,'n10':0,'n11':0}
        with open(args.out_csv, 'r', encoding='utf-8', errors='replace') as _f:
            next(_f, None)
            for _ln in _f:
                p = _ln.strip().split(',')
                if len(p) >= 3:
                    k = f"n{p[1]}{p[2]}"
                    if k in cc:
                        cc[k] += 1
        print(f"Combos     : n00={cc['n00']} n01={cc['n01']} n10={cc['n10']} n11={cc['n11']}")
        vals = [cc['n00'], cc['n01'], cc['n10'], cc['n11']]
        mx = max(vals) if vals else 0
        mn = min(vals) if vals else 0
        if mx > 0:
            ratio = mn / mx
            print(f'ComboBal   : min/max={ratio:.6f}')
            if ratio < 0.25:
                print('WARNING    : Severe setting-combo imbalance detected. This usually means wrong settings decode and/or missing coincidence selector/index. Inspect DEBUG_TXT autodetect paths and SCHEMA_TXT.')
    except Exception:
        pass
    print(f'OutcomeMap : {args.outcome_mode} (slot 1..8 -> -1, 9..16 -> +1 for half)')
    print('Next step  : run Bridge-E0 prereg on OUT_CSV')


if __name__ == '__main__':
    main()
