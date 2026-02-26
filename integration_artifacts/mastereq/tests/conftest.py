from __future__ import annotations

import sys
from pathlib import Path

# Ensure imports like `from mastereq...` resolve when pytest is run from repo root.
_INTEGRATION_ROOT = Path(__file__).resolve().parents[2]
if str(_INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(_INTEGRATION_ROOT))
