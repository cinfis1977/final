#!/usr/bin/env python3
"""Summarize the profanity-removal audit log.

Reads a log produced by tools/clean_allconversations_profanity.py and produces:
- Per-chunk removal counts (chunk size = pages_per_chunk)
- Per-reason-category counts (sanitized; does not include profane token text)

This tool does NOT print any removed/original sentence text.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Header:
    source: str
    lines_per_page: int
    pages_per_chunk: int
    removed_sentences: int


_HEADER_RE = re.compile(
    r"^source=(?P<source>.+)\n"
    r"lines_per_page=(?P<lpp>\d+) pages_per_chunk=(?P<ppc>\d+)\n"
    r"removed_sentences=(?P<removed>\d+)\n",
    re.MULTILINE,
)

_ENTRY_RE = re.compile(
    r"^line=(?P<line>\d+) page=(?P<page>\d+) chunk=(?P<chunk>\d+) reason=(?P<reason>.+)$",
    re.MULTILINE,
)


def _parse_header(text: str) -> Header:
    m = _HEADER_RE.search(text)
    if not m:
        raise ValueError("Could not parse log header")
    return Header(
        source=m.group("source").strip(),
        lines_per_page=int(m.group("lpp")),
        pages_per_chunk=int(m.group("ppc")),
        removed_sentences=int(m.group("removed")),
    )


def _reason_category(reason: str) -> str:
    # Remove anything after ':' so we don't reproduce profane tokens.
    return reason.split(":", 1)[0].strip()


def summarize(log_path: Path) -> tuple[Header, dict[int, int], Counter[str], dict[int, list[int]]]:
    text = log_path.read_text(encoding="utf-8", errors="surrogateescape")
    header = _parse_header(text)

    per_chunk: dict[int, int] = defaultdict(int)
    reason_counts: Counter[str] = Counter()
    sample_lines_per_chunk: dict[int, list[int]] = defaultdict(list)

    for m in _ENTRY_RE.finditer(text):
        chunk = int(m.group("chunk"))
        line_no = int(m.group("line"))
        reason = m.group("reason").strip()

        per_chunk[chunk] += 1
        reason_counts[_reason_category(reason)] += 1

        # Keep small samples of line numbers for spot-checking.
        if len(sample_lines_per_chunk[chunk]) < 8:
            sample_lines_per_chunk[chunk].append(line_no)

    return header, dict(per_chunk), reason_counts, dict(sample_lines_per_chunk)


def write_markdown(
    out_path: Path,
    header: Header,
    per_chunk: dict[int, int],
    reason_counts: Counter[str],
    samples: dict[int, list[int]],
) -> None:
    max_chunk = max(per_chunk.keys(), default=0)
    rows = []
    total = 0
    for chunk in range(1, max_chunk + 1):
        removed = per_chunk.get(chunk, 0)
        total += removed
        start_page = (chunk - 1) * header.pages_per_chunk + 1
        end_page = chunk * header.pages_per_chunk
        sample = ", ".join(str(x) for x in samples.get(chunk, []))
        rows.append((chunk, start_page, end_page, removed, sample))

    with out_path.open("w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(f"# Profanity removal summary\n\n")
        f.write(f"- source: {header.source}\n")
        f.write(f"- lines_per_page: {header.lines_per_page}\n")
        f.write(f"- pages_per_chunk: {header.pages_per_chunk}\n")
        f.write(f"- removed_sentences (log header): {header.removed_sentences}\n")
        f.write(f"- removed_sentences (parsed): {total}\n\n")

        f.write("## By chunk (200-page blocks)\n")
        f.write("Chunk | Pages | Removed | Sample line numbers (first 8)\n")
        f.write("---:|:---|---:|:---\n")
        for chunk, start_page, end_page, removed, sample in rows:
            if removed == 0:
                continue
            f.write(f"{chunk} | {start_page}-{end_page} | {removed} | {sample}\n")

        f.write("\n## By reason category (sanitized)\n")
        f.write("Category | Count\n")
        f.write("---|---:\n")
        for cat, cnt in reason_counts.most_common():
            f.write(f"{cat} | {cnt}\n")

        f.write("\nNotes:\n")
        f.write("- This report intentionally omits removed/original sentence text.\n")
        f.write("- Reason categories are sanitized (anything after ':' is dropped).\n")


def write_csv(out_path: Path, header: Header, per_chunk: dict[int, int]) -> None:
    max_chunk = max(per_chunk.keys(), default=0)
    with out_path.open("w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chunk", "start_page", "end_page", "removed"])
        for chunk in range(1, max_chunk + 1):
            removed = per_chunk.get(chunk, 0)
            start_page = (chunk - 1) * header.pages_per_chunk + 1
            end_page = chunk * header.pages_per_chunk
            w.writerow([chunk, start_page, end_page, removed])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--log",
        default=str(Path("paper") / "allconversations_removed_profanity_ALL_conservative.log"),
        help="Input audit log path",
    )
    ap.add_argument(
        "--out-md",
        default=str(Path("paper") / "allconversations_removed_profanity_summary.md"),
        help="Output markdown summary path",
    )
    ap.add_argument(
        "--out-csv",
        default=str(Path("paper") / "allconversations_removed_profanity_summary.csv"),
        help="Output CSV summary path",
    )
    args = ap.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        raise SystemExit(f"Log not found: {log_path}")

    header, per_chunk, reason_counts, samples = summarize(log_path)

    out_md = Path(args.out_md)
    out_csv = Path(args.out_csv)
    write_markdown(out_md, header, per_chunk, reason_counts, samples)
    write_csv(out_csv, header, per_chunk)

    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Chunks with removals: {sum(1 for v in per_chunk.values() if v)}")
    print(f"Removed (parsed): {sum(per_chunk.values())}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
