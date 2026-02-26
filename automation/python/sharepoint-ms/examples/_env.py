"""
Utility helpers for loading .env files in example scripts.

The .env file is searched in the following order:
1. Project root  (parent directory of the ``examples/`` folder)
2. Current working directory

Existing environment variables are never overwritten.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_local_env(filename: str = ".env") -> None:
    """
    Load KEY=VALUE pairs from a ``.env`` file into ``os.environ``.

    Silently does nothing if no ``.env`` file is found.
    """
    candidates = [
        Path(__file__).resolve().parent.parent / filename,  # project root
        Path.cwd() / filename,                              # cwd fallback
    ]
    for env_path in candidates:
        if env_path.exists():
            _parse_env_file(env_path)
            return


def _parse_env_file(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def require_env(*keys: str) -> dict[str, str]:
    """
    Return a ``{key: value}`` dict for the requested environment variables.

    Raises:
        RuntimeError: If any key is missing from the environment.
    """
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
            + ".\nPlease fill in your .env file (see .env.example)."
        )
    return {k: os.environ[k] for k in keys}
