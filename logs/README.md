# logs/

This folder stores **run-captured evidence** grouped by sector:

- `logs/weak/<run_id>/...`
- `logs/strong/<run_id>/...`
- `logs/em/<run_id>/...`
- `logs/dm/<run_id>/...`

Each captured run contains:

1) `command.txt` — exact command line used
2) `terminal_output_and_exit_code.txt` — combined stdout/stderr plus exit code
3) `artifacts/` — copies of produced `.csv`/`.json`

Run IDs are formatted like `YYYY-MM-DD_runNN`.

To generate a new run capture on Windows PowerShell:

```powershell
./scripts/capture_sector_runs_to_logs.ps1
```

You can override the run id:

```powershell
./scripts/capture_sector_runs_to_logs.ps1 -RunId 2026-03-03_run01
```
