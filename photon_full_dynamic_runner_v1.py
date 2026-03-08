#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> int:
    target = Path(__file__).resolve().parent / "CODE" / "photon_dynamic_full_runner_v1.py"
    spec = importlib.util.spec_from_file_location("_photon_dynamic_full_runner_v1", str(target))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load {target}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
