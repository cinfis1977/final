Integration artifacts for the GKSL/Lindblad demo and comparison.

## Local-only policy (NO REMOTE PUSH)

Do **not** push this repository to GitHub or any other remote. These artifacts are meant for **local** reproducibility only.

If you want to hard-disable remote pushes:

```powershell
git remote -v
# Option A (recommended): remove the remote entirely
git remote remove origin
# Option B: keep fetch but disable push
git remote set-url --push origin DISABLED
```

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
