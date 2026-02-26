#!/usr/bin/env python3
"""Remove ChatGPT-targeted profanity/insults from paper/allconversations.txt.

Design goals:
- Operate in chunks of N pages (default 200 pages), where a page is a fixed number
  of lines (default 50). This is a pragmatic mapping for plain-text files.
- Prefer sentence-level removal inside a line when possible; drop whole line only
  if it becomes empty after removing sentences.
- Create a timestamped backup before modifying the file.
- Write an audit log of removed content.

This script is intentionally conservative: it only removes sentences that both
(a) reference ChatGPT (or similar) and (b) include a profanity/insult token.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MatchInfo:
    line_no: int
    page_no: int
    chunk_no: int
    original_line: str
    removed_sentence: str
    reason: str


@dataclass(frozen=True)
class CandidateInfo:
    line_no: int
    page_no: int
    chunk_no: int
    candidate_sentence: str
    original_line: str
    reason: str


@dataclass(frozen=True)
class _BadToken:
    pattern: str
    flags: int


def _bad_tokens(profile: str) -> list[_BadToken]:
    """Return regex token patterns for profanity/insults.

    IMPORTANT:
    - Do NOT apply re.IGNORECASE globally, because Unicode casefolding can cause
      Turkish i/ı to match unexpectedly (e.g. "sık" being detected as "sik").
    - Instead, each token carries its own flags.
    """

    ci = re.IGNORECASE

    conservative: list[_BadToken] = [
        # amk / a.m.k / a m k
        _BadToken(r"(?<!\w)a\s*\.?\s*m\s*\.?\s*k(?!\w)", ci),
        _BadToken(r"\baq\b", ci),
        # mk as a standalone word token
        _BadToken(r"(?<!\w)mk(?!\w)", ci),

        # Core Turkish profanity roots (dotted i only for 'sik')
        # Exclude the scientific stem "siklo" (cyclo-) as in "siklotron".
        # NOTE: flags=0 to avoid Turkish i/ı casefold leakage.
        _BadToken(r"(?<!\w)[sS][iİ][kK](?![lL][oO])\w*", 0),
        _BadToken(r"(?<!\w)[sS][iİ][kK][tT][iİ][rR]\w*", 0),

        # Other Turkish profanity
        _BadToken(r"\borospu\w*", ci),
        _BadToken(r"\bpiç\w*", ci),
        _BadToken(r"\byarrak\w*", ci),
        # 'göt' is profanity, but exclude the common verb stem 'götür...'
        _BadToken(r"(?<!\w)[gG][öÖ][tT](?![uUüÜ][rR])\w*", 0),
        # 'amın/amına...' uses dotless ı; keep flags=0 to avoid matching 'amin'
        _BadToken(r"(?<!\w)[aA][mM][ıI][nN]\w*", 0),
        _BadToken(r"\banan\w*", ci),
        _BadToken(r"(?<!\w)lan(?!\w)", ci),

        # English profanity
        _BadToken(r"\bfuck\w*", ci),
        _BadToken(r"\bshit\w*", ci),
        _BadToken(r"\bbitch\w*", ci),
        _BadToken(r"\basshole\w*", ci),
        _BadToken(r"(?<!\w)fking(?!\w)", ci),
        _BadToken(r"\bmotherfucker\w*", ci),
    ]

    broad: list[_BadToken] = conservative + [
        _BadToken(r"\baptal\w*", ci),
        _BadToken(r"\bsalak\w*", ci),
        _BadToken(r"\bgerizekal\w*", ci),
        _BadToken(r"\bembesil\w*", ci),
        _BadToken(r"\bdangalak\w*", ci),
        _BadToken(r"\bmal\b", ci),
    ]

    if profile == "conservative":
        return conservative
    if profile == "broad":
        return broad
    raise ValueError(f"Unknown bad-token profile: {profile}")


def _compile_patterns(*, bad_profile: str) -> tuple[re.Pattern[str], re.Pattern[str], list[re.Pattern[str]]]:
    # References to the assistant/platform.
    ref = re.compile(r"\b(chat\s*gpt|chatgpt|gpt\b|openai|copilot)\b", re.IGNORECASE)

    # Second-person address patterns (common in direct complaints/insults).
    # Used as a heuristic for "directed at the assistant" even when the word
    # "ChatGPT" is not present.
    target_2p = re.compile(
        r"\b("
        r"sen|sana|seni|senin|siz|size|sizin|"
        r"ver|verin|"
        r"çöz|çözün|"
        r"ver(?:din|dim|medin|medim|emedin|emedim)|"
        r"verdiğ(?:in|im)|"
        r"yap(?:t[ıi]n|[ıi]yorsun)|"
        r"yapt[ıi]ğ(?:in|im)|yapacağ(?:ın|ım)|"
        r"yaz(?:d[ıi]n|[ıi]yorsun)|"
        r"yazd[ıi]ğ(?:in|im)"
        r")\b",
        re.IGNORECASE,
    )

    # Turkish/English profanity + insults.
    # IMPORTANT: avoid re.IGNORECASE for Turkish tokens involving i/ı.
    # Python's Unicode casefolding can equate i/ı in ways that create false
    # positives (e.g., matching "sık" when searching for "sik").
    bad_pats = [re.compile(t.pattern, t.flags) for t in _bad_tokens(bad_profile)]

    return ref, target_2p, bad_pats


def _split_sentences(line: str) -> list[str]:
    # Best-effort sentence splitter for single-line text. We keep punctuation.
    # If no split points exist, returns [line].
    stripped = line.rstrip("\n")
    if not stripped:
        return [line]

    parts = re.split(r"(?<=[.!?…])\s+", stripped)
    # Re-attach newline later; keep as sentences without trailing newline.
    return parts


def _first_bad_match(sentence: str, bad_pats: list[re.Pattern[str]]) -> re.Match[str] | None:
    for p in bad_pats:
        m = p.search(sentence)
        if m:
            return m
    return None


def _needs_removal(
    sentence: str, ref_pat: re.Pattern[str], bad_pats: list[re.Pattern[str]]
) -> tuple[bool, str]:
    if not ref_pat.search(sentence):
        return False, ""
    bad_m = _first_bad_match(sentence, bad_pats)
    if not bad_m:
        return False, ""
    return True, f"ref+bad:{bad_m.group(0)}"


def _needs_removal_any(sentence: str, bad_pats: list[re.Pattern[str]]) -> tuple[bool, str]:
    bad_m = _first_bad_match(sentence, bad_pats)
    if not bad_m:
        return False, ""
    return True, f"bad:{bad_m.group(0)}"


def _needs_removal_in_line(
    sentence: str, line_targeted: bool, bad_pats: list[re.Pattern[str]]
) -> tuple[bool, str]:
    """If a line seems directed at the assistant, drop any sentence with a bad token.

    This catches cases like:
    "... chatgpt'ye sesleniyorum ..." + "... <küfür> ..." split into separate sentences.
    """
    if not line_targeted:
        return False, ""
    bad_m = _first_bad_match(sentence, bad_pats)
    if not bad_m:
        return False, ""
    return True, f"targeted_line+bad:{bad_m.group(0)}"


def clean_file(
    path: Path,
    *,
    lines_per_page: int,
    pages_per_chunk: int,
    log_path: Path,
    make_backup: bool,
    scope: str,
    targeting: str,
    bad_profile: str,
    candidates_log_path: Path | None,
) -> dict[str, object]:
    ref_pat, target_2p_pat, bad_pats = _compile_patterns(bad_profile=bad_profile)
    shell_pat = re.compile(r"\bPS\s+[A-Za-z]:\\|\bPS\s+\\\\|\bC:\\", re.IGNORECASE)

    raw = path.read_text(encoding="utf-8", errors="surrogateescape")
    lines = raw.splitlines(keepends=True)

    if make_backup:
        stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(path.suffix + f".bak_{stamp}")
        shutil.copyfile(path, backup_path)
    else:
        backup_path = None

    removed: list[MatchInfo] = []
    candidates: list[CandidateInfo] = []
    cleaned_lines: list[str] = []

    chunk_removed_counts: dict[int, int] = {}

    for idx, line in enumerate(lines, start=1):
        page_no = (idx - 1) // lines_per_page + 1
        chunk_no = (page_no - 1) // pages_per_chunk + 1

        line_has_ref = bool(ref_pat.search(line))
        line_has_2p = bool(target_2p_pat.search(line))
        line_has_shell = bool(shell_pat.search(line))
        if targeting == "strict":
            # Only treat as targeted if ChatGPT/GPT/etc is explicitly mentioned
            line_targeted = line_has_ref
        else:
            # Heuristic: also consider direct second-person address as targeted
            line_targeted = line_has_ref or line_has_2p or line_has_shell
        sentences = _split_sentences(line)
        kept_sentences: list[str] = []

        line_removed_any = False
        for s in sentences:
            needs1, reason1 = _needs_removal(s, ref_pat, bad_pats)
            needs2, reason2 = _needs_removal_in_line(s, line_targeted, bad_pats)
            needs3, reason3 = _needs_removal_any(s, bad_pats) if scope == "all" else (False, "")

            # Candidate collection (for strict targeted mode):
            # A profanity sentence with second-person address but without explicit
            # ChatGPT mention could still be directed at the assistant; don't delete
            # it automatically in strict mode, but log it for review.
            if (
                scope == "targeted"
                and targeting == "strict"
                and (not line_has_ref)
                and line_has_2p
            ):
                cand_needs, cand_reason = _needs_removal_any(s, bad_pats)
                if cand_needs:
                    candidates.append(
                        CandidateInfo(
                            line_no=idx,
                            page_no=page_no,
                            chunk_no=chunk_no,
                            candidate_sentence=s,
                            original_line=line.rstrip("\n"),
                            reason=f"candidate_2p+{cand_reason}",
                        )
                    )

            if needs1 or needs2 or needs3:
                line_removed_any = True
                removed.append(
                    MatchInfo(
                        line_no=idx,
                        page_no=page_no,
                        chunk_no=chunk_no,
                        original_line=line.rstrip("\n"),
                        removed_sentence=s,
                        reason=reason1 or reason2 or reason3,
                    )
                )
                chunk_removed_counts[chunk_no] = chunk_removed_counts.get(chunk_no, 0) + 1
            else:
                kept_sentences.append(s)

        if not line_removed_any:
            cleaned_lines.append(line)
            continue

        # If we removed something, rebuild the line from kept sentences.
        rebuilt = " ".join([t.strip() for t in kept_sentences if t.strip()])
        if rebuilt:
            cleaned_lines.append(rebuilt + "\n")
        # else: drop the line entirely

    # Write cleaned file back
    path.write_text("".join(cleaned_lines), encoding="utf-8", errors="surrogateescape")

    # Write audit log
    with log_path.open("w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(f"source={path}\n")
        f.write(f"lines_per_page={lines_per_page} pages_per_chunk={pages_per_chunk}\n")
        f.write(f"removed_sentences={len(removed)}\n")
        f.write("---\n")
        for m in removed:
            f.write(
                f"line={m.line_no} page={m.page_no} chunk={m.chunk_no} reason={m.reason}\n"
                f"removed={m.removed_sentence}\n"
                f"original_line={m.original_line}\n"
                "---\n"
            )

    if candidates_log_path is not None:
        with candidates_log_path.open("w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(f"source={path}\n")
            f.write(f"lines_per_page={lines_per_page} pages_per_chunk={pages_per_chunk}\n")
            f.write(f"candidates={len(candidates)}\n")
            f.write("---\n")
            for c in candidates:
                f.write(
                    f"line={c.line_no} page={c.page_no} chunk={c.chunk_no} reason={c.reason}\n"
                    f"candidate={c.candidate_sentence}\n"
                    f"original_line={c.original_line}\n"
                    "---\n"
                )

    # Build chunk summary (include zero-removal chunks too for consistent reporting)
    total_pages = (len(lines) - 1) // lines_per_page + 1 if lines else 0
    total_chunks = (total_pages - 1) // pages_per_chunk + 1 if total_pages else 0
    chunk_summary = [chunk_removed_counts.get(c, 0) for c in range(1, total_chunks + 1)]

    return {
        "backup_path": str(backup_path) if backup_path else None,
        "removed_count": len(removed),
        "total_lines": len(lines),
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "chunk_summary": chunk_summary,
        "log_path": str(log_path),
        "candidates": len(candidates),
        "candidates_log_path": str(candidates_log_path) if candidates_log_path else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--file",
        default=str(Path("paper") / "allconversations.txt"),
        help="Path to allconversations.txt",
    )
    ap.add_argument("--lines-per-page", type=int, default=50)
    ap.add_argument("--pages-per-chunk", type=int, default=200)
    ap.add_argument(
        "--log",
        default=str(Path("paper") / "allconversations_removed_profanity.log"),
        help="Audit log output path",
    )
    ap.add_argument(
        "--scope",
        choices=["targeted", "all"],
        default="targeted",
        help="Removal scope: 'targeted' (assistant-directed) or 'all' (any profanity/insult).",
    )
    ap.add_argument(
        "--bad-profile",
        choices=["conservative", "broad"],
        default="conservative",
        help="Token set to use when detecting profanity/insults. Use conservative to minimize false positives.",
    )
    ap.add_argument(
        "--targeting",
        choices=["strict", "heuristic"],
        default="strict",
        help="When scope=targeted: 'strict' requires explicit ChatGPT/GPT mention; 'heuristic' also uses second-person address.",
    )
    ap.add_argument(
        "--candidates-log",
        default=str(Path("paper") / "allconversations_profanity_candidates.log"),
        help="Where to write review-only candidates (used in strict targeted mode).",
    )
    ap.add_argument("--no-backup", action="store_true", help="Do not create a backup file")

    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    log_path = Path(args.log)

    candidates_log_path = Path(args.candidates_log) if args.candidates_log else None

    res = clean_file(
        path,
        lines_per_page=args.lines_per_page,
        pages_per_chunk=args.pages_per_chunk,
        log_path=log_path,
        make_backup=not args.no_backup,
        scope=args.scope,
        targeting=args.targeting,
        bad_profile=args.bad_profile,
        candidates_log_path=candidates_log_path,
    )

    print(f"Cleaned: {path}")
    if res["backup_path"]:
        print(f"Backup:  {res['backup_path']}")
    print(f"Removed sentences: {res['removed_count']}")
    print(f"Audit log: {res['log_path']}")
    if res.get("candidates_log_path"):
        print(f"Candidates log: {res['candidates_log_path']} (candidates={res['candidates']})")

    # Print per-chunk summary, but keep it compact.
    total_chunks = int(res["total_chunks"])
    chunk_summary = res["chunk_summary"]
    for i in range(total_chunks):
        removed_i = int(chunk_summary[i])
        start_page = i * args.pages_per_chunk + 1
        end_page = min((i + 1) * args.pages_per_chunk, int(res["total_pages"]))
        if removed_i:
            print(f"Chunk {i+1:02d} (pages {start_page}-{end_page}): removed={removed_i}")

    if total_chunks and not any(int(x) for x in chunk_summary):
        print("No ChatGPT-targeted profanity/insults found by current rules.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
