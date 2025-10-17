# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
from typing import Callable, MutableMapping, Optional, Tuple


class TokenAuth:
    """Minimal bearer-token auth helper.

    Optionally accepts a refresh() callback that returns (token, exp_ts).
    """

    def __init__(
        self, token: str, refresh: Optional[Callable[[], Tuple[str, int]]] = None
    ) -> None:
        self._token = token
        self._refresh = refresh
        self._exp_ts: int = 0

    def update_token(self, token: str, exp_ts: Optional[int] = None) -> None:
        self._token = token
        if exp_ts is not None:
            self._exp_ts = int(exp_ts)

    def apply(self, headers: MutableMapping[str, str]) -> None:
        if self._refresh and self._exp_ts and time.time() >= self._exp_ts - 60:
            new_token, new_exp = self._refresh()
            self.update_token(new_token, new_exp)
        headers["Authorization"] = f"Bearer {self._token}"


__all__ = ["TokenAuth"]
