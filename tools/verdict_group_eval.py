#!/usr/bin/env python3
import csv
import json
import re
from pathlib import Path


def norm_rel(p: str) -> str:
    if not p:
        return ""
    s = p.strip().strip('"').strip("'")
    s = re.sub(r"^[.\s\\/]+", "", s)
    return s.replace("/", "\\")


def parse_arg(cmd: str, name: str) -> str:
    pat = re.compile(rf"--{re.escape(name)}(?:\s+|=)(\"[^\"]+\"|\S+)", re.IGNORECASE)
    m = pat.search(cmd or "")
    if not m:
        return ""
    return m.group(1).strip().strip('"').strip("'")


def parse_a(cmd: str):
    raw = parse_arg(cmd, "A")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse_expected_outputs(cell: str):
    if not cell:
        return []
    return [norm_rel(x) for x in cell.split(";") if x.strip()]


def find_chi2_path(row: dict, repo_root: Path):
    for out in parse_expected_outputs(row.get("expected_outputs", "")):
        if out.lower().endswith("_chi2.json"):
            p = repo_root / out
            if p.exists():
                return p
    raw = norm_rel(parse_arg(row.get("command", ""), "chi2_out"))
    if raw:
        p = repo_root / raw
        if p.exists():
            return p
    return None


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def chi2_geo_value(payload: dict):
    if isinstance(payload.get("results"), list):
        vals = []
        for r in payload["results"]:
            v = r.get("chi2_GEO")
            if isinstance(v, (int, float)):
                vals.append(float(v))
        if vals:
            return float(sum(vals))
    for key in ("chi2_GEO_disp", "chi2_GEO", "chi2_geo"):
        v = payload.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def summarize_data_ok(rows):
    vals = [str(r.get("data_ok", "")).upper() for r in rows]
    if not vals:
        return "UNKNOWN"
    if any(v == "NO" for v in vals):
        return "NO"
    if all(v == "YES" for v in vals):
        return "YES"
    if all(v == "NO_DATA" for v in vals):
        return "NO_DATA"
    if all(v in ("YES", "NO_DATA") for v in vals):
        return "PARTIAL"
    return "UNKNOWN"


def links(rows):
    out = []
    for r in rows:
        lf = (r.get("log_file") or "").strip()
        if not lf:
            continue
        lf_norm = re.sub(r"[\\/]+", "/", lf).lstrip("/")
        if lf_norm and lf_norm not in out:
            out.append(lf_norm)
    return ";".join(out)


def safe_group_id(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return s or "group"


def has_chi2_marker_in_log(repo_root: Path, row: dict) -> bool:
    log_rel = (row.get("log_file") or "").strip()
    if not log_rel:
        return False
    log_path = repo_root / norm_rel(log_rel)
    if not log_path.exists():
        return False
    txt = log_path.read_text(encoding="utf-8", errors="ignore")
    return bool(re.search(r"\bchi2\b", txt, re.IGNORECASE))


def make_strong_groups(rows, repo_root: Path):
    pass_rows = [
        r
        for r in rows
        if (r.get("status") or "").upper() == "PASS"
        and str(r.get("runner", "")).lower().startswith("strong_")
    ]
    grouped = {}
    for r in pass_rows:
        runner = str(r.get("runner", "")).lower()
        if "sigma_tot_energy_scan" in runner:
            family = "sigma_tot"
        elif "rho_energy_scan" in runner:
            family = "rho"
        elif "rho_from_sigmatot_dispersion" in runner:
            family = "rho_from_sigmatot_dispersion"
        else:
            family = "other"
        dataset = r.get("dataset", "")
        key = (dataset, family)
        grouped.setdefault(key, []).append(r)

    out = []
    for (dataset, family), grows in sorted(grouped.items(), key=lambda x: (x[0][1], x[0][0])):
        a_vals = []
        for r in grows:
            a = parse_a(r.get("command", ""))
            if a is not None:
                a_vals.append(a)
        a_unique = sorted(set(a_vals))
        present_runs = ",".join([f"A={a:g}" for a in a_unique]) if a_unique else str(len(grows))

        metrics = {
            "runner_family": family,
            "dataset": dataset,
            "a_values_present": a_unique,
        }
        notes = []
        verdict = "UNKNOWN"

        null_row = None
        geo_row = None
        for r in grows:
            a = parse_a(r.get("command", ""))
            if a is None:
                continue
            if abs(a - 0.0) < 1e-12:
                null_row = r
            if abs(a - (-0.003)) < 1e-12:
                geo_row = r

        if null_row and geo_row:
            null_path = find_chi2_path(null_row, repo_root)
            geo_path = find_chi2_path(geo_row, repo_root)
            if null_path and geo_path:
                null_json = load_json(null_path)
                geo_json = load_json(geo_path)
                null_chi2 = chi2_geo_value(null_json)
                geo_chi2 = chi2_geo_value(geo_json)
                if null_chi2 is not None and geo_chi2 is not None:
                    delta = geo_chi2 - null_chi2
                    metrics["delta_chi2"] = delta
                    metrics["chi2_geo"] = geo_chi2
                    metrics["chi2_null"] = null_chi2
                    metrics["chi2_geo_file"] = str(geo_path.relative_to(repo_root)).replace("\\", "/")
                    metrics["chi2_null_file"] = str(null_path.relative_to(repo_root)).replace("\\", "/")
                    notes.append("delta_chi2 computed; no threshold applied")
                else:
                    notes.append("chi2 json found but chi2 fields missing")
            else:
                notes.append("required chi2 json files missing")
        else:
            notes.append("required A=0 and A=-0.003 runs not both present")

        out.append(
            {
                "group_id": safe_group_id(f"STRONG_{family}_{dataset}"),
                "sector": "STRONG",
                "definition": f"dataset={dataset};runner_family={family}",
                "required_runs": "A=0 and A=-0.003",
                "present_runs": present_runs,
                "data_ok": summarize_data_ok(grows),
                "verdict": verdict,
                "metrics_json": json.dumps(metrics, ensure_ascii=False),
                "notes": "; ".join(notes) if notes else "",
                "links_to_logs": links(grows),
            }
        )
    return out


def make_weak_group(rows, repo_root: Path):
    weak_rows = [
        r
        for r in rows
        if (r.get("status") or "").upper() == "PASS"
        and ("WEAK" in str(r.get("sector", "")).upper() or "nova_mastereq_forward" in str(r.get("runner", "")))
    ]
    if not weak_rows:
        return {
            "group_id": "WEAK_minos_single",
            "sector": "WEAK",
            "definition": "single MINOS prereg run",
            "required_runs": "1",
            "present_runs": "0",
            "data_ok": "UNKNOWN",
            "verdict": "UNKNOWN",
            "metrics_json": json.dumps({}),
            "notes": "no successful prereg run to evaluate",
            "links_to_logs": "",
        }

    has_chi2 = False
    for r in weak_rows:
        if find_chi2_path(r, repo_root) is not None or has_chi2_marker_in_log(repo_root, r):
            has_chi2 = True
            break

    note = "chi2 markers present; no threshold specified" if has_chi2 else "no chi2 markers produced"
    return {
        "group_id": "WEAK_minos_single",
        "sector": "WEAK",
        "definition": "single MINOS prereg run",
        "required_runs": "1",
        "present_runs": str(len(weak_rows)),
        "data_ok": summarize_data_ok(weak_rows),
        "verdict": "UNKNOWN",
        "metrics_json": json.dumps({"chi2_marker_present": has_chi2}),
        "notes": note,
        "links_to_logs": links(weak_rows),
    }


def make_ligo_group(rows):
    ligo_rows = [
        r
        for r in rows
        if (r.get("status") or "").upper() == "PASS"
        and ("LIGO" in str(r.get("sector", "")).upper() or "improved_simulation_stable" in str(r.get("runner", "")).lower())
    ]
    pats = []
    for r in ligo_rows:
        p = parse_arg(r.get("command", ""), "drive_pattern")
        if p and p not in pats:
            pats.append(p)
    return {
        "group_id": "LIGO_pattern_generation",
        "sector": "LIGO",
        "definition": "plus/cross pattern generation",
        "required_runs": "drive_pattern=quad_plus_xy and quad_cross_xy",
        "present_runs": ",".join(pats) if pats else str(len(ligo_rows)),
        "data_ok": summarize_data_ok(ligo_rows) if ligo_rows else "NO_DATA",
        "verdict": "NA",
        "metrics_json": json.dumps({"patterns": pats}),
        "notes": "pattern generation only, no data input",
        "links_to_logs": links(ligo_rows),
    }


def make_sector_no_pass_group(rows, sector_name: str, runner_key: str):
    sec_rows = [
        r
        for r in rows
        if sector_name in str(r.get("sector", "")).upper() or runner_key in str(r.get("runner", "")).lower()
    ]
    pass_rows = [r for r in sec_rows if (r.get("status") or "").upper() == "PASS"]
    if not pass_rows:
        return {
            "group_id": f"{sector_name}_prereg",
            "sector": sector_name,
            "definition": f"{sector_name} prereg group",
            "required_runs": ">=1 PASS prereg run",
            "present_runs": "0",
            "data_ok": "UNKNOWN",
            "verdict": "UNKNOWN",
            "metrics_json": json.dumps({}),
            "notes": "no successful prereg run to evaluate",
            "links_to_logs": links(sec_rows),
        }
    return {
        "group_id": f"{sector_name}_prereg",
        "sector": sector_name,
        "definition": f"{sector_name} prereg group",
        "required_runs": ">=1 PASS prereg run",
        "present_runs": str(len(pass_rows)),
        "data_ok": summarize_data_ok(pass_rows),
        "verdict": "UNKNOWN",
        "metrics_json": json.dumps({}),
        "notes": "PASS runs present; group-level rule not specified",
        "links_to_logs": links(pass_rows),
    }


def main():
    repo_root = Path(__file__).resolve().parents[1]
    repro_dir = repo_root / "repro"
    summary_path = repro_dir / "run_summary.csv"
    groups_csv = repro_dir / "verdict_groups.csv"
    report_md = repro_dir / "REPORT_VERDICT.md"

    if not summary_path.exists():
        raise SystemExit(f"Missing input: {summary_path}")

    with summary_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    groups = []
    groups.extend(make_strong_groups(rows, repo_root))
    groups.append(make_weak_group(rows, repo_root))
    groups.append(make_ligo_group(rows))
    groups.append(make_sector_no_pass_group(rows, "DM", "dm_"))
    groups.append(make_sector_no_pass_group(rows, "EM", "em_"))

    fields = [
        "group_id",
        "sector",
        "definition",
        "required_runs",
        "present_runs",
        "data_ok",
        "verdict",
        "metrics_json",
        "notes",
        "links_to_logs",
    ]
    with groups_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for g in groups:
            w.writerow(g)

    verdict_counts = {}
    for g in groups:
        verdict_counts[g["verdict"]] = verdict_counts.get(g["verdict"], 0) + 1

    lines = []
    lines.append("# Group Verdict Report")
    lines.append("")
    lines.append(f"- Source summary: `{summary_path.relative_to(repo_root).as_posix()}`")
    lines.append(f"- Groups: {len(groups)}")
    lines.append(f"- Verdict counts: {json.dumps(verdict_counts, ensure_ascii=False)}")
    lines.append("")
    lines.append("| group_id | sector | verdict | data_ok | required_runs | present_runs | notes | logs |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for g in groups:
        logs = g.get("links_to_logs", "")
        log_links = []
        for lp in [x for x in logs.split(";") if x.strip()]:
            lp_norm = lp.replace("\\", "/")
            # REPORT_VERDICT.md lives in repro/, so link relative to repro/.
            if lp_norm.lower().startswith("repro/"):
                rel_target = lp_norm[len("repro/") :]
            else:
                rel_target = lp_norm
            log_links.append(f"[{lp_norm}]({rel_target})")
        log_cell = " ".join(log_links)
        lines.append(
            f"| {g['group_id']} | {g['sector']} | {g['verdict']} | {g['data_ok']} | {g['required_runs']} | {g['present_runs']} | {g['notes']} | {log_cell} |"
        )
    lines.append("")
    lines.append("## Metrics JSON")
    lines.append("")
    for g in groups:
        lines.append(f"- `{g['group_id']}`: `{g['metrics_json']}`")

    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote: {groups_csv}")
    print(f"Wrote: {report_md}")


if __name__ == "__main__":
    main()
