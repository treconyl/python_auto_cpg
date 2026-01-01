from __future__ import annotations

import os
from pathlib import Path

from app.config import settings


def build_node_env() -> dict[str, str]:
    env = os.environ.copy()
    path = env.get("PATH", "")
    extra_paths = ["/opt/homebrew/bin", "/usr/local/bin"]
    for extra in extra_paths:
        if extra not in path:
            path = f"{extra}{os.pathsep}{path}"
    env["PATH"] = path

    node_candidates: list[Path] = []
    env_node_path = env.get("PLAYWRIGHT_NODE_PATH")
    if env_node_path:
        node_candidates.append(Path(env_node_path))
    node_candidates.append(settings.REPO_ROOT / "node_modules")
    node_candidates.append(Path.cwd() / "node_modules")
    node_candidates.append(Path.home() / "github" / "native-php" / "node_modules")

    for candidate in node_candidates:
        if candidate.exists():
            env["NODE_PATH"] = str(candidate)
            break

    return env
