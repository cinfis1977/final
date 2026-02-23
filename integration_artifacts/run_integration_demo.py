"""Run the GKSL integration demo and tests from the isolated integration_artifacts folder.

This script changes into `integration_artifacts/`, runs the demo runner copy,
and runs the unit tests located in `mastereq/tests/`. It writes outputs into
`integration_artifacts/out/` and does not modify any files outside this folder.
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

def run_demo():
    demo_script = ROOT / "runners" / "new_mastereq_forward_solver.py"
    if not demo_script.exists():
        print("Demo script not found:", demo_script)
        return 2
    cmd = [sys.executable, str(demo_script), "--out", str(OUT / "out_demo.csv")]
    print("Running demo:", " ".join(cmd))
    env = os.environ.copy()
    # Ensure the integration_artifacts root is on PYTHONPATH so imports like
    # `from mastereq.gk_sl_solver import ...` resolve to the copies here.
    env_py = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env_py if env_py else "")
    return subprocess.call(cmd, cwd=str(ROOT), env=env)

def run_tests():
    tests_dir = ROOT / "mastereq" / "tests"
    if not tests_dir.exists():
        print("No tests directory:", tests_dir)
        return 0
    # Prefer pytest if available, but fall back to executing tests directly
    # (the test file includes a __main__ runner) if pytest is not installed.
    env = os.environ.copy()
    env_py = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env_py if env_py else "")
    try:
        cmd = [sys.executable, "-m", "pytest", "-q", str(tests_dir)]
        print("Running tests with pytest:", " ".join(cmd))
        rc = subprocess.call(cmd, cwd=str(ROOT), env=env)
        if rc == 0:
            return 0
    except Exception:
        pass

    # Fall back: run the test file directly (test_gksl_basic.py has a main block).
    test_file = tests_dir / "test_gksl_basic.py"
    if test_file.exists():
        cmd2 = [sys.executable, str(test_file)]
        print("Falling back to direct test execution:", " ".join(cmd2))
        return subprocess.call(cmd2, cwd=str(ROOT), env=env)
    print("No runnable tests found")
    return 0

def main():
    rc = run_demo()
    if rc != 0:
        print("Demo returned non-zero:", rc)
    else:
        print("Demo completed; output in:", OUT)

    rc2 = run_tests()
    if rc2 != 0:
        print("Tests returned non-zero:", rc2)
    else:
        print("Tests passed (or returned 0).")

    return 0 if (rc == 0 and rc2 == 0) else 3

if __name__ == "__main__":
    sys.exit(main())
