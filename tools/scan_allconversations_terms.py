#!/usr/bin/env python3
"""Scan paper/allconversations.txt for specified profanity/insult terms.

This is a reporting tool: it does NOT modify files and it does NOT print matched
line text; only counts and line numbers.

Default patterns are tuned to avoid common false positives (e.g. "eksik" for
"sik" and "siklo-" scientific stems like "siklotron").
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Stat:
    line_hits: int = 0
    match_hits: int = 0
    first_lines: list[int] | None = None

    def __post_init__(self) -> None:
        if self.first_lines is None:
            self.first_lines = []


def _default_patterns() -> list[tuple[str, str, int]]:
    """Return (name, regex, flags)."""
    return [
        (
            "amk (a.m.k variants)",
            r"(?i)(?<!\w)a\s*\.?\s*m\s*\.?\s*k(?!\w)",
            0,
        ),
        (
            "mk (word)",
            r"(?i)(?<!\w)mk(?!\w)",
            0,
        ),
        (
            "orospu*",
            r"(?i)\borospu\w*",
            0,
        ),
        (
            "orospu çocu* (approx)",
            r"(?i)\borospu\s*çocu\w*|\borospuçocu\w*",
            0,
        ),
        (
            "lan (word)",
            r"(?i)(?<!\w)lan(?!\w)",
            0,
        ),
        (
            "sik* (exclude siklo-)",
            r"(?<!\w)[sS][iİ][kK](?![lL][oO])\w*",
            0,
        ),
        (
            "sikik*",
            r"(?<!\w)[sS][iİ][kK][iİ][kK]\w*",
            0,
        ),
        (
            "fking (word)",
            r"(?i)(?<!\w)fking(?!\w)",
            0,
        ),
        (
            "fucking/fuck*",
            r"(?i)\bfuck\w*",
            0,
        ),
        (
            "motherfucker*",
            r"(?i)\bmotherfucker\w*",
            0,
        ),
    ]


def scan_file(path: Path, patterns: list[tuple[str, str, int]], *, first_n: int) -> list[tuple[str, Stat]]:
    compiled: list[tuple[str, re.Pattern[str], Stat]] = []
    for name, rx, flags in patterns:
        compiled.append((name, re.compile(rx, flags), Stat()))

    with path.open("r", encoding="utf-8", errors="surrogateescape") as f:
        for line_no, line in enumerate(f, start=1):
            for _, pat, stat in compiled:
                matches = list(pat.finditer(line))
                if not matches:
                    continue
                stat.line_hits += 1
                stat.match_hits += len(matches)
                if len(stat.first_lines) < first_n:
                    stat.first_lines.append(line_no)

    return [(name, stat) for name, _, stat in compiled]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(Path("paper") / "allconversations.txt"))
    ap.add_argument("--first", type=int, default=12, help="How many first line numbers to print per pattern")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    stats = scan_file(path, _default_patterns(), first_n=args.first)

    print(f"source={path}")
    print("pattern\tlines\tmatches\tfirst_lines")
    for name, st in stats:
        first_lines = ",".join(str(n) for n in st.first_lines)
        print(f"{name}\t{st.line_hits}\t{st.match_hits}\t{first_lines}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
