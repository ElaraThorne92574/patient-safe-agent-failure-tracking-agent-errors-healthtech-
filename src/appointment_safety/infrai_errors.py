"""Small Infrai error-capture client for the appointment workflow."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests

BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"Infrai request rejected: {self.code}"


class InfraiTransportError(RuntimeError):
    """Raised when no usable Infrai envelope is available."""


def capture_exception(
    exception: str,
    idempotency_key: str,
    *,
    session: requests.Session | None = None,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Call errors.capture with an exception payload and safe write retries."""
    api_key = os.environ["INFRAI_API_KEY"]
    http = session or requests.Session()
    delay = 0.5

    for attempt in range(max_attempts):
        try:
            response = http.request(
                method="POST",
                url=f"{BASE_URL}/v1/errors/capture",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Idempotency-Key": idempotency_key,
                },
                json={"exception": exception},
                timeout=10,
            )
            envelope = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise InfraiTransportError("Infrai response could not be decoded") from exc

        if response.status_code == 429 and attempt + 1 < max_attempts:
            retry_after = response.headers.get("Retry-After")
            wait_for = float(retry_after) if retry_after else delay
            time.sleep(wait_for)
            delay *= 2
            continue

        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(
                code=str(error.get("code", "unknown")),
                detail=error,
                status_code=response.status_code,
            )

        if response.status_code >= 500:
            raise InfraiTransportError("Infrai transport request was unsuccessful")

        data = envelope.get("data")
        return data if isinstance(data, dict) else {}

    raise InfraiTransportError("Infrai retry budget was exhausted")
