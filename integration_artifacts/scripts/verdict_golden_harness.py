"""Golden re-run harness for main-project verdict commands.

Goal
- Re-run the *canonical* command list in tools/verdict_commands.txt.
- Rewrite any output paths (e.g. --out/--out_csv/--chi2_out) so that files are
  written under integration_artifacts/out/verdict_golden/ instead of the main
  project output locations.
- Produce a machine-readable + human-readable summary of which commands ran and
  what outputs were produced.

This does not validate physics correctness by itself; it validates
reproducibility of the canonical runners and gives stable reference artefacts
for later GKSL-vs-runner equivalence checks.

Usage (from repo root):
  python integration_artifacts/scripts/verdict_golden_harness.py

Options:
  --start N / --end N  : 1-based slice into the parsed command list
  --dry_run            : print rewritten commands, do not execute
  --keep_existing      : do not delete existing golden outputs directory

Notes
- Canonical source: tools/run_verdict.ps1 consumes tools/verdict_commands.txt.
- Output flags currently rewritten:
    --out, --out_csv, --chi2_out
  (Additional flags can be added if needed.)
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMANDS_FILE = REPO_ROOT / "tools" / "verdict_commands.txt"
GOLDEN_ROOT = REPO_ROOT / "integration_artifacts" / "out" / "verdict_golden"

OUTPUT_FLAGS = {"--out", "--out_csv", "--chi2_out"}


@dataclass
class RunResult:
    index: int
    command_original: str
    command_rewritten: list[str]
    returncode: int
    elapsed_sec: float
    outputs: list[str]


def parse_commands(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    commands: list[str] = []
    current: list[str] = []

    def flush() -> None:
        nonlocal current
        if current:
            commands.append(" ".join(current).strip())
            current = []

    for raw in lines:
        line = raw.strip().lstrip("\ufeff")
        if not line:
            continue
        if line.startswith("#") or line.startswith(">") or line.startswith("---"):
            continue
        if line.startswith("```"):
            continue

        is_cmd_start = line.lower().startswith("py ") or line.lower().startswith("python ")
        if is_cmd_start:
            flush()

        if not current and not is_cmd_start:
            # ignore stray text outside a command block
            continue

        cont = line.endswith("`")
        if cont:
            line = line[:-1].rstrip()

        current.append(line)
        if not cont:
            flush()

    flush()
    return commands


def normalize_relpath(p: str) -> str:
    p2 = p.strip().strip('"').strip("'")
    # Defensive: some tokenizers may interpret \t/\n escapes inside quoted strings.
    # Convert literal tab/newline characters back to the intended two-character
    # sequences so Windows paths remain stable.
    p2 = p2.replace("\t", "\\t").replace("\n", "\\n")
    # keep NUL special case
    if p2.lower() == "nul":
        return "NUL"
    # strip leading .\ or ./
    while p2.startswith(".\\") or p2.startswith("./") or p2.startswith(".//") or p2.startswith(".\\\\"):
        p2 = p2[2:]
    p2 = p2.replace("/", "\\")
    return p2


def rewrite_output_path(original_token: str) -> tuple[str, str | None]:
    """Return (rewritten_token, rewritten_abs_path_if_any)."""
    norm = normalize_relpath(original_token)
    if norm == "NUL":
        return "NUL", None

    # Place under GOLDEN_ROOT, preserving relative substructure if present.
    rel = Path(norm)
    out_path = GOLDEN_ROOT / rel
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve quoting style minimally (use raw string path).
    return str(out_path), str(out_path)


def rewrite_command(cmd: str) -> tuple[list[str], list[str]]:
    # Windows-friendly tokenization
    tokens = shlex.split(cmd, posix=False)
    if not tokens:
        return [], []

    # Replace launcher with current Python
    if tokens[0].lower() == "py":
        # drop version selector if present
        if len(tokens) >= 2 and tokens[1].startswith("-"):
            tokens = [sys.executable] + tokens[2:]
        else:
            tokens[0] = sys.executable
    elif tokens[0].lower() == "python":
        tokens[0] = sys.executable

    outputs: list[str] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in OUTPUT_FLAGS and i + 1 < len(tokens):
            rewritten, out_abs = rewrite_output_path(tokens[i + 1])
            tokens[i + 1] = rewritten
            if out_abs is not None:
                outputs.append(out_abs)
            i += 2
            continue
        i += 1

    return tokens, outputs


def run_one(index: int, cmd_original: str, cmd_tokens: list[str], outputs: list[str], dry_run: bool) -> RunResult:
    start = time.time()
    if dry_run:
        rc = 0
    else:
        proc = subprocess.run(cmd_tokens, cwd=str(REPO_ROOT))
        rc = int(proc.returncode)
    elapsed = time.time() - start

    # Verify outputs exist if command succeeded.
    missing: list[str] = []
    if rc == 0:
        for outp in outputs:
            if outp and not Path(outp).exists():
                missing.append(outp)

    if missing and rc == 0:
        # treat missing expected outputs as failure
        rc = 10

    return RunResult(
        index=index,
        command_original=cmd_original,
        command_rewritten=cmd_tokens,
        returncode=rc,
        elapsed_sec=float(elapsed),
        outputs=outputs,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=0)
    ap.add_argument("--dry_run", action="store_true")
    ap.add_argument("--keep_existing", action="store_true")
    args = ap.parse_args()

    if not COMMANDS_FILE.exists():
        raise FileNotFoundError(COMMANDS_FILE)

    commands = parse_commands(COMMANDS_FILE)
    if not commands:
        print("No commands parsed from", COMMANDS_FILE)
        return 2

    start_idx = max(1, int(args.start))
    end_idx = int(args.end) if int(args.end) > 0 else len(commands)
    end_idx = min(end_idx, len(commands))
    if start_idx > end_idx:
        raise SystemExit(f"Invalid range: start={start_idx} end={end_idx} total={len(commands)}")

    if GOLDEN_ROOT.exists() and not args.keep_existing and not args.dry_run:
        # delete only the golden root (safe, under integration_artifacts)
        for p in sorted(GOLDEN_ROOT.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                try:
                    p.rmdir()
                except OSError:
                    pass
        try:
            GOLDEN_ROOT.rmdir()
        except OSError:
            pass

    GOLDEN_ROOT.mkdir(parents=True, exist_ok=True)

    results: list[RunResult] = []
    overall_start = time.time()

    for idx in range(start_idx, end_idx + 1):
        cmd_str = commands[idx - 1]
        tokens, outs = rewrite_command(cmd_str)
        if not tokens:
            continue

        print(f"\n[{idx}/{len(commands)}] original: {cmd_str}")
        print(f"[{idx}/{len(commands)}] rewritten: {' '.join(tokens)}")

        res = run_one(idx, cmd_str, tokens, outs, dry_run=bool(args.dry_run))
        results.append(res)

        status = "OK" if res.returncode == 0 else f"FAIL(rc={res.returncode})"
        print(f"[{idx}] {status}  elapsed={res.elapsed_sec:.2f}s")

        if res.returncode != 0:
            # stop early on first failure (matches prereg runner philosophy)
            break

    total_elapsed = time.time() - overall_start

    # Write summaries
    summary_json = GOLDEN_ROOT / "RUN_SUMMARY.json"
    summary_md = GOLDEN_ROOT / "RUN_SUMMARY.md"

    data = {
        "repo_root": str(REPO_ROOT),
        "commands_file": str(COMMANDS_FILE),
        "golden_root": str(GOLDEN_ROOT),
        "start": start_idx,
        "end": end_idx,
        "dry_run": bool(args.dry_run),
        "total_commands_parsed": len(commands),
        "total_elapsed_sec": float(total_elapsed),
        "results": [
            {
                "index": r.index,
                "returncode": r.returncode,
                "elapsed_sec": r.elapsed_sec,
                "command_original": r.command_original,
                "command_rewritten": r.command_rewritten,
                "outputs": r.outputs,
            }
            for r in results
        ],
    }
    summary_json.write_text(json.dumps(data, indent=2), encoding="utf-8")

    ok = all(r.returncode == 0 for r in results) and (len(results) == (end_idx - start_idx + 1))

    lines = []
    lines.append("# Verdict golden harness summary")
    lines.append("")
    lines.append(f"- Commands file: `{COMMANDS_FILE}`")
    lines.append(f"- Golden root: `{GOLDEN_ROOT}`")
    lines.append(f"- Range: {start_idx}..{end_idx} (total parsed: {len(commands)})")
    lines.append(f"- Total elapsed: {total_elapsed:.2f} s")
    lines.append(f"- Result: {'OK' if ok else 'FAILED'}")
    lines.append("")

    for r in results:
        status = "OK" if r.returncode == 0 else f"FAIL(rc={r.returncode})"
        lines.append(f"## {r.index}: {status} ({r.elapsed_sec:.2f}s)")
        lines.append("")
        lines.append("Original:")
        lines.append(f"`{r.command_original}`")
        lines.append("")
        lines.append("Rewritten:")
        lines.append(f"`{' '.join(r.command_rewritten)}`")
        lines.append("")
        if r.outputs:
            lines.append("Outputs:")
            for o in r.outputs:
                lines.append(f"- `{o}`")
            lines.append("")

    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nWrote: {summary_md}")
    print(f"Wrote: {summary_json}")

    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
