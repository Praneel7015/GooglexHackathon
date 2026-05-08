"""
NammaCity ADK App — entry point for `adk web` and `adk run`.
Exposes `root_agent` so the ADK dev server discovers NammaCity automatically.
"""

import os
import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
# Ensure the backend root is on sys.path so all NammaCity imports resolve
_BACKEND_ROOT = Path(__file__).parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# ── Load .env before any NammaCity imports (ADK web doesn't auto-load it) ────
_env_file = _BACKEND_ROOT / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

# ── Build root_agent ──────────────────────────────────────────────────────────
# ADK web discovers packages via the `root_agent` variable.
from agents.adk_agent import _build_orchestrator_agent  # noqa: E402

root_agent = _build_orchestrator_agent()
