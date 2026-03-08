#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST raw .dat reader (timetagger events) — DROP-IN v1

What we learned
---------------
Your alice_03_43.zip and bob_03_43.zip each contain exactly one huge *.dat file.

NIST's own "Bell Test Data File Folder Descriptions" document describes the RAW timetagger format as
a stream of 8-byte unsigned integers:
  (1) channel id (8 bytes, uint64)
  (2) raw timetag  (8 bytes, uint64)  -- each bin is 78.125 ps (12.8 GHz clock)
  (3) transfer number (8 bytes, uint64)

So each event record is 24 bytes, little-endian uint64s. This matches your hex preview:
  06 00 00 00 00 00 00 00  -> channel=6 (sync)
  <8 bytes>                -> timetag
  00..00                   -> transfer=0
  04 00 00 00 00 00 00 00  -> next record channel=4 ...

Channel mapping in stored data (0-based) per the same doc:
  0: Detector click
  2: RNG output 0
  4: RNG output 1
  5: GPS PPS
  6: Sync

What this script does
---------------------
- Streams through the .dat (either directly or inside a .zip) and parses records as <QQQ.
- Prints:
    total records processed
    unique channels seen
    counts per channel
    min/max timetag per channel
    min/max transfer number (overall)
- Optionally writes the first N records to a small CSV for inspection.

Usage (PowerShell)
------------------
# 1) Quick summary from zip (fast, limited records)
py -3 .\CODE\nist_raw_dat_reader_v1_DROPIN.py `
  --zip_path ".\data\nist_raw_03_43\alice_03_43.zip" `
  --max_records 2000000

# 2) Write first 200k records to CSV
py -3 .\CODE\nist_raw_dat_reader_v1_DROPIN.py `
  --zip_path ".\data\nist_raw_03_43\alice_03_43.zip" `
  --max_records 200000 `
  --out_csv ".\out\alice_03_43_head200k.csv"

If you have an extracted .dat instead:
  --dat_path "...\alice.dat"

Notes
-----
- This is a READER/probe. It does NOT attempt to build trials yet.
- Next step after this: build a sync-indexed trial table (setting + click/no-click)
  without post-selecting "both clicked", so Bell statistics are meaningful.
"""
from __future__ import annotations

import argparse
import os
import zipfile
import numpy as np
import pandas as pd

REC_BYTES = 24  # 3 * uint64

def _open_stream(args):
    """
    Returns (stream, total_uncompressed_bytes, label)
    stream must support .read().
    """
    if args.dat_path:
        p = args.dat_path
        if not os.path.exists(p):
            raise SystemExit(f"dat not found: {p}")
        return open(p, "rb"), os.path.getsize(p), p

    if args.zip_path:
        zp = args.zip_path
        if not os.path.exists(zp):
            raise SystemExit(f"zip not found: {zp}")
        z = zipfile.ZipFile(zp, "r")
        members = [m for m in z.namelist() if not m.endswith("/")]
        if args.member:
            if args.member not in members:
                raise SystemExit(f"member not found in zip: {args.member}")
            mem = args.member
        else:
            # pick the largest member
            infos = sorted((z.getinfo(m) for m in members), key=lambda i: i.file_size, reverse=True)
            mem = infos[0].filename if infos else None
            if not mem:
                raise SystemExit("zip is empty")
        info = z.getinfo(mem)
        # ZipExtFile will be closed when z is closed; keep z alive via closure
        stream = z.open(mem, "r")
        stream._zipfile_ref = z  # keep reference
        return stream, int(info.file_size), f"{zp}::{mem}"

    raise SystemExit("Provide either --dat_path or --zip_path")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip_path", default="")
    ap.add_argument("--dat_path", default="")
    ap.add_argument("--member", default="", help="zip member name (optional). Default: largest member")
    ap.add_argument("--max_records", type=int, default=0, help="0 means read entire file (can be huge)")
    ap.add_argument("--chunk_records", type=int, default=2_000_000)
    ap.add_argument("--out_csv", default="", help="write first N records (controlled by --max_records) to CSV")
    args = ap.parse_args()

    stream, total_bytes, label = _open_stream(args)
    member = args.member if args.member else ""
    try:
        # Counters
        chan_counts = {}
        chan_min_t = {}
        chan_max_t = {}
        min_transfer = None
        max_transfer = None

        # For optional CSV output
        write_csv = bool(args.out_csv)
        csv_rows = []

        max_rec = int(args.max_records) if args.max_records else None
        chunk_rec = int(args.chunk_records)
        chunk_bytes = chunk_rec * REC_BYTES

        read_records = 0
        while True:
            if max_rec is not None and read_records >= max_rec:
                break

            # Limit read for last chunk if max_rec is set
            if max_rec is not None:
                remaining = max_rec - read_records
                want = min(chunk_rec, remaining)
                data = stream.read(want * REC_BYTES)
            else:
                data = stream.read(chunk_bytes)

            if not data:
                break

            # Trim to full records
            rem = len(data) % REC_BYTES
            if rem:
                data = data[:-rem]
            if not data:
                break

            arr = np.frombuffer(data, dtype="<u8").reshape(-1, 3)
            ch = arr[:, 0]
            tt = arr[:, 1]
            tr = arr[:, 2]

            # transfer min/max
            tmin = int(tr.min())
            tmax = int(tr.max())
            min_transfer = tmin if min_transfer is None else min(min_transfer, tmin)
            max_transfer = tmax if max_transfer is None else max(max_transfer, tmax)

            # channel stats
            for u in np.unique(ch):
                u_int = int(u)
                mask = (ch == u)
                cnt = int(mask.sum())
                chan_counts[u_int] = chan_counts.get(u_int, 0) + cnt
                tmin_u = int(tt[mask].min())
                tmax_u = int(tt[mask].max())
                chan_min_t[u_int] = tmin_u if u_int not in chan_min_t else min(chan_min_t[u_int], tmin_u)
                chan_max_t[u_int] = tmax_u if u_int not in chan_max_t else max(chan_max_t[u_int], tmax_u)

            # optional CSV rows (only from beginning, up to max_records)
            if write_csv:
                # only store up to max_records, which must be set in that case to keep file small
                take = arr
                for r in take:
                    csv_rows.append((int(r[0]), int(r[1]), int(r[2])))
                # keep memory bounded if user accidentally sets max_records huge
                if len(csv_rows) > 5_000_000:
                    raise SystemExit("Refusing to hold >5,000,000 rows in memory. Reduce --max_records.")

            read_records += arr.shape[0]

        print("=== NIST RAW DAT READER v1 ===")
        print("source:", label)
        print("total_uncompressed_bytes:", total_bytes)
        print("records_read:", read_records)
        chans = sorted(chan_counts.keys())
        print("unique_channels:", chans)
        print("channel_counts:", {k: chan_counts[k] for k in chans})
        print("timetag_min_max_by_channel:", {k: (chan_min_t[k], chan_max_t[k]) for k in chans})
        print("transfer_min_max:", (min_transfer, max_transfer))

        if write_csv:
            if not args.max_records:
                raise SystemExit("--out_csv requires --max_records (to keep output bounded).")
            os.makedirs(os.path.dirname(os.path.abspath(args.out_csv)) or ".", exist_ok=True)
            df = pd.DataFrame(csv_rows, columns=["channel", "timetag", "transfer"])
            df.to_csv(args.out_csv, index=False)
            print("[OK] wrote:", args.out_csv)

    finally:
        try:
            stream.close()
        except Exception:
            pass
        # close zip if present
        z = getattr(stream, "_zipfile_ref", None)
        if z is not None:
            try:
                z.close()
            except Exception:
                pass

if __name__ == "__main__":
    main()
