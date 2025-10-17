# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import warnings
from typing import Any, Optional

import httpx
from httpx import Timeout

from dyff.schema.adapters import Adapter


class InferenceSessionClient:
    """A client used for making inference requests to a running
    :class:`~dyff.schema.platform.InferenceSession`.

    .. note::

        Do not instantiate this class. Create an instance using
        :meth:`inferencesessions.client() <dyff.client._apigroups._InferenceSessions.client>`
    """

    def __init__(
        self,
        *,
        session_id: str,
        token: str,
        dyff_api_endpoint: str,
        inference_endpoint: str,
        input_adapter: Optional[Adapter] = None,
        output_adapter: Optional[Adapter] = None,
        verify_ssl_certificates: bool = True,
        insecure: bool = False,
    ):
        if not verify_ssl_certificates and insecure:
            raise ValueError("verify_ssl_certificates is deprecated; use insecure")
        if not verify_ssl_certificates:
            warnings.warn(
                "verify_ssl_certificates is deprecated; use insecure",
                DeprecationWarning,
            )
        self._insecure = insecure or not verify_ssl_certificates

        self._session_id = session_id
        self._token = token
        self._dyff_api_endpoint = dyff_api_endpoint

        self._inference_endpoint = inference_endpoint
        self._input_adapter = input_adapter
        self._output_adapter = output_adapter

        self._client = httpx.Client(timeout=Timeout(5, read=None), verify=not insecure)

    def infer(self, body: Any) -> Any:
        """Make an inference request.

        The input and output are arbitrary JSON objects. The required format depends on
        the endpoint and input/output adapters specified when creating the inference
        client.

        :param body: A JSON object containing the inference input.
        :returns: A JSON object containing the inference output.
        """
        url = httpx.URL(
            f"{self._dyff_api_endpoint}/inferencesessions"
            f"/{self._session_id}/infer/{self._inference_endpoint}"
        )
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self._token}",
        }

        def once(x):
            yield x

        body = once(body)
        if self._input_adapter is not None:
            body = self._input_adapter(body)
        request_body = None
        for i, x in enumerate(body):
            if i > 0:
                raise ValueError("adapted input should contain exactly one element")
            request_body = x
        if request_body is None:
            raise ValueError("adapted input should contain exactly one element")

        request = self._client.build_request(
            "POST", url, headers=headers, json=request_body
        )
        response = self._client.send(request, stream=True)
        response.raise_for_status()
        response.read()
        json_response = once(response.json())
        if self._output_adapter is not None:
            json_response = self._output_adapter(json_response)
        return list(json_response)


__all__ = [
    "InferenceSessionClient",
]
