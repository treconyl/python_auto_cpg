from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

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
    node_candidates.append(settings.PLAYWRIGHT_DIR / "node_modules")
    node_candidates.append(settings.REPO_ROOT / "node_modules")
    node_candidates.append(Path.cwd() / "node_modules")

    for candidate in node_candidates:
        if candidate.exists():
            env["NODE_PATH"] = str(candidate)
            break

    return env


def resolve_node_bin() -> str:
    env_node_bin = os.environ.get("PLAYWRIGHT_NODE_BIN")
    if env_node_bin:
        candidate = Path(env_node_bin)
        if candidate.exists():
            return str(candidate)

    node_bin = shutil.which("node")
    if node_bin:
        return node_bin

    if sys.platform == "win32":
        candidates = [
            Path(os.environ.get("ProgramFiles", r"C:\\Program Files")) / "nodejs" / "node.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)")) / "nodejs" / "node.exe",
            Path.home() / "AppData" / "Local" / "Programs" / "nodejs" / "node.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

    return "node"
