# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
from typing import Any, Dict, Mapping, Optional, Tuple

import httpx

from .errors import HTTPError, TransportError, explain

DEFAULT_TIMEOUT: float = 30.0
_TRANSIENT_STATUSES = (408, 429, 500, 502, 503, 504)


class HTTP:
    """
    Tiny HTTP transport on top of httpx with:
      - base_url handling
      - optional auth hook (object with .apply(headers))
      - retries with exponential backoff on transient statuses
      - optional default headers
    """

    def __init__(
        self,
        base_url: str,
        auth: Optional[object] = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = 3,
        backoff: float = 0.5,
        headers: Optional[Mapping[str, str]] = None,
        verify: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = float(timeout)
        self.retries = int(retries)
        self.backoff = float(backoff)
        self._base_headers = dict(headers or {})
        self._client = httpx.Client(timeout=self.timeout, verify=verify)

    # ---- context management -------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HTTP":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ---- internals ----------------------------------------------------------

    def _prepare_headers(self, headers: Optional[Mapping[str, str]]) -> Dict[str, str]:
        final = dict(self._base_headers)
        if headers:
            final.update(headers)
        if self.auth and hasattr(self.auth, "apply"):
            # type: ignore[attr-defined]
            self.auth.apply(final)
        return final

    def _request_once(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json_body: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        hdrs = self._prepare_headers(headers)
        return self._client.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            data=data,
            files=files,
            headers=hdrs,
        )

    # ---- public API ---------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json_body: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        expected_status: Tuple[int, ...] = (200, 201, 202, 204),
    ) -> Any:
        last_exc: Optional[Exception] = None

        for attempt in range(self.retries + 1):
            try:
                resp = self._request_once(
                    method,
                    path,
                    params=params,
                    json_body=json_body,
                    data=data,
                    files=files,
                    headers=headers,
                )
            except httpx.HTTPError as e:
                last_exc = e
                if attempt < self.retries:
                    time.sleep(self.backoff * (2**attempt))
                    continue
                raise TransportError(str(e)) from e

            sc = resp.status_code
            if sc in expected_status:
                if sc == 204 or resp.headers.get("content-length") == "0":
                    return None
                ct = resp.headers.get("content-type", "").lower()
                if "application/json" in ct:
                    return resp.json()
                return resp.content

            if sc in _TRANSIENT_STATUSES and attempt < self.retries:
                retry_after = resp.headers.get("retry-after")
                sleep_s = (
                    float(retry_after) if retry_after else self.backoff * (2**attempt)
                )
                time.sleep(sleep_s)
                continue

            # Hard failure
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text
            raise HTTPError(sc, explain(sc, payload), payload)

        # Should not reach here
        raise TransportError(str(last_exc) if last_exc else "unknown transport error")


__all__ = ["HTTP", "DEFAULT_TIMEOUT"]
