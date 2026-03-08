#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIST raw ZIP probe — DROP-IN v1

What it does
------------
Given one or more .zip files, this prints:
- a sorted inventory (member name, uncompressed size, extension)
- a short "signature" for each member (magic bytes / likely type)
- for the top-N largest members: a hex preview of the first 32 bytes + a quick "textiness" score

Why
---
Your alice/bob zips did not contain parseable csv/tsv/txt/npy/npz/h5 directly, so we need to
identify the actual internal format before writing a correct trial builder (with outcomes).

Usage (PowerShell)
------------------
py -3 .\CODE\nist_zip_probe_v1_DROPIN.py `
  --zips ".\data\nist_raw_03_43\alice_03_43.zip" ".\data\nist_raw_03_43\bob_03_43.zip" `
  --top 30 `
  --preview 16
"""
from __future__ import annotations

import argparse
import os
import zipfile
from dataclasses import dataclass
from typing import List, Tuple, Optional

def ext(name: str) -> str:
    return os.path.splitext(name.lower())[1]

def magic_kind(b: bytes) -> str:
    if b.startswith(b"\x1f\x8b"):
        return "gzip"
    if b.startswith(b"\x42\x5a\x68"):
        return "bzip2"
    if b.startswith(b"\x28\xb5\x2f\xfd"):
        return "zstd"
    if b.startswith(b"\x04\x22\x4d\x18"):
        return "lz4"
    if b.startswith(b"\xfd\x37\x7a\x58\x5a\x00"):
        return "xz"
    if b.startswith(b"\x89HDF\r\n\x1a\n"):
        return "hdf5"
    if b.startswith(b"\x93NUMPY"):
        return "npy"
    if b.startswith(b"PK\x03\x04"):
        return "zip"
    # simple text sniff
    if all((c in b"\t\r\n\f\b" or 32 <= c <= 126) for c in b[:64]):
        return "ascii-ish"
    return "binary/unknown"

def textiness(b: bytes) -> float:
    if not b:
        return 0.0
    good = 0
    for c in b:
        if c in (9,10,13) or 32 <= c <= 126:
            good += 1
    return good / len(b)

@dataclass
class Member:
    name: str
    size: int
    ext: str
    kind: str

def probe_zip(path: str, top: int, preview: int) -> None:
    print("\n=== ZIP:", path, "===")
    with zipfile.ZipFile(path, "r") as z:
        members: List[Member] = []
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            size = int(info.file_size)
            with z.open(info, "r") as f:
                head = f.read(64)
            members.append(Member(name=name, size=size, ext=ext(name), kind=magic_kind(head)))

        members.sort(key=lambda m: m.size, reverse=True)

        print(f"Members: {len(members)}")
        print("Top by size:")
        for m in members[:top]:
            print(f"  {m.size:12d}  {m.kind:12s}  {m.ext:6s}  {m.name}")

        # preview a few
        print(f"\nHex preview (first 32 bytes) for top {min(preview, len(members))}:")
        for m in members[:preview]:
            with z.open(m.name, "r") as f:
                head = f.read(32)
            hx = head.hex()
            tx = textiness(head)
            print(f"- {m.name}  size={m.size}  kind={m.kind}  textiness={tx:.2f}")
            print(f"  {hx}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zips", nargs="+", required=True)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--preview", type=int, default=16)
    args = ap.parse_args()

    for zp in args.zips:
        if not os.path.exists(zp):
            raise SystemExit(f"zip not found: {zp}")
        probe_zip(zp, top=args.top, preview=args.preview)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
