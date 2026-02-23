Integration artifacts for the GKSL/Lindblad demo and comparison.

This folder contains copies of all files created for the GKSL integration so
that nothing in the original repository is modified. Use `run_integration_demo.py`
to run the demo and tests in this isolated location.

Structure:
- `mastereq/` : GKSL solver and tests (copies)
- `runners/`  : demo runner (copy)
- `scripts/`  : plotting script (copy)
- `out/`      : demo outputs (example)
- `run_integration_demo.py` : runner script that runs demo and tests from here

How to run (from repository root):

```bash
python integration_artifacts/run_integration_demo.py
```

This will:
- run the demo runner and write outputs to `integration_artifacts/out/`
- run the small test-suite located in `integration_artifacts/mastereq/tests/`

No existing files outside `integration_artifacts/` will be modified.
