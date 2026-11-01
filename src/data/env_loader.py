"""
Environment and Secret Loader.
Safely loads environment variables from .env if present, without exposing keys or committing them to git.
"""

import os
from pathlib import Path
from typing import Dict, Optional


def load_env_file(env_path: Optional[str] = None) -> Dict[str, str]:
    """
    Parses a key=value .env file into os.environ if the key is not already set.
    Avoids overwriting existing process environment variables.
    """
    if env_path is None:
        # Search current working directory, then user home config directory
        candidates = [
            Path(".env"),
            Path("~/.config/afterimage/.env").expanduser(),
        ]
        for c in candidates:
            if c.exists() and c.is_file():
                env_path = str(c)
                break

    loaded: Dict[str, str] = {}
    if not env_path or not Path(env_path).exists():
        return loaded

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val
                    loaded[key] = val
    except Exception:
        pass

    return loaded
