# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Mapping, Optional

from .http import HTTP


class RawOps:
    """Very thin wrapper exposing method+path helpers used by API groups."""

    def __init__(self, http: HTTP) -> None:
        self._http = http

    def get(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        return self._http.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        return self._http.request(
            "POST", path, json_body=json, data=data, files=files, headers=headers
        )

    def put(
        self,
        path: str,
        *,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        return self._http.request(
            "PUT", path, json_body=json, data=data, files=files, headers=headers
        )

    def patch(
        self,
        path: str,
        *,
        json: Any = None,
        data: Any = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        return self._http.request(
            "PATCH", path, json_body=json, data=data, headers=headers
        )

    def delete(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        return self._http.request(
            "DELETE",
            path,
            params=params,
            headers=headers,
            expected_status=(200, 202, 204),
        )


__all__ = ["RawOps"]
