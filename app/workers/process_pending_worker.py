from __future__ import annotations

import time

from app.services import accounts_service, proxies_service
from app.workers.run_garena_worker import run_garena_job


def process_pending_for_proxy(proxy: dict[str, object]) -> None:
    meta = dict(proxy.get("meta") or {})
    if not proxies_service.should_rotate(meta):
        return

    try:
        payload = proxies_service.rotate_proxy(proxy)
    except Exception:
        return

    proxies_service.apply_proxy_payload(int(proxy["id"]), meta, payload)

    if payload.get("status") != 100:
        return

    new_password = accounts_service.generate_password()
    account = accounts_service.claim_next_account(new_password)
    if not account:
        return

    credentials = {
        "account_id": account["id"],
        "username": account["login"],
        "password": account.get("current_password") or "",
        "new_password": new_password,
        "proxy_key_id": proxy["id"],
        "proxy_label": proxy["label"],
        "headless": True,
    }
    run_garena_job(credentials)


def run_proxy_loop(proxy_id: int, idle_sleep: int = 10) -> None:
    while True:
        proxy = proxies_service.get_proxy(proxy_id)
        if not proxy:
            return
        if proxy.get("stop_requested") or not proxy.get("is_active") or proxy.get("status") == "expired":
            return

        meta = dict(proxy.get("meta") or {})
        if not proxies_service.should_rotate(meta):
            time.sleep(2)
            continue

        try:
            payload = proxies_service.rotate_proxy(proxy)
        except Exception:
            time.sleep(idle_sleep)
            continue

        proxies_service.apply_proxy_payload(proxy_id, meta, payload)

        if payload.get("status") != 100:
            time.sleep(idle_sleep)
            continue

        new_password = accounts_service.generate_password()
        account = accounts_service.claim_next_account(new_password)
        if not account:
            time.sleep(idle_sleep)
            continue

        credentials = {
            "account_id": account["id"],
            "username": account["login"],
            "password": account.get("current_password") or "",
            "new_password": new_password,
            "proxy_key_id": proxy["id"],
            "proxy_label": proxy["label"],
            "headless": True,
        }
        run_garena_job(credentials)
