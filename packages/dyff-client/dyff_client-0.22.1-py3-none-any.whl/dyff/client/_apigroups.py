# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

# mypy: disable-error-code="import-untyped"
from __future__ import annotations

import json
import subprocess
import sys
import time
import typing
import warnings
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    AsyncIterable,
    Generic,
    Iterable,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

import httpx
import websockets
from httpx import Timeout
from tqdm.auto import tqdm

from dyff.schema.adapters import Adapter, create_pipeline
from dyff.schema.base import DyffBaseModel
from dyff.schema.dataset import arrow, binary
from dyff.schema.platform import (
    Accelerator,
    Artifact,
    ArtifactURL,
    Audit,
    Challenge,
    ChallengeTask,
    Concern,
    DataSchema,
    Dataset,
    Digest,
    Documentation,
    DyffEntity,
    DyffEntityType,
    Entities,
    Evaluation,
    Family,
    FamilyMemberBase,
    File,
    InferenceInterface,
    InferenceService,
    InferenceSession,
    InferenceSessionAndToken,
    Label,
    Measurement,
    Method,
    Model,
    ModelArtifact,
    ModelArtifactKind,
    ModelResources,
    ModelSource,
    ModelSourceKinds,
    Module,
    OCIArtifact,
    Report,
    Resources,
    SafetyCase,
    Score,
    Status,
    StorageSignedURL,
    Team,
    UseCase,
    Volume,
)
from dyff.schema.requests import (
    AnalysisCreateRequest,
    ArtifactCreateRequest,
    ChallengeContentEditRequest,
    ChallengeCreateRequest,
    ChallengeTaskCreateRequest,
    ChallengeTeamCreateRequest,
    ConcernCreateRequest,
    DatasetCreateRequest,
    DocumentationEditRequest,
    EvaluationCreateRequest,
    FamilyCreateRequest,
    FamilyMembersEditRequest,
    InferenceServiceCreateRequest,
    InferenceSessionCreateRequest,
    LabelsEditRequest,
    MethodCreateRequest,
    ModelCreateRequest,
    ModuleCreateRequest,
    ReportCreateRequest,
)
from dyff.schema.responses import WorkflowLogEntry, WorkflowLogsResponse

from ._inference import InferenceSessionClient
from .errors import HTTPError, HttpResponseError
from .ops import ChallengesOperations as ChallengesOperationsGenerated
from .ops import DatasetsOperations as DatasetsOperationsGenerated
from .ops import EvaluationsOperations as EvaluationsOperationsGenerated
from .ops import FamiliesOperations as FamiliesOperationsGenerated
from .ops import InferenceServicesOperations as InferenceServicesOperationsGenerated
from .ops import InferenceSessionsOperations as InferenceSessionsOperationsGenerated
from .ops import MeasurementsOperations as MeasurementsOperationsGenerated
from .ops import MethodsOperations as MethodsOperationsGenerated
from .ops import ModelsOperations as ModelsOperationsGenerated
from .ops import ModulesOperations as ModulesOperationsGenerated
from .ops import ReportsOperations as ReportsOperationsGenerated
from .ops import SafetyCasesOperations as SafetyCasesOperationsGenerated
from .ops import TeamsOperations as TeamsOperationsGenerated
from .ops import UseCasesOperations as UseCasesOperationsGenerated

if typing.TYPE_CHECKING:
    from .client import Client


QueryT = Union[str, dict[str, Any], list[dict[str, Any]]]


class _OpsProtocol(Protocol):
    @property
    def _insecure(self) -> bool: ...

    @property
    def _timeout(self) -> Timeout: ...

    @property
    def _raw_ops(self) -> Any: ...

    def label(self, resource_id: str, labels: dict[str, Optional[str]]) -> None:
        """Label the specified resource with key-value pairs (stored in the ``.labels``
        field of the resource).

        Providing ``None`` for the value deletes the label.

        See :class:`~dyff.schema.platform.Label` for a description of the
        constraints on label keys and values.

        :param resource_id: The ID of the resource to label.
        :param labels: The label keys and values.
        """
        ...


class _ArtifactsProtocol(_OpsProtocol, Protocol):
    def downlinks(self, id: str) -> list[ArtifactURL]: ...


def _require_id(x: DyffEntity | str) -> str:
    if isinstance(x, str):
        return x
    elif x.id is not None:
        return x.id
    else:
        raise ValueError(".id attribute not set")


def _encode_query(query: QueryT | None) -> Optional[str]:
    if query is None:
        return None
    elif isinstance(query, (list, dict)):
        query = json.dumps(query)
    return query


def _encode_labels(labels: Optional[dict[str, str]]) -> Optional[str]:
    """The Python client accepts 'annotations' and 'labels' as dicts, but they need to
    be json-encoded so that they can be forwarded as part of the HTTP query
    parameters."""
    if labels is None:
        return None
    # validate
    for k, v in labels.items():
        try:
            Label(key=k, value=v)
        except Exception as ex:
            raise HttpResponseError(
                f"label ({k}: {v}) has invalid format", status_code=400
            ) from ex
    return json.dumps(labels)


def _retry_not_found(fn):
    def _impl(*args, **kwargs):
        delays = [1.0, 2.0, 5.0, 10.0, 10.0]
        retries = 0
        while True:
            try:
                return fn(*args, **kwargs)
            except (HTTPError, HttpResponseError) as ex:
                if ex.status_code == 404 and retries < len(delays):
                    time.sleep(delays[retries])
                    retries += 1
                else:
                    raise
            except httpx.HTTPStatusError as ex:
                if ex.response.status_code == 404 and retries < len(delays):
                    time.sleep(delays[retries])
                    retries += 1
                else:
                    raise

    return _impl


def _httpx_retry_not_found(fn):
    def _impl(*args, **kwargs):
        delays = [1.0, 2.0, 5.0, 10.0, 10.0]
        retries = 0
        while True:
            try:
                response: httpx.Response = fn(*args, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as ex:
                if ex.response.status_code == 404 and retries < len(delays):
                    time.sleep(delays[retries])
                    retries += 1
                else:
                    raise

    return _impl


@contextmanager
def _file_upload_progress_bar(
    stream, *, total=None, bytes=True, chunk_size: int = 4096, **tqdm_kwargs
):
    """Thin wrapper around ``tqdm.wrapattr()``.

    Works around an issue where
    httpx doesn't recognize the progress bar as an ``Iterable[bytes]``.
    """

    def _tqdm_iter_bytes(pb) -> Iterable[bytes]:
        while x := pb.read(chunk_size):
            yield x

    with tqdm.wrapattr(stream, "read", total=total, bytes=bytes, **tqdm_kwargs) as pb:
        yield _tqdm_iter_bytes(pb)


def _access_label(
    access: Literal["public", "preview", "private"],
) -> dict[str, Optional[str]]:
    if access == "private":
        label_value = None
    elif access == "preview":
        # TODO: Change usage of "internal" to "preview" on the backend
        label_value = "internal"
    else:
        label_value = str(access)
    return {"dyff.io/access": label_value}


SchemaType = TypeVar("SchemaType", bound=DyffBaseModel)
SchemaObject = Union[SchemaType, dict[str, Any]]


def _parse_schema_object(
    t: type[SchemaType], obj: SchemaObject[SchemaType]
) -> SchemaType:
    """If ``obj`` is a ``dict``, parse it as a ``t``.

    Else return it unchanged.
    """
    if isinstance(obj, dict):
        return t.model_validate(obj)
    elif type(obj) != t:
        raise TypeError(f"obj: expected {t}; got {type(obj)}")
    else:
        return obj


_EntityT = TypeVar(
    "_EntityT",
    Challenge,
    Dataset,
    Evaluation,
    Family,
    InferenceService,
    InferenceSession,
    Measurement,
    Method,
    Model,
    Module,
    OCIArtifact,
    Report,
    SafetyCase,
    Team,
    UseCase,
)
_CreateRequestT = TypeVar(
    "_CreateRequestT",
    AnalysisCreateRequest,
    ArtifactCreateRequest,
    ChallengeCreateRequest,
    ConcernCreateRequest,
    DatasetCreateRequest,
    EvaluationCreateRequest,
    FamilyCreateRequest,
    InferenceServiceCreateRequest,
    InferenceSessionCreateRequest,
    MethodCreateRequest,
    ModelCreateRequest,
    ModuleCreateRequest,
    ReportCreateRequest,
)
_CreateResponseT = TypeVar(
    "_CreateResponseT",
    Challenge,
    Dataset,
    Evaluation,
    Family,
    InferenceService,
    InferenceSessionAndToken,
    Measurement,
    Method,
    Model,
    Module,
    OCIArtifact,
    Report,
    SafetyCase,
    Team,
    UseCase,
)
_RawOpsT = TypeVar(
    "_RawOpsT",
    ChallengesOperationsGenerated,
    DatasetsOperationsGenerated,
    EvaluationsOperationsGenerated,
    FamiliesOperationsGenerated,
    InferenceServicesOperationsGenerated,
    InferenceSessionsOperationsGenerated,
    MeasurementsOperationsGenerated,
    MethodsOperationsGenerated,
    ModelsOperationsGenerated,
    ModulesOperationsGenerated,
    ReportsOperationsGenerated,
    SafetyCasesOperationsGenerated,
    TeamsOperationsGenerated,
    UseCasesOperationsGenerated,
)


class _OpsBase(Generic[_EntityT, _CreateRequestT, _CreateResponseT, _RawOpsT]):
    def __init__(
        self,
        *,
        _client: Client,
        _entity_type: type[_EntityT],
        _request_type: type[_CreateRequestT],
        _response_type: type[_CreateResponseT],
        _raw_ops: _RawOpsT,
    ):
        self._client = _client
        self._entity_type: type[_EntityT] = _entity_type
        self._request_type: type[_CreateRequestT] = _request_type
        self._response_type: type[_CreateResponseT] = _response_type
        self.__raw_ops: _RawOpsT = _raw_ops

    @property
    def _insecure(self) -> bool:
        return self._client.insecure

    @property
    def _timeout(self) -> Timeout:
        return self._client.timeout

    @property
    def _raw_ops(self) -> _RawOpsT:
        return self.__raw_ops

    def create(self, request: SchemaObject[_CreateRequestT]) -> _CreateResponseT:
        """Create a new entity.

        .. note::
            This operation may incur compute costs.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        request = _parse_schema_object(self._request_type, request)
        payload = request.model_dump(mode="json")
        entity = _retry_not_found(self._raw_ops.create)(payload)
        return self._response_type.model_validate(entity)

    def get(self, id: str) -> _EntityT:
        """Get an entity by its .id.

        :param id: The entity ID
        :return: The entity with the given ID.
        """
        return self._entity_type.model_validate(self._raw_ops.get(id))

    def delete(self, id: str) -> Status:
        """Mark an entity for deletion.

        :param id: The entity ID
        :return: The resulting status of the entity
        """
        return Status.model_validate(self._raw_ops.delete(id))

    def label(self, id: str, labels: dict[str, Optional[str]]) -> None:
        """Label the specified entity with key-value pairs (stored in the ``.labels``
        field).

        Providing ``None`` for the value deletes the label. Key-value mappings
        not given in ``labels`` remain unchanged.

        See :class:`~dyff.schema.platform.Label` for a description of the
        constraints on label keys and values.

        :param id: The ID of the entity to label.
        :param labels: The label keys and values.
        """
        if not labels:
            return
        labels = LabelsEditRequest(labels=labels).model_dump(by_alias=True)
        self._raw_ops.label(id, labels)

    def _request(self, method: str, route: str, **kwargs) -> httpx.Response:
        if kwargs.pop("verify", None) is not None:
            raise ValueError(
                "overriding 'verify' is not allowed;"
                " set 'insecure=True' in the client to disable verification"
            )

        if not route.startswith("/"):
            route = f"/{route}"
        headers: dict[str, str] = kwargs.pop("headers", {})
        headers.setdefault("Authorization", f"Bearer {self._client._api_token}")
        timeout = kwargs.pop("timeout", self._client.timeout)
        verify = not self._client.insecure

        response = httpx.request(
            method,
            f"{self._client._endpoint}{route}",
            headers=headers,
            timeout=timeout,
            verify=verify,
            **kwargs,
        )
        response.raise_for_status()
        return response


class _NewOpsBase(Generic[_EntityT, _CreateRequestT, _CreateResponseT]):
    def __init__(
        self,
        *,
        _client: Client,
        _entity: Entities,
        _entity_type: type[_EntityT],
        _request_type: type[_CreateRequestT],
        _response_type: type[_CreateResponseT],
    ):
        self._client = _client
        self._entity = _entity
        self._entity_type: type[_EntityT] = _entity_type
        self._request_type: type[_CreateRequestT] = _request_type
        self._response_type: type[_CreateResponseT] = _response_type

    @property
    def _insecure(self) -> bool:
        return self._client.insecure

    @property
    def _timeout(self) -> Timeout:
        return self._client.timeout

    def _route(self, *, id: Optional[str] = None, path: Optional[str] = None) -> str:
        parts = [Resources.for_kind(self._entity).value]
        if id is not None:
            parts.append(id)
        if path is not None:
            parts.append(path.removeprefix("/"))
        return "/".join(parts)

    def get(self, id: str) -> _EntityT:
        """Get an entity by its .id.

        :param id: The entity ID
        :return: The entity with the given ID.
        """
        response = self._request("GET", self._route(id=id))
        return self._entity_type.model_validate(response.json())

    def delete(self, id: str) -> Status:
        """Mark an entity for deletion.

        :param id: The entity ID
        :return: The resulting status of the entity
        """
        response = self._request("PUT", self._route(id=id, path="delete"))
        return Status.model_validate(response.json())

    def label(self, id: str, labels: dict[str, Optional[str]]) -> None:
        """Label the specified entity with key-value pairs (stored in the ``.labels``
        field).

        Providing ``None`` for the value deletes the label. Key-value mappings
        not given in ``labels`` remain unchanged.

        See :class:`~dyff.schema.platform.Label` for a description of the
        constraints on label keys and values.

        :param id: The ID of the entity to label.
        :param labels: The label keys and values.
        """
        if not labels:
            return
        request = LabelsEditRequest(labels=labels)  # type: ignore
        self._request(
            "PATCH",
            self._route(id=id, path="labels"),
            json=request.model_dump(mode="json"),
        )

    def create(self, request: SchemaObject[_CreateRequestT]) -> _CreateResponseT:
        """Create a new entity.

        .. note::
            This operation may incur compute costs.

        :param request: The entity create request specification.
        :return: A full entity spec with its .id and other system properties set
        """
        request = _parse_schema_object(self._request_type, request)
        response = _httpx_retry_not_found(self._request)(
            "POST", self._route(), json=request.model_dump(mode="json")
        )
        return self._response_type.model_validate(response.json())

    def _request(self, method: str, route: str, **kwargs) -> httpx.Response:
        if kwargs.pop("verify", None) is not None:
            raise ValueError(
                "overriding 'verify' is not allowed;"
                " set 'insecure=True' in the client to disable verification"
            )

        if not route.startswith("/"):
            route = f"/{route}"
        headers: dict[str, str] = kwargs.pop("headers", {})
        headers.setdefault("Authorization", f"Bearer {self._client._api_token}")
        timeout = kwargs.pop("timeout", self._client.timeout)
        verify = not self._client.insecure

        response = httpx.request(
            method,
            f"{self._client._endpoint}{route}",
            headers=headers,
            timeout=timeout,
            verify=verify,
            **kwargs,
        )
        response.raise_for_status()
        return response


class _PublishMixin(_OpsProtocol):
    def publish(
        self,
        id: str,
        access: Literal["public", "preview", "private"],
    ) -> None:
        """Set the publication status of an entity in the Dyff cloud app.

        Publication status affects only:

        1. Deliberate outputs, such as the rendered HTML from a safety case
        2. The entity spec (the information you get back from .get())
        3. Associated documentation

        Other artifacts -- source code, data, logs, etc. -- are never accessible
        to unauthenticated users.

        The possible access modes are:

        1. ``"public"``: Anyone can view the results
        2. ``"preview"``: Authorized users can view the results as they
            would appear if they were public
        3. ``"private"``: The results are not visible in the app
        """
        return self.label(id, _access_label(access))


class _ConcernsMixin(_OpsProtocol):
    def add_concern(self, id: str, concern: Concern) -> None:
        """Label the entity with a link to a relevant Concern."""
        return self.label(id, {concern.label_key(): concern.label_value()})

    def remove_concern(self, id: str, concern: Concern) -> None:
        """Remove a link to a Concern, if a link exists."""
        return self.label(id, {concern.label_key(): None})


class _ArtifactsMixin(_ArtifactsProtocol):
    def downlinks(self, id: str) -> list[ArtifactURL]:
        """Get a list of signed GET URLs from which entity artifacts can be downloaded.

        :param id: The ID of the entity.
        :return: List of signed GET URLs.
        :raises HttpResponseError:
        """
        return [
            ArtifactURL.model_validate(link) for link in self._raw_ops.downlinks(id)
        ]

    def download(self, id: str, destination: Path | str) -> None:
        """Download all of the artifact files for an entity to a local directory.

        The destination path must not exist. Parent directories will be created.

        :param id: The ID of the entity.
        :param destination: The destination directory. Must exist and be empty.
        :raises HttpResponseError:
        :raises ValueError: If arguments are invalid
        """
        links = self.downlinks(id)

        destination = Path(destination).resolve()
        destination.mkdir(parents=True)

        paths: list[tuple[ArtifactURL, Path]] = [
            (link, (destination / link.artifact.path).resolve()) for link in links
        ]

        # The file paths are the paths that are not a prefix of any other path
        file_paths = [
            (link, path)
            for link, path in paths
            if not any(
                path != other and other.is_relative_to(path) for _, other in paths
            )
        ]

        # TODO: Make the download resumable
        # TODO: Download in parallel
        for link, path in file_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as fout:
                with httpx.stream(
                    "GET",
                    link.signedURL.url,
                    headers=link.signedURL.headers,
                    verify=not self._insecure,
                    timeout=self._timeout,
                ) as response:
                    file_size = float(response.headers.get("Content-Length"))
                    with tqdm.wrapattr(
                        fout, "write", total=file_size, desc=link.artifact.path
                    ) as out_stream:
                        for chunk in response.iter_raw():
                            out_stream.write(chunk)


class _DocumentationMixin(_OpsProtocol):
    def documentation(self, id: str) -> Documentation:
        """Get the documentation associated with an entity.

        :param id: The ID of the entity.
        :return: The documentation associated with the entity.
        :raises HttpResponseError:
        """
        return Documentation.model_validate(self._raw_ops.documentation(id))

    def edit_documentation(
        self, id: str, edit_request: DocumentationEditRequest
    ) -> Documentation:
        """Edit the documentation associated with an entity.

        :param id: The ID of the entity.
        :param edit_request: Object containing the edits to make.
        :return: The modified documentation.
        :raises HttpResponseError:
        """
        return Documentation.model_validate(
            self._raw_ops.edit_documentation(id, edit_request.model_dump(by_alias=True))
        )


class _LogsMixin(_OpsProtocol):
    def logs(self, id: str) -> Iterable[str]:
        """Stream the logs from an entity as a sequence of lines.

        :param id: The ID of the entity.
        :return: An Iterable over the lines in the logs file. The response is streamed,
            and may time out if it is not consumed quickly enough.
        :raises HttpResponseError:
        """
        link = ArtifactURL.model_validate(self._raw_ops.logs(id))
        with httpx.stream(
            "GET",
            link.signedURL.url,
            headers=link.signedURL.headers,
            verify=not self._insecure,
            timeout=self._timeout,
        ) as response:
            yield from response.iter_lines()

    def download_logs(self, id, destination: Path | str) -> None:
        """Download the logs file from an entity.

        The destination path must not exist. Parent directories will be created.

        :param id: The ID of the entity.
        :param destination: The destination file. Must not exist, and its parent
            directory must exist.
        :raises HttpResponseError:
        """
        destination = Path(destination).resolve()
        if destination.exists():
            raise FileExistsError(str(destination))
        destination.parent.mkdir(exist_ok=True, parents=True)

        link = ArtifactURL.model_validate(self._raw_ops.logs(id))
        with open(destination, "wb") as fout:
            with httpx.stream(
                "GET",
                link.signedURL.url,
                headers=link.signedURL.headers,
                verify=not self._insecure,
                timeout=self._timeout,
            ) as response:
                file_size = float(response.headers.get("Content-Length"))
                with tqdm.wrapattr(
                    fout, "write", total=file_size, desc=link.artifact.path
                ) as out_stream:
                    for chunk in response.iter_raw():
                        out_stream.write(chunk)


class _Artifacts(
    _NewOpsBase[OCIArtifact, ArtifactCreateRequest, OCIArtifact],
    _DocumentationMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.OCIArtifact` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.artifacts`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(
        self,
        _client: Client,
    ):
        super().__init__(
            _client=_client,
            _entity=Entities.Artifact,
            _entity_type=OCIArtifact,
            _request_type=ArtifactCreateRequest,
            _response_type=OCIArtifact,
        )

    @property
    def _raw_ops(self) -> Any:
        # FIXME: This class is implemented in a different way from all the
        # other API groups. We need this property for it to type-check.
        raise NotImplementedError()

    # def query(
    #     self,
    #     *,
    #     query: Optional[QueryT] = None,
    #     id: Optional[str] = None,
    #     account: Optional[str] = None,
    #     status: Optional[str] = None,
    #     reason: Optional[str] = None,
    #     labels: Optional[dict[str, str]] = None,
    # ) -> list[OCIArtifact]:
    #     """Get all Artifact entities matching a query. The query is a set of equality
    #     constraints specified as key-value pairs.

    #     :keyword query:
    #     :keyword id:
    #     :keyword account:
    #     :keyword status:
    #     :keyword reason:
    #     :keyword labels: Matches entities that are labeled with *all* of the given key-
    #         value pairs.
    #     :raises HttpResponseError:
    #     """
    #     return [
    #         OCIArtifact.model_validate(obj)
    #         for obj in self._raw_ops.query(
    #             query=_encode_query(query),
    #             id=id,
    #             account=account,
    #             status=status,
    #             reason=reason,
    #             labels=_encode_labels(labels),
    #         )
    #     ]

    # FIXME: This method should be provided by _DocumentationMixin, but first
    # we need to migrate all the other types to store documentation as a
    # member rather than a separate entity.

    # def edit_documentation(
    #     self, id: str, edit_request: DocumentationEditRequest
    # ) -> None:
    #     """Edit the documentation associated with an entity.

    #     :param id: The ID of the entity.
    #     :param edit_request: Object containing the edits to make.
    #     """
    #     self._raw_ops.edit_documentation(id, edit_request.dict())

    def push(self, artifact: OCIArtifact, *, source: str) -> None:
        """Push an OCI artifact to the Dyff registry.

        The push operation uses the ``skopeo`` command-line tool, which must
        be installed on the system where the client is running.

        The ``artifact`` must be in ``Created`` status.

        The ``source`` can be any "image name" understood by ``skopeo``.

        :param artifact: An ``OCIArtifact`` entity as returned from ``.create()``.
        :keyword source: A ``skopeo`` image name referencing the artifact to push.
        :see: https://github.com/containers/skopeo/blob/main/docs/skopeo.1.md#image-names
        """
        registry_username = "unused"
        registry_password = self._client._api_token
        registry_credential = f"{registry_username}:{registry_password}"
        registry_url = self._client._registry_url

        remote_name = f"artifacts/{artifact.id}:latest"

        push_command = [
            "skopeo",
            "copy",
            "--format",
            "oci",
            "--dest-creds",
            registry_credential,
        ]
        if self._client._insecure:
            push_command.append("--dest-tls-verify=false")
        destination_host = registry_url.removeprefix("https://")
        destination = f"docker://{destination_host}/{remote_name}"
        push_command.extend([source, destination])

        subprocess.run(
            push_command,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )

    def finalize(self, id: str) -> Status:
        response = self._request("POST", self._route(id=id, path="finalize"))
        return Status.model_validate(response.json())


class _Challenges(
    _OpsBase[
        Challenge, ChallengeCreateRequest, Challenge, ChallengesOperationsGenerated
    ],
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.Challenge` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.challenges`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(
        self,
        _client: Client,
    ):
        super().__init__(
            _client=_client,
            _entity_type=Challenge,
            _request_type=ChallengeCreateRequest,
            _response_type=Challenge,
            _raw_ops=_client.raw.challenges,
        )

    def create_task(
        self, id: str, request: ChallengeTaskCreateRequest
    ) -> ChallengeTask:
        result = self._raw_ops.create_task(id, request.model_dump(mode="json"))
        return ChallengeTask.model_validate(result)

    def create_team(self, id: str, request: ChallengeTeamCreateRequest) -> Team:
        result = self._raw_ops.create_team(id, request.model_dump(mode="json"))
        return Team.model_validate(result)

    def edit_content(self, id: str, edit: ChallengeContentEditRequest) -> None:
        self._raw_ops.edit_content(id, edit.model_dump(mode="json"))

    def teams(self, id: str) -> list[Team]:
        return [Team.model_validate(team) for team in self._raw_ops.teams(id)]


class _Datasets(
    _OpsBase[Dataset, DatasetCreateRequest, Dataset, DatasetsOperationsGenerated],
    _ArtifactsMixin,
    _DocumentationMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.Dataset` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.datasets`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(
        self,
        _client: Client,
    ):
        super().__init__(
            _client=_client,
            _entity_type=Dataset,
            _request_type=DatasetCreateRequest,
            _response_type=Dataset,
            _raw_ops=_client.raw.datasets,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        name: Optional[str] = None,
    ) -> list[Dataset]:
        """Get all Datasets matching a query. The query is a set of equality constraints
        specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword name:
        :return: list of ``Dataset`` resources satisfying the query.
        :raises HttpResponseError:
        """
        return [
            Dataset.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                name=name,
            )
        ]

    def create_arrow_dataset(
        self, dataset_directory: Path | str, *, account: str, name: str
    ) -> Dataset:
        """Create a Dataset resource describing an existing Arrow dataset.

        Internally, constructs a ``DatasetCreateRequest`` using information
        obtained from the Arrow dataset, then calls ``create()`` with the
        constructed request.

        Typical usage::

            dataset = client.datasets.create_arrow_dataset(dataset_directory, ...)
            client.datasets.upload_arrow_dataset(dataset, dataset_directory)

        :param dataset_directory: The root directory of the Arrow dataset.
        :keyword account: The account that will own the Dataset resource.
        :keyword name: The name of the Dataset resource.
        :returns: The complete Dataset resource.
        """
        dataset_path = Path(dataset_directory)
        ds = arrow.open_dataset(str(dataset_path))
        file_paths = list(ds.files)  # type: ignore[attr-defined]
        artifact_paths = [
            str(Path(file_path).relative_to(dataset_path)) for file_path in file_paths
        ]
        artifacts = [
            Artifact(
                kind="parquet",
                path=artifact_path,
                digest=Digest(
                    md5=binary.encode(binary.file_digest("md5", file_path)),
                ),
            )
            for file_path, artifact_path in zip(file_paths, artifact_paths)
        ]
        schema = DataSchema(
            arrowSchema=arrow.encode_schema(ds.schema),
        )
        request = DatasetCreateRequest(
            account=account,
            name=name,
            artifacts=artifacts,
            schema=schema,
        )
        return self.create(request)

    def upload_arrow_dataset(
        self,
        dataset: Dataset,
        dataset_directory: Path | str,
    ) -> None:
        """Uploads the data files in an existing Arrow dataset for which a Dataset
        resource has already been created.

        Typical usage::

            dataset = client.datasets.create_arrow_dataset(dataset_directory, ...)
            client.datasets.upload_arrow_dataset(dataset, dataset_directory)

        :param dataset: The Dataset resource for the Arrow dataset.
        :param dataset_directory: The root directory of the Arrow dataset.
        """
        if any(artifact.digest.md5 is None for artifact in dataset.artifacts):
            raise ValueError("artifact.digest.md5 must be set for all artifacts")
        for artifact in dataset.artifacts:
            assert artifact.digest.md5 is not None
            file_path = Path(dataset_directory) / artifact.path
            put_url_json = _retry_not_found(self._raw_ops.upload)(
                dataset.id, artifact.path
            )
            put_url = StorageSignedURL.model_validate(put_url_json)
            if put_url.method != "PUT":
                raise ValueError(f"expected a PUT URL; got {put_url.method}")

            file_size = file_path.stat().st_size
            with open(file_path, "rb") as fin:
                with _file_upload_progress_bar(
                    fin, total=file_size, desc=artifact.path
                ) as content:
                    headers = {
                        "content-md5": artifact.digest.md5,
                    }
                    headers.update(put_url.headers)
                    response = httpx.put(
                        put_url.url,
                        content=content,
                        headers=headers,
                        verify=not self._insecure,
                        timeout=self._timeout,
                    )
                    response.raise_for_status()
        _retry_not_found(self._raw_ops.finalize)(dataset.id)


class _Evaluations(
    _OpsBase[
        Evaluation, EvaluationCreateRequest, Evaluation, EvaluationsOperationsGenerated
    ],
    _ArtifactsMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.Evaluation` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.evaluations`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=Evaluation,
            _request_type=EvaluationCreateRequest,
            _response_type=Evaluation,
            _raw_ops=_client.raw.evaluations,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        dataset: Optional[str] = None,
        inferenceService: Optional[str] = None,
        inferenceServiceName: Optional[str] = None,
        model: Optional[str] = None,
        modelName: Optional[str] = None,
    ) -> list[Evaluation]:
        """Get all Evaluations matching a query. The query is a set of equality
        constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword dataset:
        :keyword inferenceService: Queries the
            ``.inferenceSession.inferenceService.id`` nested field.
        :keyword inferenceServiceName: Queries the
            ``.inferenceSession.inferenceService.name`` nested field.
        :keyword model: Queries the
            ``.inferenceSession.inferenceService.model.id`` nested field.
        :keyword modelName: Queries the
            ``.inferenceSession.inferenceService.model.name`` nested field.
        :return: list of ``Evaluation`` resources satisfying the query.
        :raises HttpResponseError:
        """
        return [
            Evaluation.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                dataset=dataset,
                inference_service=inferenceService,
                inference_service_name=inferenceServiceName,
                model=model,
                model_name=modelName,
            )
        ]


class _Families(
    _OpsBase[Family, FamilyCreateRequest, Family, FamiliesOperationsGenerated],
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.Family` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.families`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=Family,
            _request_type=FamilyCreateRequest,
            _response_type=Family,
            _raw_ops=_client.raw.families,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> list[Family]:
        """Get all Family entities matching a query. The query is a set of equality
        constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :return: list of ``Family`` resources satisfying the query.
        :raises HttpResponseError:
        """
        return [
            Family.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
            )
        ]

    def get_member(self, id: str, tag: str) -> Optional[DyffEntityType]:
        family: Family = self.get(id)
        member = family.members.get(tag)
        if member is None:
            return None
        return self._client.apigroup(member.entity.kind).get(member.entity.id)

    def edit_members(
        self, id: str, members: dict[str, Optional[FamilyMemberBase]]
    ) -> None:
        """Set tagged members of the Family.

        The keys in the dictionary are the tag names. Providing ``None`` for
        the value deletes the tag. Tag mappings not given in ``members``
        remain unchanged.

        See :class:`~dyff.schema.platform.TagName` for a description of the
        constraints on tag names.

        :param id: The ID of the Family to edit.
        :param members: The tag names and corresponding members.
        """
        if not members:
            return
        edit = FamilyMembersEditRequest(members=members).model_dump(by_alias=True)
        self._raw_ops.edit_members(id, edit)

    # FIXME: This method should be provided by _DocumentationMixin, but first
    # we need to migrate all the other types to store documentation as a
    # member rather than a separate entity.

    def edit_documentation(
        self, id: str, edit_request: DocumentationEditRequest
    ) -> None:
        """Edit the documentation associated with an entity.

        :param id: The ID of the entity.
        :param edit_request: Object containing the edits to make.
        """
        self._raw_ops.edit_documentation(id, edit_request.model_dump(by_alias=True))


class _InferenceServices(
    _OpsBase[
        InferenceService,
        InferenceServiceCreateRequest,
        InferenceService,
        InferenceServicesOperationsGenerated,
    ],
    _DocumentationMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.InferenceService` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.inferenceservices`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=InferenceService,
            _request_type=InferenceServiceCreateRequest,
            _response_type=InferenceService,
            _raw_ops=_client.raw.inferenceservices,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        name: Optional[str] = None,
        model: Optional[str] = None,
        modelName: Optional[str] = None,
    ) -> list[InferenceService]:
        """Get all InferenceServices matching a query. The query is a set of equality
        constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword name:
        :keyword model: Queries the ``.model.id`` nested field.
        :keyword modelName: Queries the ``model.name`` nested field.
        :return: list of ``InferenceService`` resources satisfying the query.
        :raises HttpResponseError:
        """
        return [
            InferenceService.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                name=name,
                model=model,
                model_name=modelName,
            )
        ]


class _InferenceSessions(
    _OpsBase[
        InferenceSession,
        InferenceSessionCreateRequest,
        InferenceSessionAndToken,
        InferenceSessionsOperationsGenerated,
    ]
):
    """Operations on :class:`~dyff.schema.platform.Inferencesession` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.inferencesessions`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=InferenceSession,
            _request_type=InferenceSessionCreateRequest,
            _response_type=InferenceSessionAndToken,
            _raw_ops=_client.raw.inferencesessions,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        name: Optional[str] = None,
        inferenceService: Optional[str] = None,
        inferenceServiceName: Optional[str] = None,
        model: Optional[str] = None,
        modelName: Optional[str] = None,
    ) -> list[InferenceSession]:
        """Get all InferenceSessions matching a query. The query is a set of equality
        constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword name:
        :keyword inferenceService: Queries the ``.inferenceService.id`` nested
            field.
        :keyword inferenceServiceName: Queries the ``.inferenceService.name``
            nested field.
        :keyword model: Queries the ``.inferenceService.model.id`` nested field.
        :keyword modelName: Queries the ``.inferenceService.model.name`` nested
            field.
        :return: list of ``InferenceSession`` resources satisfying the query.
        :raises HttpResponseError:
        """
        return [
            InferenceSession.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                name=name,
                inference_service=inferenceService,
                inference_service_name=inferenceServiceName,
                model=model,
                model_name=modelName,
            )
        ]

    def client(
        self,
        session_id: str,
        token: str,
        *,
        interface: Optional[InferenceInterface] = None,
        endpoint: Optional[str] = None,
        input_adapter: Optional[Adapter] = None,
        output_adapter: Optional[Adapter] = None,
    ) -> InferenceSessionClient:
        """Create an InferenceSessionClient that interacts with the given inference
        session. The token should be one returned either from
        ``Client.inferencesessions.create()`` or from
        ``Client.inferencesessions.token(session_id)``.

        The inference endpoint in the session must also be specified, either
        directly through the ``endpoint`` argument or by specifying an
        ``interface``. Specifying ``interface`` will also use the input and
        output adapters from the interface. You can also specify these
        separately in the ``input_adapter`` and ``output_adapter``. The
        non-``interface`` arguments override the corresponding values in
        ``interface`` if both are specified.

        :param session_id: The inference session to connect to
        :param token: An access token with permission to run inference against
            the session.
        :param interface: The interface to the session. Either ``interface``
            or ``endpoint`` must be specified.
        :param endpoint: The inference endpoint in the session to call. Either
            ``endpoint`` or ``interface`` must be specified.
        :param input_adapter: Optional input adapter, applied to the input
            before sending it to the session. Will override the input adapter
            from ``interface`` if both are specified.
        :param output_adapter: Optional output adapter, applied to the output
            of the session before returning to the client. Will override the
            output adapter from ``interface`` if both are specified.
        :return: An ``InferenceSessionClient`` that makes inference calls to
            the specified session.
        """
        if interface is not None:
            endpoint = endpoint or interface.endpoint
            if input_adapter is None:
                if interface.inputPipeline is not None:
                    input_adapter = create_pipeline(interface.inputPipeline)
            if output_adapter is None:
                if interface.outputPipeline is not None:
                    output_adapter = create_pipeline(interface.outputPipeline)
        if endpoint is None:
            raise ValueError("either 'endpoint' or 'interface' is required")
        return InferenceSessionClient(
            session_id=session_id,
            token=token,
            dyff_api_endpoint=self._client._endpoint,
            inference_endpoint=endpoint,
            input_adapter=input_adapter,
            output_adapter=output_adapter,
            insecure=self._insecure,
        )

    def ready(self, session_id: str) -> bool:
        """Return True if the session is ready; tolerate 202/JSON bodies; GET→POST
        fallback."""
        # Try GET first
        try:
            resp = self._request("GET", f"/inferencesessions/{session_id}/ready")
            sc = resp.status_code
            if sc == 202:
                return False
            if sc == 204:
                return True
            if sc == 200:
                try:
                    data = resp.json()
                    if isinstance(data, dict) and "ready" in data:
                        return bool(data["ready"])
                except Exception:
                    pass
                return True
            # Any other 2xx: assume ready
            return True
        except httpx.HTTPStatusError as ex:
            sc = ex.response.status_code
            if sc in (404, 503):
                return False
            if sc != 405:
                raise
        # Fallback to POST (older API)
        try:
            resp = self._request("POST", f"/inferencesessions/{session_id}/ready")
            sc = resp.status_code
            if sc == 202:
                return False
            return sc in (200, 204)
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code in (404, 503, 405):
                return False
            raise

    def terminate(self, session_id: str) -> Status:
        """Terminate a session.

        :param session_id: The inference session key
        :return: The resulting status of the entity
        :raises HttpResponseError:
        """
        return Status.model_validate(self._raw_ops.terminate(session_id))

    def token(self, session_id: str, *, expires: Optional[datetime] = None) -> str:
        """Create a short-lived session token (POST for new servers; GET fallback)."""
        body = {"expires": expires.isoformat()} if expires is not None else None
        # Prefer POST (newer API)
        try:
            resp = self._request(
                "POST",
                f"/inferencesessions/{session_id}/token",
                json=body,
            )
            ct = resp.headers.get("content-type", "").lower()
            if "application/json" in ct:
                payload = resp.json()
                if isinstance(payload, dict) and "token" in payload:
                    return str(payload["token"])
                if isinstance(payload, str):
                    return payload
            return resp.text
        except httpx.HTTPStatusError as ex:
            # Older servers may only support GET
            if ex.response.status_code != 405:
                raise
        # Fallback to GET (legacy)
        raw = self._raw_ops.token(session_id)
        if isinstance(raw, (bytes, bytearray)):
            return raw.decode()
        if isinstance(raw, dict) and "token" in raw:
            return str(raw["token"])
        return str(raw)


class _Measurements(
    _OpsBase[
        Measurement,
        AnalysisCreateRequest,
        Measurement,
        MeasurementsOperationsGenerated,
    ],
    _ArtifactsMixin,
    _LogsMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.Measurement` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.measurements`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=Measurement,
            _request_type=AnalysisCreateRequest,
            _response_type=Measurement,
            _raw_ops=_client.raw.measurements,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        method: Optional[str] = None,
        methodName: Optional[str] = None,
        dataset: Optional[str] = None,
        evaluation: Optional[str] = None,
        inferenceService: Optional[str] = None,
        model: Optional[str] = None,
        inputs: Optional[list[str]] = None,
    ) -> list[Measurement]:
        """Get all Measurement entities matching a query. The query is a set of equality
        constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword method: Queries the ``.method.id`` nested field.
        :keyword methodName: Queries the ``.method.name`` nested field.
        :keyword dataset: Queries the ``.scope.dataset`` nested field.
        :keyword evaluation: Queries the ``.scope.evaluation`` nested field.
        :keyword inferenceService: Queries the ``.scope.inferenceService``
            nested field.
        :keyword model: Queries the ``.scope.model`` nested field.
        :keyword inputs: List of entity IDs. Matches Measurements that took
            *any* of these entities as inputs.
        :return: Entities matching the query
        :raises HttpResponseError:
        """
        return [
            Measurement.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                method=method,
                method_name=methodName,
                dataset=dataset,
                evaluation=evaluation,
                inference_service=inferenceService,
                model=model,
                inputs=(",".join(inputs) if inputs is not None else None),
            )
        ]

    def workflow_logs(
        self, id: str, *, since: str | None = None, limit: int = 1000
    ) -> WorkflowLogsResponse:
        """Get workflow infrastructure logs for a Measurement.

        Returns logs from Kubernetes pods running the measurement workflow, including
        container startup, pod scheduling, and system errors.

        :param id: The ID of the measurement.
        :param since: Time range like '1h', '30m', '2d'. Optional.
        :param limit: Maximum number of log lines to return.
        :return: Workflow logs response with log entries.
        :raises HttpResponseError:
        """
        # Build query parameters
        params: dict[str, int | str] = {"limit": limit}
        if since is not None:
            params["since"] = since

        # Make HTTP request to the measurements workflow logs endpoint
        # Use the raw client's base URL by reconstructing from endpoint
        endpoint = self._client._endpoint
        response = httpx.get(
            f"{endpoint}/measurements/{id}/logs/workflow",
            headers={"Authorization": f"Bearer {self._client._api_token}"},
            params=params,
            verify=not self._insecure,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return WorkflowLogsResponse.model_validate(response.json())

    async def stream_workflow_logs(self, id: str) -> AsyncIterable[WorkflowLogEntry]:
        """Stream workflow logs in real-time via WebSocket.

        :param id: The ID of the measurement.
        :yield: Individual log entries as they arrive.
        :raises HttpResponseError:
        """
        ws_endpoint = self._client._endpoint.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        ws_url = f"{ws_endpoint}/measurements/{id}/logs/workflow/stream"

        # Connect to WebSocket with authentication
        headers = {"Authorization": f"Bearer {self._client._api_token}"}

        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            async for message in websocket:
                log_entry = WorkflowLogEntry.model_validate(json.loads(message))
                yield log_entry


class _Methods(
    _OpsBase[
        Method,
        MethodCreateRequest,
        Method,
        MethodsOperationsGenerated,
    ],
    _DocumentationMixin,
    _LogsMixin,
    _PublishMixin,
    _ConcernsMixin,
):
    """Operations on :class:`~dyff.schema.platform.Method` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.analyses`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=Method,
            _request_type=MethodCreateRequest,
            _response_type=Method,
            _raw_ops=_client.raw.methods,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        name: Optional[str] = None,
        outputKind: Optional[str] = None,
        output_kind: Optional[str] = None,
    ) -> list[Method]:
        """Get all Method entities matching a query. The query is a set of equality
        constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword name:
        :keyword outputKind: Queries the ``.output.kind`` nested field.
        :keyword output_kind: Deprecated alias for ``outputKind``

            .. deprecated:: 0.15.2

                Use ``outputKind`` instead.

        :return: list of Method entities matching query
        :raises HttpResponseError:
        """
        if outputKind is not None and output_kind is not None:
            raise ValueError("output_kind is deprecated; use outputKind")
        if output_kind is not None:
            warnings.warn(
                "output_kind is deprecated; use outputKind", DeprecationWarning
            )
            outputKind = output_kind
        return [
            Method.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                name=name,
                output_kind=outputKind,
            )
        ]

    def workflow_logs(
        self, id: str, *, since: str | None = None, limit: int = 1000
    ) -> WorkflowLogsResponse:
        """Get workflow infrastructure logs for a Method.

        Returns logs from Kubernetes pods running the method workflow, including
        container startup, pod scheduling, and system errors.

        :param id: The ID of the method.
        :param since: Time range like '1h', '30m', '2d'. Optional.
        :param limit: Maximum number of log lines to return.
        :return: Workflow logs response with log entries.
        :raises HttpResponseError:
        """
        # Build query parameters
        params: dict[str, int | str] = {"limit": limit}
        if since is not None:
            params["since"] = since

        # Make HTTP request to the methods workflow logs endpoint
        response = httpx.get(
            f"{self._client._endpoint}/methods/{id}/logs/workflow",
            headers={"Authorization": f"Bearer {self._client._api_token}"},
            params=params,
            verify=not self._insecure,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return WorkflowLogsResponse.model_validate(response.json())

    async def stream_workflow_logs(self, id: str) -> AsyncIterable[WorkflowLogEntry]:
        """Stream workflow logs in real-time via WebSocket.

        :param id: The ID of the method.
        :yield: Individual log entries as they arrive.
        :raises HttpResponseError:
        """
        ws_endpoint = self._client._endpoint.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        ws_url = f"{ws_endpoint}/methods/{id}/logs/workflow/stream"

        # Connect to WebSocket with authentication
        api_token = self._client._api_token
        headers = {"Authorization": f"Bearer {api_token}"}

        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            async for message in websocket:
                log_entry = WorkflowLogEntry.model_validate(json.loads(message))
                yield log_entry


class _Models(
    _OpsBase[
        Model,
        ModelCreateRequest,
        Model,
        ModelsOperationsGenerated,
    ],
    _DocumentationMixin,
    _LogsMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.Model` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.models`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=Model,
            _request_type=ModelCreateRequest,
            _response_type=Model,
            _raw_ops=_client.raw.models,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        name: Optional[str] = None,
    ) -> list[Model]:
        """Get all Models matching a query. The query is a set of equality constraints
        specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword name:
        :return: list of ``Model`` resources satisfying the query.
        :raises HttpResponseError:
        """
        return [
            Model.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                name=name,
            )
        ]

    def uplink(self, model_id: str, path: str) -> StorageSignedURL:
        response = self._request("GET", f"/models/{model_id}/upload/{path}")
        return StorageSignedURL.model_validate(response.json())

    def finalize(self, model_id: str) -> None:
        self._request("POST", f"/models/{model_id}/finalize")

    def create_from_volume(
        self,
        root_directory: Path | str,
        *,
        account: str,
        name: str,
        resources: ModelResources,
        accelerators: Optional[list[Accelerator]] = None,
        include_symlinks: bool = False,
    ) -> Model:
        """Create a Model resource backed by a Volume.

        The Volume will contain all files and directories in the directory tree
        rooted at ``root_directory``.

        Internally, constructs a ``ModelCreateRequest`` using information
        obtained from the filesystem, then calls ``create()`` with the
        constructed request.

        Typical usage::

            model = client.models.create_from_volume(root_directory, ...)
            client.models.upload_volume(model, root_directory)

        :param root_directory: The root directory of the model data.
        :keyword account: The account that will own the Model resource.
        :keyword name: The name of the Model resource.
        :keyword include_symlinks: If True, the targets of symlinks will be
            **duplicated** at the path of the symlink. If False, symlinks will
            be **skipped entirely**. This is because s3-style storage does not
            have a concept of symlinks.
        :returns: The complete Model resource.
        """
        root_directory = Path(root_directory)
        file_paths = [
            file_path
            for file_path in root_directory.rglob("*")
            if file_path.is_file() and (include_symlinks or not file_path.is_symlink())
        ]
        upload_paths = [
            str(Path(file_path).relative_to(root_directory)) for file_path in file_paths
        ]
        files = [
            File(
                path=upload_path,
                digest=Digest(
                    md5=binary.encode(binary.file_digest("md5", str(file_path))),
                ),
                # At this point, we've either excluded symlinks or decided to
                # copy the target. stat() gives info about the target.
                size=file_path.stat().st_size,
            )
            for file_path, upload_path in zip(file_paths, upload_paths)
        ]
        request = ModelCreateRequest(
            name=name,
            account=account,
            artifact=ModelArtifact(
                kind=ModelArtifactKind.Volume,
                volume=Volume(files=files),
            ),
            source=ModelSource(
                kind=ModelSourceKinds.Upload,
            ),
            resources=resources,
            accelerators=accelerators,
        )
        return self.create(request)

    def upload_volume(
        self,
        model: Model,
        root_directory: Path | str,
    ) -> None:
        """Uploads the files in a volume for which a Model resource has already been
        created.

        Typical usage::

            model = client.models.create_from_volume(root_directory, ...)
            client.models.upload_volume(model, root_directory)

        :param model: The Model resource to be backed by the volume.
        :param root_directory: The root directory of the model data.
        """
        if model.artifact.kind != ModelArtifactKind.Volume:
            raise ValueError(f"expected .artifact.kind == {ModelArtifactKind.Volume}")
        if model.artifact.volume is None:
            raise ValueError("expected .artifact.volume")

        if any(file.digest.md5 is None for file in model.artifact.volume.files):
            raise ValueError("file.digest.md5 must be set for all files")
        for file in model.artifact.volume.files:
            assert file.digest.md5 is not None
            file_path = Path(root_directory) / file.path
            put_url: StorageSignedURL = _retry_not_found(self.uplink)(
                model.id, file.path
            )
            if put_url.method != "PUT":
                raise ValueError(f"expected a PUT URL; got {put_url.method}")

            file_size = file_path.stat().st_size
            with open(file_path, "rb") as fin:
                with _file_upload_progress_bar(
                    fin, total=file_size, desc=file.path
                ) as content:
                    headers = {
                        "content-md5": file.digest.md5,
                    }
                    headers.update(put_url.headers)
                    response = httpx.put(
                        put_url.url,
                        content=content,
                        headers=headers,
                        verify=not self._insecure,
                        timeout=self._timeout,
                    )
                    response.raise_for_status()
        _retry_not_found(self.finalize)(model.id)

    def workflow_logs(
        self, id: str, *, since: str | None = None, limit: int = 1000
    ) -> WorkflowLogsResponse:
        """Get workflow infrastructure logs for a Model.

        Returns logs from Kubernetes pods running the model workflow, including
        container startup, pod scheduling, and system errors.

        :param id: The ID of the model.
        :param since: Time range like '1h', '30m', '2d'. Optional.
        :param limit: Maximum number of log lines to return.
        :return: Workflow logs response with log entries.
        :raises HttpResponseError:
        """
        # Build query parameters
        params: dict[str, int | str] = {"limit": limit}
        if since is not None:
            params["since"] = since

        # Make HTTP request to the models workflow logs endpoint
        response = httpx.get(
            f"{self._client._endpoint}/models/{id}/logs/workflow",
            headers={"Authorization": f"Bearer {self._client._api_token}"},
            params=params,
            verify=not self._insecure,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return WorkflowLogsResponse.model_validate(response.json())

    async def stream_workflow_logs(self, id: str) -> AsyncIterable[WorkflowLogEntry]:
        """Stream workflow logs in real-time via WebSocket.

        :param id: The ID of the model.
        :yield: Individual log entries as they arrive.
        :raises HttpResponseError:
        """
        ws_endpoint = self._client._endpoint.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        ws_url = f"{ws_endpoint}/models/{id}/logs/workflow/stream"

        # Connect to WebSocket with authentication
        api_token = self._client._api_token
        headers = {"Authorization": f"Bearer {api_token}"}

        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            async for message in websocket:
                log_entry = WorkflowLogEntry.model_validate(json.loads(message))
                yield log_entry


class _Modules(
    _OpsBase[
        Module,
        ModuleCreateRequest,
        Module,
        ModulesOperationsGenerated,
    ],
    _ArtifactsMixin,
    _DocumentationMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.Module` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.modules`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=Module,
            _request_type=ModuleCreateRequest,
            _response_type=Module,
            _raw_ops=_client.raw.modules,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        name: Optional[str] = None,
    ) -> list[Module]:
        """Get all Modules matching a query. The query is a set of equality constraints
        specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword name:
        :return: list of ``Module`` resources satisfying the query.
        :raises HttpResponseError:
        """
        return [
            Module.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                name=name,
            )
        ]

    def create_package(
        self, package_directory: Path | str, *, account: str, name: str
    ) -> Module:
        """Create a Module resource describing a package structured as a directory tree.

        Internally, constructs a ``ModuleCreateRequest`` using information
        obtained from the directory tree, then calls ``create()`` with the
        constructed request.

        Typical usage::

            module = client.modules.create_package(package_directory, ...)
            client.modules.upload_package(module, package_directory)

        :param package_directory: The root directory of the package.
        :keyword account: The account that will own the Module resource.
        :keyword name: The name of the Module resource.
        :returns: The complete Module resource.
        """
        package_root = Path(package_directory)
        file_paths = [path for path in package_root.rglob("*") if path.is_file()]
        if not file_paths:
            raise ValueError(f"package_directory is empty: {package_directory}")
        artifact_paths = [
            str(Path(file_path).relative_to(package_root)) for file_path in file_paths
        ]
        artifacts = [
            Artifact(
                # FIXME: Is this a useful thing to do? It's redundant with
                # information in 'path'. Maybe it should just be 'code' or
                # something generic.
                kind="".join(file_path.suffixes),
                path=artifact_path,
                digest=Digest(
                    md5=binary.encode(binary.file_digest("md5", str(file_path))),
                ),
            )
            for file_path, artifact_path in zip(file_paths, artifact_paths)
        ]
        request = ModuleCreateRequest(
            account=account,
            name=name,
            artifacts=artifacts,
        )
        return self.create(request)

    def upload_package(self, module: Module, package_directory: Path | str) -> None:
        """Uploads the files in a package directory for which a Module resource has
        already been created.

        Typical usage::

            module = client.modules.create_package(package_directory, ...)
            client.modules.upload_package(module, package_directory)

        :param module: The Module resource for the package.
        :param package_directory: The root directory of the package.
        """
        if any(artifact.digest.md5 is None for artifact in module.artifacts):
            raise ValueError("artifact.digest.md5 must be set for all artifacts")
        for artifact in module.artifacts:
            assert artifact.digest.md5 is not None
            file_path = Path(package_directory) / artifact.path
            put_url_json = _retry_not_found(self._raw_ops.upload)(
                module.id, artifact.path
            )
            put_url = StorageSignedURL.model_validate(put_url_json)
            if put_url.method != "PUT":
                raise ValueError(f"expected a PUT URL; got {put_url.method}")

            file_size = file_path.stat().st_size
            with open(file_path, "rb") as fin:
                with _file_upload_progress_bar(
                    fin, total=file_size, desc=artifact.path
                ) as content:
                    headers = {
                        "content-md5": artifact.digest.md5,
                    }
                    headers.update(put_url.headers)
                    response = httpx.put(
                        put_url.url,
                        content=content,
                        headers=headers,
                        verify=not self._insecure,
                        timeout=self._timeout,
                    )
                    response.raise_for_status()
        _retry_not_found(self._raw_ops.finalize)(module.id)


class _Reports(
    _OpsBase[
        Report,
        ReportCreateRequest,
        Report,
        ReportsOperationsGenerated,
    ],
    _ArtifactsMixin,
    _LogsMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.Report` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.reports`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=Report,
            _request_type=ReportCreateRequest,
            _response_type=Report,
            _raw_ops=_client.raw.reports,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        report: Optional[str] = None,
        dataset: Optional[str] = None,
        evaluation: Optional[str] = None,
        inferenceService: Optional[str] = None,
        model: Optional[str] = None,
    ) -> list[Report]:
        """Get all Reports matching a query. The query is a set of equality constraints
        specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword report:
        :keyword dataset:
        :keyword evaluation:
        :keyword inferenceService:
        :keyword model:
        :return: list of ``Report`` resources satisfying the query.
        :raises HttpResponseError:
        """
        return [
            Report.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                report=report,
                dataset=dataset,
                evaluation=evaluation,
                inference_service=inferenceService,
                model=model,
            )
        ]


class _SafetyCases(
    _OpsBase[
        SafetyCase,
        AnalysisCreateRequest,
        SafetyCase,
        SafetyCasesOperationsGenerated,
    ],
    _ArtifactsMixin,
    _LogsMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.SafetyCase` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.safetycases`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        super().__init__(
            _client=_client,
            _entity_type=SafetyCase,
            _request_type=AnalysisCreateRequest,
            _response_type=SafetyCase,
            _raw_ops=_client.raw.safetycases,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        method: Optional[str] = None,
        methodName: Optional[str] = None,
        dataset: Optional[str] = None,
        evaluation: Optional[str] = None,
        inferenceService: Optional[str] = None,
        model: Optional[str] = None,
        inputs: Optional[list[str]] = None,
    ) -> list[SafetyCase]:
        """Get all SafetyCase entities matching a query. The query is a set of equality
        constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword method: Queries the ``.method.id`` nested field.
        :keyword methodName: Queries the ``.method.name`` nested field.
        :keyword dataset: Queries the ``.scope.dataset`` nested field.
        :keyword evaluation: Queries the ``.scope.evaluation`` nested field.
        :keyword inferenceService: Queries the ``.scope.inferenceService``
            nested field.
        :keyword model: Queries the ``.scope.model`` nested field.
        :keyword inputs: List of entity IDs. Matches SafetyCases that took
            *any* of these entities as inputs.
        :return: Entities matching the query
        :raises HttpResponseError:
        """
        return [
            SafetyCase.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                method=method,
                method_name=methodName,
                dataset=dataset,
                evaluation=evaluation,
                inference_service=inferenceService,
                model=model,
                inputs=(",".join(inputs) if inputs is not None else None),
            )
        ]

    def scores(self, id: str) -> list[Score]:
        """Get all Scores associated with a SafetyCase.

        :param id: The ID of the SafetyCase.
        :return: A list of Scores associated with the SafetyCase.
        """
        return [Score.model_validate(obj) for obj in self._raw_ops.scores(id)]

    def query_scores(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        method: Optional[str] = None,
        methodName: Optional[str] = None,
        dataset: Optional[str] = None,
        evaluation: Optional[str] = None,
        inferenceService: Optional[str] = None,
        model: Optional[str] = None,
        inputs: Optional[list[str]] = None,
    ) -> list[Score]:
        """Get all Scores associated with SafetyCases matching a query.

        The query is a set of equality constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the
            given key-value pairs.
        :keyword method: Queries the ``.method.id`` nested field.
        :keyword methodName: Queries the ``.method.name`` nested field.
        :keyword dataset: Queries the ``.scope.dataset`` nested field.
        :keyword evaluation: Queries the ``.scope.evaluation`` nested field.
        :keyword inferenceService: Queries the ``.scope.inferenceService``
            nested field.
        :keyword model: Queries the ``.scope.model`` nested field.
        :keyword inputs: List of entity IDs. Matches SafetyCases that took
            *any* of these entities as inputs.
        :return: Scores associated with SafetyCases that match the query.
        :raises HttpResponseError:
        """
        return [
            Score.model_validate(obj)
            for obj in self._raw_ops.query_scores(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                method=method,
                method_name=methodName,
                dataset=dataset,
                evaluation=evaluation,
                inference_service=inferenceService,
                model=model,
                inputs=(",".join(inputs) if inputs is not None else None),
            )
        ]

    def workflow_logs(
        self, id: str, *, since: str | None = None, limit: int = 1000
    ) -> WorkflowLogsResponse:
        """Get workflow infrastructure logs for a SafetyCase.

        Returns logs from Kubernetes pods running the safety case workflow, including
        container startup, pod scheduling, and system errors.

        :param id: The ID of the safety case.
        :param since: Time range like '1h', '30m', '2d'. Optional.
        :param limit: Maximum number of log lines to return.
        :return: Workflow logs response with log entries.
        :raises HttpResponseError:
        """
        # Build query parameters
        params: dict[str, int | str] = {"limit": limit}
        if since is not None:
            params["since"] = since

        # Make HTTP request to the safetycases workflow logs endpoint
        response = httpx.get(
            f"{self._client._endpoint}/safetycases/{id}/logs/workflow",
            headers={"Authorization": f"Bearer {self._client._api_token}"},
            params=params,
            verify=not self._insecure,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return WorkflowLogsResponse.model_validate(response.json())

    async def stream_workflow_logs(self, id: str) -> AsyncIterable[WorkflowLogEntry]:
        """Stream workflow logs in real-time via WebSocket.

        :param id: The ID of the safety case.
        :yield: Individual log entries as they arrive.
        :raises HttpResponseError:
        """
        ws_endpoint = self._client._endpoint.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        ws_url = f"{ws_endpoint}/safetycases/{id}/logs/workflow/stream"

        # Connect to WebSocket with authentication
        api_token = self._client._api_token
        headers = {"Authorization": f"Bearer {api_token}"}

        async with websockets.connect(ws_url, extra_headers=headers) as websocket:
            async for message in websocket:
                log_entry = WorkflowLogEntry.model_validate(json.loads(message))
                yield log_entry


class _Teams:
    def __init__(
        self,
        _client: Client,
    ):
        self._client = _client
        self.__raw_ops = _client.raw.teams

    @property
    def _insecure(self) -> bool:
        return self._client.insecure

    @property
    def _timeout(self) -> Timeout:
        return self._client.timeout

    @property
    def _raw_ops(self) -> TeamsOperationsGenerated:
        return self.__raw_ops

    def get(self, id: str) -> Team:
        """Get an entity by its .id.

        :param id: The entity ID
        :return: The entity with the given ID.
        """
        return Team.model_validate(self._raw_ops.get(id))

    def label(self, id: str, labels: dict[str, Optional[str]]) -> None:
        """Label the specified entity with key-value pairs (stored in the ``.labels``
        field).

        Providing ``None`` for the value deletes the label. Key-value mappings
        not given in ``labels`` remain unchanged.

        See :class:`~dyff.schema.platform.Label` for a description of the
        constraints on label keys and values.

        :param id: The ID of the entity to label.
        :param labels: The label keys and values.
        """
        if not labels:
            return
        labels = LabelsEditRequest(labels=labels).model_dump(by_alias=True)
        self._raw_ops.label(id, labels)

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        challenge: Optional[str] = None,
    ) -> list[Team]:
        """Get all SafetyCase entities matching a query. The query is a set of equality
        constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the given key-
            value pairs.
        :keyword challenge:
        :raises HttpResponseError:
        """
        return [
            Team.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
                challenge=challenge,
            )
        ]


class _Audits(_LogsMixin):
    """Operations on :class:`~dyff.schema.platform.Audit` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.audits`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(self, _client: Client):
        self._client = _client

    @property
    def _insecure(self) -> bool:
        return self._client.insecure

    @property
    def _timeout(self) -> Timeout:
        return self._client.timeout

    def get(self, id: str) -> Audit:
        raise NotImplementedError()


class _UseCases(
    _OpsBase[UseCase, ConcernCreateRequest, UseCase, UseCasesOperationsGenerated],
    # _DocumentationMixin,
    _PublishMixin,
):
    """Operations on :class:`~dyff.schema.platform.UseCase` entities.

    .. note::

        Do not instantiate this class. Access it through the
        ``.usecases`` attribute of :class:`~dyff.client.Client`.
    """

    def __init__(
        self,
        _client: Client,
    ):
        super().__init__(
            _client=_client,
            _entity_type=UseCase,
            _request_type=ConcernCreateRequest,
            _response_type=UseCase,
            _raw_ops=_client.raw.usecases,
        )

    def query(
        self,
        *,
        query: Optional[QueryT] = None,
        id: Optional[str] = None,
        account: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> list[UseCase]:
        """Get all SafetyCase entities matching a query. The query is a set of equality
        constraints specified as key-value pairs.

        :keyword query:
        :keyword id:
        :keyword account:
        :keyword status:
        :keyword reason:
        :keyword labels: Matches entities that are labeled with *all* of the given key-
            value pairs.
        :raises HttpResponseError:
        """
        return [
            UseCase.model_validate(obj)
            for obj in self._raw_ops.query(
                query=_encode_query(query),
                id=id,
                account=account,
                status=status,
                reason=reason,
                labels=_encode_labels(labels),
            )
        ]

    # FIXME: This method should be provided by _DocumentationMixin, but first
    # we need to migrate all the other types to store documentation as a
    # member rather than a separate entity.

    def edit_documentation(
        self, id: str, edit_request: DocumentationEditRequest
    ) -> None:
        """Edit the documentation associated with an entity.

        :param id: The ID of the entity.
        :param edit_request: Object containing the edits to make.
        """
        self._raw_ops.edit_documentation(id, edit_request.model_dump(by_alias=True))


__all__ = [
    "_Artifacts",
    "_Audits",
    "_Challenges",
    "_Datasets",
    "_Evaluations",
    "_Families",
    "_InferenceServices",
    "_InferenceSessions",
    "_Measurements",
    "_Methods",
    "_Models",
    "_Modules",
    "_Reports",
    "_SafetyCases",
    "_Teams",
    "_UseCases",
]
