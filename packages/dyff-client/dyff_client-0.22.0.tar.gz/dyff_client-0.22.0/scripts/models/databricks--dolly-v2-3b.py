# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import os

from dyff.client.client import Client
from dyff.schema.platform import (
    ModelArtifact,
    ModelArtifactHuggingFaceCache,
    ModelArtifactKind,
    ModelResources,
    ModelSource,
    ModelSourceHuggingFaceHub,
    ModelSourceKinds,
    ModelStorage,
    ModelStorageMedium,
)
from dyff.schema.requests import ModelCreateRequest

API_KEY: str = os.environ["DYFF_API_KEY"]
ACCOUNT: str = "public"

dyffapi = Client(api_key=API_KEY)

model_request = ModelCreateRequest(
    account=ACCOUNT,
    name="databricks/dolly-v2-3b",
    artifact=ModelArtifact(
        kind=ModelArtifactKind.HuggingFaceCache,
        huggingFaceCache=ModelArtifactHuggingFaceCache(
            repoID="databricks/dolly-v2-3b",
            revision="f6c9be08f16fe4d3a719bee0a4a7c7415b5c65df",
        ),
    ),
    source=ModelSource(
        kind=ModelSourceKinds.HuggingFaceHub,
        huggingFaceHub=ModelSourceHuggingFaceHub(
            repoID="databricks/dolly-v2-3b",
            revision="f6c9be08f16fe4d3a719bee0a4a7c7415b5c65df",
        ),
    ),
    storage=ModelStorage(
        medium=ModelStorageMedium.PersistentVolume,
    ),
    resources=ModelResources(
        storage="10Gi",
        memory="16Gi",
    ),
)

model = dyffapi.models.create(model_request)
print(model)
