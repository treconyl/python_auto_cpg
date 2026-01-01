from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from app.services import db, proxy_api


def list_proxies() -> list[dict[str, Any]]:
    with db.session() as connection:
        rows = db.execute_with_retry(
            connection,
            "SELECT * FROM proxy_keys ORDER BY label ASC;",
        ).fetchall()
    results = []
    for row in rows:
        payload = dict(row)
        meta = payload.get("meta")
        payload["meta"] = json.loads(meta) if meta else {}
        results.append(payload)
    return results


def get_proxy(proxy_id: int) -> dict[str, Any] | None:
    with db.session() as connection:
        row = db.execute_with_retry(
            connection,
            "SELECT * FROM proxy_keys WHERE id = ?;",
            (proxy_id,),
        ).fetchone()
    if not row:
        return None
    payload = dict(row)
    meta = payload.get("meta")
    payload["meta"] = json.loads(meta) if meta else {}
    return payload


def create_proxy(payload: dict[str, Any]) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.session() as connection:
        db.execute_with_retry(
            connection,
            """
            INSERT INTO proxy_keys (label, api_key, is_active, status, stop_requested, meta, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """.strip(),
            (
                payload["label"],
                payload["api_key"],
                1 if payload.get("is_active", True) else 0,
                payload.get("status", "idle"),
                0,
                json.dumps(payload.get("meta") or {}),
                now,
                now,
            ),
        )


def update_proxy(proxy_id: int, payload: dict[str, Any]) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.session() as connection:
        db.execute_with_retry(
            connection,
            """
            UPDATE proxy_keys
            SET label = ?, api_key = ?, is_active = ?, status = ?, meta = ?, updated_at = ?
            WHERE id = ?;
            """.strip(),
            (
                payload["label"],
                payload["api_key"],
                1 if payload.get("is_active", True) else 0,
                payload.get("status", "idle"),
                json.dumps(payload.get("meta") or {}),
                now,
                proxy_id,
            ),
        )


def stats() -> dict[str, int]:
    with db.session() as connection:
        total = db.execute_with_retry(connection, "SELECT COUNT(*) FROM proxy_keys;").fetchone()[0]
        running = db.execute_with_retry(
            connection,
            "SELECT COUNT(*) FROM proxy_keys WHERE status = 'running';",
        ).fetchone()[0]
    return {"total": total, "running": running}


def update_proxy_meta(proxy_id: int, meta: dict[str, Any]) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.session() as connection:
        db.execute_with_retry(
            connection,
            "UPDATE proxy_keys SET meta = ?, updated_at = ? WHERE id = ?;",
            (json.dumps(meta), now, proxy_id),
        )


def set_proxy_status(proxy_id: int, status: str, is_active: bool | None = None) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.session() as connection:
        if is_active is None:
            db.execute_with_retry(
                connection,
                "UPDATE proxy_keys SET status = ?, updated_at = ? WHERE id = ?;",
                (status, now, proxy_id),
            )
            return
        db.execute_with_retry(
            connection,
            "UPDATE proxy_keys SET status = ?, is_active = ?, updated_at = ? WHERE id = ?;",
            (status, 1 if is_active else 0, now, proxy_id),
        )


def test_proxy(proxy: dict[str, Any]) -> dict[str, Any]:
    return proxy_api.request_proxy(proxy["api_key"])


def rotate_proxy(proxy: dict[str, Any]) -> dict[str, Any]:
    return proxy_api.request_proxy(proxy["api_key"])


def stop_proxy(proxy_id: int) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with db.session() as connection:
        db.execute_with_retry(
            connection,
            "UPDATE proxy_keys SET stop_requested = 1, status = 'expired', is_active = 0, updated_at = ? WHERE id = ?;",
            (now, proxy_id),
        )


def should_rotate(meta: dict[str, Any], cooldown_seconds: int = 60) -> bool:
    last_rotated_at = meta.get("last_proxy_rotated_at")
    if not last_rotated_at:
        return True
    try:
        rotated_time = datetime.fromisoformat(str(last_rotated_at))
    except ValueError:
        return True
    return (datetime.utcnow() - rotated_time).total_seconds() >= cooldown_seconds


def apply_proxy_payload(proxy_id: int, meta: dict[str, Any], payload: dict[str, Any]) -> None:
    meta["last_proxy_response"] = payload
    meta["last_proxy_http"] = payload.get("proxyhttp")
    meta["last_proxy_socks"] = payload.get("proxysocks5")
    meta["last_proxy_username"] = payload.get("username")
    meta["last_proxy_password"] = payload.get("password")
    meta["last_proxy_rotated_at"] = datetime.utcnow().isoformat(timespec="seconds")
    if payload.get("status") == 100:
        meta["last_proxy_expire_at"] = payload.get("Token expiration date")
        set_proxy_status(proxy_id, "running", is_active=True)
    else:
        set_proxy_status(proxy_id, "expired", is_active=False)
    update_proxy_meta(proxy_id, meta)
