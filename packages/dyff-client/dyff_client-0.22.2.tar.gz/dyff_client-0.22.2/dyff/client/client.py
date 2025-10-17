# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import warnings
from typing import Optional, Union

from httpx import Timeout

from dyff.schema.platform import (
    DyffEntityType,
    Entities,
    EntityIdentifier,
    EntityKindLiteral,
)

from ._apigroups import (
    _Artifacts,
    _Audits,
    _Challenges,
    _Datasets,
    _Evaluations,
    _Families,
    _InferenceServices,
    _InferenceSessions,
    _Measurements,
    _Methods,
    _Models,
    _Modules,
    _Reports,
    _SafetyCases,
    _Teams,
    _UseCases,
)
from .auth import TokenAuth
from .http import HTTP
from .ops import Raw as RawOps

_APIGroupType = Union[
    _Artifacts,
    _Challenges,
    _Datasets,
    _Evaluations,
    _Families,
    _InferenceServices,
    _InferenceSessions,
    _Measurements,
    _Methods,
    _Models,
    _Modules,
    _Reports,
    _SafetyCases,
    _Teams,
    _UseCases,
    _Audits,
]


class Client:
    """Python client for the Dyff Platform API (no AutoRest).

    Groups operations by resource type; e.g. ``client.models.create(...)``.
    """

    def __init__(
        self,
        *,
        api_token: Optional[str] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        registry_url: Optional[str] = None,
        verify_ssl_certificates: bool = True,
        insecure: bool = False,
        timeout: Optional[Timeout] = None,
        retries: int = 3,
        backoff: float = 0.5,
        default_headers: Optional[dict[str, str]] = None,
    ):
        """
        :param str api_token: API token for authentication. If not provided,
            reads DYFF_API_TOKEN from the environment.
        :param str api_key: Deprecated alias for 'api_token'.
            .. deprecated:: 0.13.1  Use api_token instead.
        :param str endpoint: Base URL of the Dyff API. Defaults to DYFF_API_ENDPOINT
            or https://api.dyff.io/v0 if unset.
        :param bool verify_ssl_certificates: (deprecated) use 'insecure' instead.
        :param bool insecure: Disable TLS certificate verification (testing only).
        :param Timeout timeout: httpx.Timeout for requests; defaults to 5s.
        :param int retries: Transient retry attempts (408/429/5xx).
        :param float backoff: Initial backoff in seconds (exponential).
        :param dict default_headers: Headers applied to every request.
        """
        if not verify_ssl_certificates and insecure:
            raise ValueError("verify_ssl_certificates is deprecated; use insecure")
        if not verify_ssl_certificates:
            warnings.warn(
                "verify_ssl_certificates is deprecated; use insecure",
                DeprecationWarning,
            )
        self._insecure = insecure or not verify_ssl_certificates

        if api_token is None:
            api_token = api_key or os.environ.get("DYFF_API_TOKEN")
        if api_token is None:
            raise ValueError(
                "Must provide api_token or set DYFF_API_TOKEN environment variable"
            )
        self._api_token = api_token

        if endpoint is None:
            endpoint = os.environ.get("DYFF_API_ENDPOINT", "https://api.dyff.io/v0")
        self._endpoint = endpoint

        self._timeout = timeout or Timeout(5.0)
        _t: float
        try:
            _t = float(getattr(self._timeout, "timeout", None) or 5.0)
        except Exception:
            _t = 5.0
        if registry_url is None:
            registry_url = os.environ.get(
                "DYFF_REGISTRY_URL", "https://registry.dyff.io"
            )
        self._registry_url = registry_url

        self._timeout = timeout or Timeout(5.0)  # Same as httpx default

        self._http = HTTP(
            base_url=self._endpoint,
            auth=TokenAuth(self._api_token),
            headers=default_headers,
            timeout=_t,
            retries=retries,
            backoff=backoff,
            verify=not self._insecure,
        )

        self._raw = RawOps(self._http)

        self._artifacts = _Artifacts(self)
        self._challenges = _Challenges(self)
        self._datasets = _Datasets(self)
        self._evaluations = _Evaluations(self)
        self._families = _Families(self)
        self._inferenceservices = _InferenceServices(self)
        self._inferencesessions = _InferenceSessions(self)
        self._measurements = _Measurements(self)
        self._methods = _Methods(self)
        self._models = _Models(self)
        self._modules = _Modules(self)
        self._reports = _Reports(self)
        self._safetycases = _SafetyCases(self)
        self._teams = _Teams(self)
        self._usecases = _UseCases(self)

        self._apigroups_by_kind: dict[Entities, _APIGroupType] = {
            # getattr(Entities, "Audit", None) or Entities("Audit"): self._audits,
            Entities.Artifact: self._artifacts,
            Entities.Challenge: self._challenges,
            Entities.Dataset: self._datasets,
            Entities.Evaluation: self._evaluations,
            Entities.Family: self._families,
            Entities.InferenceService: self._inferenceservices,
            Entities.InferenceSession: self._inferencesessions,
            Entities.Measurement: self._measurements,
            Entities.Method: self._methods,
            Entities.Module: self._modules,
            Entities.Report: self._reports,
            Entities.SafetyCase: self._safetycases,
            Entities.Team: self._teams,
            Entities.UseCase: self._usecases,
        }

    @property
    def insecure(self) -> bool:
        return self._insecure

    @property
    def timeout(self) -> Timeout:
        return self._timeout

    @property
    def raw(self) -> RawOps:
        """Low-level ops namespace with per-resource groups (datasets, models, …)"""
        return self._raw

    def apigroup(self, kind: Entities | EntityKindLiteral) -> _APIGroupType:
        """Get the API group by kind."""
        kind = Entities(kind)
        return self._apigroups_by_kind[kind]  # type: ignore[return-value]

    def get(self, entity: EntityIdentifier) -> DyffEntityType:
        """Get an entity by identifier (id + kind)."""
        return self.apigroup(entity.kind).get(entity.id)

    @property
    def artifacts(self) -> _Artifacts:
        """Operations on :class:`~dyff.schema.platform.OCIArtifact` entities."""
        return self._artifacts

    @property
    def challenges(self) -> _Challenges:
        return self._challenges

    @property
    def datasets(self) -> _Datasets:
        return self._datasets

    @property
    def evaluations(self) -> _Evaluations:
        return self._evaluations

    @property
    def families(self) -> _Families:
        return self._families

    @property
    def inferenceservices(self) -> _InferenceServices:
        return self._inferenceservices

    @property
    def inferencesessions(self) -> _InferenceSessions:
        return self._inferencesessions

    @property
    def methods(self) -> _Methods:
        return self._methods

    @property
    def measurements(self) -> _Measurements:
        return self._measurements

    @property
    def models(self) -> _Models:
        return self._models

    @property
    def modules(self) -> _Modules:
        return self._modules

    @property
    def reports(self) -> _Reports:
        return self._reports

    @property
    def safetycases(self) -> _SafetyCases:
        return self._safetycases

    @property
    def teams(self) -> _Teams:
        return self._teams

    @property
    def usecases(self) -> _UseCases:
        return self._usecases


__all__ = [
    "Client",
    "Timeout",
]
