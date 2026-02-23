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
    # Use the cleaned runner that depends on the unified GKSL API
    demo_script = ROOT / "runners" / "new_mastereq_forward_solver_clean.py"
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
    # Run the weak and strong integration tests (prefer pytest, fallback to direct execution)
    test_files = [
        tests_dir / "test_weak_integration.py",
        tests_dir / "test_strong_integration.py",
        tests_dir / "test_em_integration.py",
        tests_dir / "test_dm_integration.py",
    ]
    any_failed = False
    for tf in test_files:
        if not tf.exists():
            print("Test not found, skipping:", tf)
            continue
        try:
            cmd = [sys.executable, "-m", "pytest", "-q", str(tf)]
            print("Running tests with pytest:", " ".join(cmd))
            rc = subprocess.call(cmd, cwd=str(ROOT), env=env)
            if rc != 0:
                any_failed = True
                # continue to attempt other tests
                continue
            else:
                continue
        except Exception:
            pass

        # Fallback direct run
        cmd2 = [sys.executable, str(tf)]
        print("Falling back to direct test execution:", " ".join(cmd2))
        rc2 = subprocess.call(cmd2, cwd=str(ROOT), env=env)
        if rc2 != 0:
            any_failed = True

    return 1 if any_failed else 0

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
