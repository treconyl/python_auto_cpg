from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.runner_env import build_node_env


def run_playwright(credentials: dict[str, Any]) -> tuple[int, str | None]:
    script = settings.PLAYWRIGHT_DIR / "garena-runner.js"

    env = build_node_env()
    env.update(
        {
            "GARENA_USERNAME": credentials["username"],
            "GARENA_PASSWORD": credentials["password"],
            "GARENA_NEW_PASSWORD": credentials.get("new_password") or settings.DEFAULT_NEW_PASSWORD,
            "PLAYWRIGHT_HEADLESS": "true" if credentials.get("headless") else "false",
        }
    )

    if credentials.get("proxy_key_id"):
        env["PLAYWRIGHT_PROXY_KEY_ID"] = str(credentials["proxy_key_id"])
        env["PLAYWRIGHT_PROXY_LABEL"] = credentials.get("proxy_label", "")

    process = subprocess.Popen(
        ["node", str(script)],
        cwd=str(settings.PLAYWRIGHT_DIR.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    last_line = None
    with settings.LOG_FILE.open("a", encoding="utf-8") as handle:
        if process.stdout:
            for line in process.stdout:
                handle.write(line)
                if line.strip():
                    last_line = line.strip()

    return process.wait(), last_line
