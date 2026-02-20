#!/usr/bin/env python3
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt


def load_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_metrics(cell: str):
    if not cell:
        return {}
    try:
        return json.loads(cell)
    except json.JSONDecodeError:
        return {}


def build_series(rows):
    labels = []
    values = []
    for row in rows:
        if (row.get("sector") or "").upper() != "STRONG":
            continue
        metrics = parse_metrics(row.get("metrics_json", ""))
        delta = metrics.get("delta_chi2")
        if not isinstance(delta, (int, float)):
            continue
        family = str(metrics.get("runner_family") or "strong_group")
        labels.append(family)
        values.append(float(delta))
    return labels, values


def make_plot(labels, values, out_png: Path):
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8.0, 4.8))
    if labels and values:
        colors = ["#1f77b4" if v <= 0 else "#d62728" for v in values]
        plt.bar(labels, values, color=colors)
        plt.axhline(0.0, color="black", linewidth=1.0)
        plt.ylabel("delta_chi2 (geo - null)")
        plt.xlabel("STRONG runner family")
        plt.title("STRONG prereg delta_chi2")
        plt.xticks(rotation=15, ha="right")
        plt.tight_layout()
    else:
        plt.text(
            0.5,
            0.5,
            "No STRONG delta_chi2 values found",
            ha="center",
            va="center",
            fontsize=11,
        )
        plt.axis("off")
        plt.tight_layout()
    plt.savefig(out_png, dpi=140)
    plt.close()


def main():
    repo_root = Path(__file__).resolve().parents[1]
    groups_csv = repo_root / "repro" / "verdict_groups.csv"
    out_png = repo_root / "repro" / "figs" / "strong_delta_chi2.png"
    if not groups_csv.exists():
        raise SystemExit(f"Missing input: {groups_csv}")
    rows = load_rows(groups_csv)
    labels, values = build_series(rows)
    make_plot(labels, values, out_png)
    print(f"Wrote: {out_png}")


if __name__ == "__main__":
    main()
