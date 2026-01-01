from __future__ import annotations

from typing import Any

from app.services import accounts_service, garena_service


def run_garena_job(credentials: dict[str, Any]) -> int:
    account_id = credentials.get("account_id")
    if account_id:
        accounts_service.update_account_status(account_id, "processing")

    code, last_line = garena_service.run_playwright(credentials)

    if account_id:
        if code == 0:
            accounts_service.mark_success(account_id, credentials.get("new_password") or "")
        else:
            accounts_service.mark_failed(account_id, last_line or "Playwright error")

    return code
