from __future__ import annotations

import os
from pathlib import Path


def load_local_env(filename: str = ".env") -> None:
    """Load KEY=VALUE pairs from project-local .env if present."""
    env_path = Path(__file__).resolve().parents[1] / filename
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def require_env(*keys: str) -> dict[str, str]:
    missing = [key for key in keys if not os.environ.get(key)]
    if missing:
        raise RuntimeError(
            "Variabili ambiente mancanti: "
            + ", ".join(missing)
            + ". Compila automation/python/sharepoint-ms/.env"
        )
    return {key: os.environ[key] for key in keys}
