# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Optional


class DyffClientError(Exception):
    """Base exception for dyff-client."""


class TransportError(DyffClientError):
    """Network/transport-level failure (connection, timeout, etc.)."""


class HTTPError(DyffClientError):
    """HTTP-layer error with code and optional payload."""

    def __init__(
        self, status: int, message: str, payload: Optional[Any] = None
    ) -> None:
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.payload = payload

    @property
    def status_code(self) -> int:
        return self.status


class HttpResponseError(HTTPError):
    """Backwards-compatible alias for the old azure.core.exceptions.HttpResponseError.

    Accepts 'status_code=' like the old type.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        *,
        status: Optional[int] = None,
        payload: Any = None,
        **_: Any,
    ) -> None:
        code = (
            status_code
            if status_code is not None
            else (status if status is not None else 0)
        )
        super().__init__(code, message, payload)


def explain(status: int, data: Any) -> str:
    if isinstance(data, dict):
        for key in ("detail", "message", "error", "reason"):
            if key in data and data[key]:
                return str(data[key])
    return "Request failed"


__all__ = [
    "DyffClientError",
    "TransportError",
    "HTTPError",
    "HttpResponseError",
    "explain",
]
