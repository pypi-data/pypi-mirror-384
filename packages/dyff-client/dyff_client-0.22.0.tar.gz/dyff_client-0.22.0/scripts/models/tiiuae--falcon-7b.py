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
    name="tiiuae/falcon-7b",
    artifact=ModelArtifact(
        kind=ModelArtifactKind.HuggingFaceCache,
        huggingFaceCache=ModelArtifactHuggingFaceCache(
            repoID="tiiuae/falcon-7b",
            revision="898df1396f35e447d5fe44e0a3ccaaaa69f30d36",
        ),
    ),
    source=ModelSource(
        kind=ModelSourceKinds.HuggingFaceHub,
        huggingFaceHub=ModelSourceHuggingFaceHub(
            repoID="tiiuae/falcon-7b",
            revision="898df1396f35e447d5fe44e0a3ccaaaa69f30d36",
        ),
    ),
    storage=ModelStorage(
        medium=ModelStorageMedium.PersistentVolume,
    ),
    resources=ModelResources(
        storage="20Gi",
        memory="20Gi",
    ),
)

model = dyffapi.models.create(model_request)
print(model)
