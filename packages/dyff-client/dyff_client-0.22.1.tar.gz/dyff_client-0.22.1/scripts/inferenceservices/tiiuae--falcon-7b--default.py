# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import json
import os

from dyff.client.client import Client
from dyff.schema.platform import (
    Accelerator,
    AcceleratorGPU,
    DataSchema,
    DyffDataSchema,
    InferenceInterface,
    InferenceServiceRunner,
    InferenceServiceRunnerKind,
    ModelResources,
    SchemaAdapter,
)
from dyff.schema.requests import InferenceServiceCreateRequest

API_KEY: str = os.environ["DYFF_API_KEY"]
ACCOUNT: str = "public"

dyffapi = Client(api_key=API_KEY)

model = dyffapi.models.query(name="tiiuae/falcon-7b", account="public")
assert len(model) == 1 and model[0].id == "371288ec69724bf8bebf51811c581f6b"
model_id = model[0].id

service_request = InferenceServiceCreateRequest(
    account=ACCOUNT,
    name="tiiuae/falcon-7b/default",
    model=model_id,
    runner=InferenceServiceRunner(
        kind=InferenceServiceRunnerKind.VLLM,
        # T4 GPUs don't support bfloat format, so force standard float format
        args=[
            "--dtype",
            "float16",
        ],
        accelerator=Accelerator(
            kind="GPU",
            gpu=AcceleratorGPU(
                hardwareTypes=["nvidia.com/gpu-a100"],
                memory="16Gi",
            ),
        ),
        resources=ModelResources(
            storage="20Gi",
            memory="16Gi",
        ),
    ),
    interface=InferenceInterface(
        # This is the inference endpoint for the vLLM runner
        endpoint="generate",
        # The output records should look like: {"text": "To be, or not to be"}
        outputSchema=DataSchema.make_output_schema(
            DyffDataSchema(
                components=["text.Text"],
            ),
        ),
        # How to convert the input dataset into the format the runner expects
        inputPipeline=[
            # {"text": "The question"} -> {"prompt": "The question"}
            SchemaAdapter(
                kind="TransformJSON",
                configuration={"prompt": "$.text"},
            ),
        ],
        # How to convert the runner output to match outputSchema
        outputPipeline=[
            # {"text": ["The answer"]} -> [{"text": "The answer"}]
            SchemaAdapter(
                kind="ExplodeCollections",
                configuration={"collections": ["text"]},
            ),
        ],
    ),
)

print(json.dumps(service_request.dict(), indent=2))

service = dyffapi.inferenceservices.create(service_request)
print(f"created inferenceservice:\n{service}")
