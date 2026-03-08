#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_evidence_bundle_terminology.py

Fails if the evidence bundle contains misleading wording that conflates
Integrity/Closure evidence with Performance_OK.

Default target bundle:
  INTEGRITY_CLOSURE_EVIDENCE_20260304/

Usage:
  python tools/check_evidence_bundle_terminology.py
  python tools/check_evidence_bundle_terminology.py --bundle INTEGRITY_CLOSURE_EVIDENCE_20260304
"""

from __future__ import annotations

import argparse
from pathlib import Path


FORBIDDEN_SUBSTRINGS = [
    "Performance Pass Bundle",
    "performance PASS",
    "a performance PASS",
    "is a performance PASS",
]


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".md", ".txt"}:
            yield path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--bundle",
        default="INTEGRITY_CLOSURE_EVIDENCE_20260304",
        help="Bundle folder to check (relative to repo root)",
    )
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    bundle_root = (repo_root / args.bundle).resolve()
    if not bundle_root.exists():
        raise SystemExit(f"Bundle folder not found: {bundle_root}")

    problems: list[str] = []
    for path in iter_text_files(bundle_root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            problems.append(f"{path}: unreadable ({exc})")
            continue

        lowered = text.lower()
        for needle in FORBIDDEN_SUBSTRINGS:
            if needle.lower() in lowered:
                problems.append(f"{path.relative_to(repo_root)}: contains forbidden phrase: {needle!r}")

    if problems:
        print("TERMINOLOGY CHECK FAILED")
        for p in problems:
            print("-", p)
        return 2

    print("OK: terminology check passed for", str(bundle_root.relative_to(repo_root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
