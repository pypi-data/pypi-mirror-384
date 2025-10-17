# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Mapping

from .http import HTTP


class _BaseOps:
    def __init__(self, http: HTTP, base: str) -> None:
        self._http = http
        self._base = base

    def query(self, **params) -> Any:
        return self._http.request("GET", self._base, params=params)

    def get(self, id: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}")

    def create(self, body: Mapping[str, Any]) -> Any:
        return self._http.request("POST", self._base, json_body=body)

    def label(self, id: str, body: Mapping[str, Any]) -> Any:
        return self._http.request("PATCH", f"{self._base}/{id}/labels", json_body=body)

    def delete(self, id: str) -> Any:
        return self._http.request("PUT", f"{self._base}/{id}/delete")

    def documentation(self, id: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/documentation")

    def edit_documentation(self, id: str, body: Mapping[str, Any]) -> Any:
        return self._http.request(
            "PATCH", f"{self._base}/{id}/documentation", json_body=body
        )

    def logs(self, id: str, **params) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/logs", params=params)

    def downlinks(self, id: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/downlinks")


class ChallengesOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/challenges")

    def create_task(self, id: str, body: Mapping[str, Any]) -> Any:
        return self._http.request("POST", f"{self._base}/{id}/tasks", json_body=body)

    def create_team(self, id: str, body: Mapping[str, Any]) -> Any:
        return self._http.request("POST", f"{self._base}/{id}/teams", json_body=body)

    def edit_content(self, id: str, body: Mapping[str, Any]) -> Any:
        return self._http.request("PATCH", f"{self._base}/{id}/content", json_body=body)

    def teams(self, id: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/teams")


class DatasetsOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/datasets")

    def upload(self, id: str, file_path: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/upload/{file_path}")

    def finalize(self, id: str) -> Any:
        return self._http.request("POST", f"{self._base}/{id}/finalize")


class EvaluationsOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/evaluations")


class FamiliesOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/families")

    def edit_members(self, id: str, body: Mapping[str, Any]) -> Any:
        return self._http.request("PATCH", f"{self._base}/{id}/members", json_body=body)


class InferenceServicesOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/inferenceservices")


class InferenceSessionsOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/inferencesessions")

    def token(self, id: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/token")

    def terminate(self, id: str) -> Any:
        return self._http.request("POST", f"{self._base}/{id}/terminate")

    def ready(self, id: str) -> Any:
        return self._http.request("POST", f"{self._base}/{id}/ready")


class MeasurementsOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/measurements")


class MethodsOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/methods")


class ModelsOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/models")

    def upload(self, id: str, file_path: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/upload/{file_path}")

    def finalize(self, id: str) -> Any:
        return self._http.request("POST", f"{self._base}/{id}/finalize")


class ModulesOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/modules")

    def upload(self, id: str, file_path: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/upload/{file_path}")

    def finalize(self, id: str) -> Any:
        return self._http.request("POST", f"{self._base}/{id}/finalize")


class ReportsOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/reports")

    def scores(self, id: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/scores")

    def query_scores(self, **params) -> Any:
        return self._http.request("GET", f"{self._base}/scores", params=params)


class SafetyCasesOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/safetycases")

    def scores(self, id: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}/scores")

    def query_scores(self, **params) -> Any:
        return self._http.request("GET", f"{self._base}/scores", params=params)


class TeamsOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        self._http = http
        self._base = "/teams"

    def query(self, **params) -> Any:
        return self._http.request("GET", self._base, params=params)

    def get(self, id: str) -> Any:
        return self._http.request("GET", f"{self._base}/{id}")

    def label(self, id: str, body: Mapping[str, Any]) -> Any:
        return self._http.request("PATCH", f"{self._base}/{id}/labels", json_body=body)


class UseCasesOperations(_BaseOps):
    def __init__(self, http: HTTP) -> None:
        super().__init__(http, "/usecases")


class Raw:
    def __init__(self, http: HTTP) -> None:
        self.challenges = ChallengesOperations(http)
        self.datasets = DatasetsOperations(http)
        self.evaluations = EvaluationsOperations(http)
        self.families = FamiliesOperations(http)
        self.inferenceservices = InferenceServicesOperations(http)
        self.inferencesessions = InferenceSessionsOperations(http)
        self.measurements = MeasurementsOperations(http)
        self.methods = MethodsOperations(http)
        self.models = ModelsOperations(http)
        self.modules = ModulesOperations(http)
        self.reports = ReportsOperations(http)
        self.safetycases = SafetyCasesOperations(http)
        self.teams = TeamsOperations(http)
        self.usecases = UseCasesOperations(http)
