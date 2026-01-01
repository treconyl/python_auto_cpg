from __future__ import annotations

import subprocess
import threading
import time
from datetime import datetime
from app.config import settings
from app.services.runner_env import build_node_env, resolve_node_bin

_lock = threading.Lock()
_processes: list[subprocess.Popen[str]] = []
_stop_event = threading.Event()


def run_001proxy_test() -> int:
    script = settings.PLAYWRIGHT_DIR / "001proxy-test.js"
    log_path = settings.LOG_DIR / "001proxy.log"
    if not script.exists():
        log_path.write_text(f"{datetime.utcnow().isoformat()} missing script: {script}\n", encoding="utf-8")
        return 1
    process = subprocess.Popen(
        [resolve_node_bin(), str(script)],
        cwd=str(settings.PLAYWRIGHT_DIR.parent),
        env=build_node_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    with _lock:
        _processes.append(process)

    try:
        if process.stdout:
            with log_path.open("a", encoding="utf-8") as handle:
                for line in process.stdout:
                    handle.write(line)
        return process.wait()
    finally:
        with _lock:
            if process in _processes:
                _processes.remove(process)


def run_001proxy_loop() -> None:
    while not _stop_event.is_set():
        run_001proxy_test()
        time.sleep(1)


def stop_all() -> None:
    _stop_event.set()
    with _lock:
        active = list(_processes)

    for process in active:
        try:
            process.terminate()
        except Exception:
            continue

    for process in active:
        try:
            process.wait(timeout=3)
        except Exception:
            try:
                process.kill()
            except Exception:
                continue


def reset_stop() -> None:
    _stop_event.clear()
