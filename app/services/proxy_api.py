from __future__ import annotations

from typing import Any

import requests

from app.config import settings


class ProxyApiError(Exception):
    pass


def request_proxy(api_key: str, nhamang: str = "random", tinhthanh: int = 0) -> dict[str, Any]:
    try:
        response = requests.get(
            settings.PROXY_API_URL,
            params={"key": api_key, "nhamang": nhamang, "tinhthanh": tinhthanh},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise ProxyApiError(str(exc)) from exc
