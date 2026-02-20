#!/usr/bin/env python3
import csv
import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def _safe_name(text: str) -> str:
    out = []
    for ch in text:
        if ch.isalnum() or ch in ('-', '_'):
            out.append(ch)
        else:
            out.append('_')
    s = ''.join(out).strip('_')
    return s or 'item'


def _as_list(cell: str):
    if not cell:
        return []
    return [x.strip() for x in cell.split(';') if x.strip()]


def _abs_path(repo_root: Path, value: str) -> Path:
    p = value.strip().strip('"').strip("'")
    if p.startswith('.\\') or p.startswith('./'):
        p = p[2:]
    p = p.replace('/', os.sep).replace('\\', os.sep)
    return repo_root / p


def _choose_xy(headers):
    lower = {h.lower(): h for h in headers}
    x_pref = ['energy', 'q2', 'bin', 't', 't_s', 'sqrts_gev', 'sqrt_s_gev', 'x']
    y_pref = ['value', 'chi2', 'sigma_tot_mb', 'rho', 'y', 'pred', 'sm_pred_pb', 'h_plus_proxy']

    x_col = None
    y_col = None

    for k in x_pref:
        if k in lower:
            x_col = lower[k]
            break

    for k in y_pref:
        if k in lower:
            y_col = lower[k]
            break

    if x_col is None and headers:
        x_col = headers[0]
    if y_col is None:
        for h in headers:
            if h != x_col:
                y_col = h
                break

    return x_col, y_col


def _read_numeric_xy(csv_path: Path):
    xs = []
    ys = []
    with csv_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if not headers:
            return None, None, xs, ys
        x_col, y_col = _choose_xy(headers)
        if not x_col or not y_col:
            return None, None, xs, ys

        for row in reader:
            xv = row.get(x_col, '')
            yv = row.get(y_col, '')
            try:
                x = float(xv)
                y = float(yv)
            except (TypeError, ValueError):
                continue
            xs.append(x)
            ys.append(y)

    return x_col, y_col, xs, ys


def main():
    repo_root = Path(__file__).resolve().parents[1]
    repro_dir = repo_root / 'repro'
    figs_dir = repro_dir / 'figs'
    figs_dir.mkdir(parents=True, exist_ok=True)

    summary_csv = repro_dir / 'run_summary.csv'
    report_md = repro_dir / 'REPORT.md'

    if not summary_csv.exists():
        raise SystemExit(f'run_summary.csv not found: {summary_csv}')

    rows = []
    with summary_csv.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    plotted = []
    plot_errors = []

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except Exception as exc:
        plt = None
        plot_errors.append(f'matplotlib_unavailable: {exc}')

    if plt is not None:
        seen = set()
        for row in rows:
            exp_values = _as_list(row.get('expected_outputs', ''))
            for exp in exp_values:
                if '*' in exp:
                    pattern_path = _abs_path(repo_root, exp)
                    for p in pattern_path.parent.glob(pattern_path.name):
                        if p.suffix.lower() == '.csv':
                            seen.add(p.resolve())
                else:
                    p = _abs_path(repo_root, exp)
                    if p.exists() and p.suffix.lower() == '.csv':
                        seen.add(p.resolve())

        for csv_path in sorted(seen):
            try:
                x_col, y_col, xs, ys = _read_numeric_xy(csv_path)
                if x_col is None or y_col is None or len(xs) < 2:
                    continue

                fig, ax = plt.subplots(figsize=(7.0, 4.0))
                ax.plot(xs, ys, linewidth=1.3)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.set_title(csv_path.name)
                ax.grid(True, alpha=0.3)

                rel = csv_path.relative_to(repo_root)
                digest = hashlib.sha1(str(rel).encode('utf-8')).hexdigest()[:10]
                out_name = f"{_safe_name(csv_path.stem)}_{digest}.png"
                out_path = figs_dir / out_name
                fig.tight_layout()
                fig.savefig(out_path, dpi=140)
                plt.close(fig)

                plotted.append((str(rel).replace('\\', '/'), str(out_path.relative_to(repo_root)).replace('\\', '/')))
            except Exception as exc:
                plot_errors.append(f'{csv_path}: {exc}')

    pass_count = sum(1 for r in rows if (r.get('status') or '').upper() == 'PASS')
    fail_count = sum(1 for r in rows if (r.get('status') or '').upper() != 'PASS')

    lines = []
    lines.append('# Reproducibility Report')
    lines.append('')
    lines.append(f'- Generated (UTC): {datetime.now(timezone.utc).isoformat()}')
    lines.append(f'- Total runs: {len(rows)}')
    lines.append(f'- PASS: {pass_count}')
    lines.append(f'- FAIL: {fail_count}')
    lines.append('')

    lines.append('## Run Summary')
    lines.append('')
    lines.append('| sector | runner | dataset | command | expected_outputs | run_ok | data_ok | verdict_pass | status | data_notes | notes | log |')
    lines.append('|---|---|---|---|---|---|---|---|---|---|---|---|')

    for row in rows:
        sector = (row.get('sector') or '').replace('|', '\\|')
        runner = (row.get('runner') or '').replace('|', '\\|')
        dataset = (row.get('dataset') or '').replace('|', '\\|')
        command = (row.get('command') or '').replace('|', '\\|')
        expected = (row.get('expected_outputs') or '').replace('|', '\\|')
        run_ok = (row.get('run_ok') or '').replace('|', '\\|')
        data_ok = (row.get('data_ok') or '').replace('|', '\\|')
        verdict_pass = (row.get('verdict_pass') or '').replace('|', '\\|')
        status = (row.get('status') or '').replace('|', '\\|')
        data_notes = (row.get('data_notes') or '').replace('|', '\\|')
        notes = (row.get('notes') or '').replace('|', '\\|')
        log_file = (row.get('log_file') or '').replace('\\', '/')
        log_file = re.sub(r'/+', '/', log_file).lstrip('/')
        if log_file.lower().startswith('repro/'):
            log_target = log_file[len('repro/'):]
        else:
            log_target = log_file
        log_target = re.sub(r'/+', '/', log_target).lstrip('/')
        log_link = f'[{log_file}]({log_target})' if log_file else ''

        lines.append(
            f'| {sector} | {runner} | {dataset} | `{command}` | {expected} | {run_ok} | {data_ok} | {verdict_pass} | {status} | {data_notes} | {notes} | {log_link} |'
        )

    lines.append('')
    lines.append('## Figures')
    lines.append('')

    if plotted:
        for src_csv, out_png in plotted:
            if out_png.lower().startswith('repro/'):
                out_target = out_png[len('repro/'):]
            else:
                out_target = out_png
            out_target = re.sub(r'/+', '/', out_target).lstrip('/')
            lines.append(f'- `{src_csv}` -> ![]({out_target})')
    else:
        lines.append('- No plots generated from produced CSV outputs.')

    if plot_errors:
        lines.append('')
        lines.append('## Plot Notes')
        lines.append('')
        for err in plot_errors:
            lines.append(f'- {err}')

    report_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    inventory_csv = repro_dir / 'summary_table.csv'
    with inventory_csv.open('w', encoding='utf-8', newline='') as f:
        if rows:
            headers = list(rows[0].keys())
        else:
            headers = ['run_index', 'sector', 'runner', 'dataset', 'command', 'expected_outputs', 'run_ok', 'data_ok', 'verdict_pass', 'status', 'data_notes', 'notes', 'log_file']
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f'Report written: {report_md}')
    print(f'Rows: {len(rows)} PASS={pass_count} FAIL={fail_count}')
    if plotted:
        print(f'Plots: {len(plotted)} -> {figs_dir}')
    else:
        print('Plots: none')


if __name__ == '__main__':
    main()
