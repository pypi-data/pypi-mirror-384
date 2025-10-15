from dataclasses import field
from functools import cached_property
import os
import time
from uuid import UUID
from typing import Any, Optional
from typing_extensions import Self

from flask import has_request_context, request
from pydantic import Field, field_validator, model_validator

from vellum import ApiVersionEnum, Vellum
from vellum.client.core import UniversalBaseModel
from vellum.workflows.context import ExecutionContext
from vellum.workflows.vellum_client import create_vellum_client
from workflow_server.utils.utils import convert_json_inputs_to_vellum

DEFAULT_TIMEOUT_SECONDS = int(os.getenv("MAX_WORKFLOW_RUNTIME_SECONDS", 1800))


class BaseExecutorContext(UniversalBaseModel):
    inputs: dict = Field(default_factory=dict)
    state: Optional[dict] = None
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    files: dict[str, str]
    environment_api_key: str
    api_version: Optional[ApiVersionEnum] = None
    execution_id: UUID
    module: str
    execution_context: ExecutionContext = field(default_factory=ExecutionContext)
    request_start_time: int = Field(default_factory=lambda: time.time_ns())
    stream_start_time: int = 0
    vembda_public_url: Optional[str] = None
    node_output_mocks: Optional[list[Any]] = None
    environment_variables: Optional[dict[str, str]] = None
    previous_execution_id: Optional[UUID] = None
    feature_flags: Optional[dict[str, bool]] = None

    @field_validator("inputs", mode="before")
    @classmethod
    def convert_inputs(cls, v: Any) -> dict:
        if v is None:
            return {}
        if isinstance(v, list):
            return convert_json_inputs_to_vellum(v)
        return v

    @field_validator("api_version", mode="before")
    @classmethod
    def extract_api_version_from_headers(cls, v: Any) -> Any:
        if v is not None:
            return v
        if has_request_context():
            api_version_header = request.headers.get("x-api-version")
            if api_version_header:
                return api_version_header
        return v

    @property
    def container_overhead_latency(self) -> int:
        return self.stream_start_time - self.request_start_time if self.stream_start_time else -1

    @property
    def trace_id(self) -> UUID:
        return self.execution_context.trace_id

    @cached_property
    def vellum_client(self) -> Vellum:
        return create_vellum_client(
            api_key=self.environment_api_key,
            api_version=self.api_version,
        )

    def __hash__(self) -> int:
        # do we think we need anything else for a unique hash for caching?
        return hash(str(self.execution_id))


class WorkflowExecutorContext(BaseExecutorContext):
    node_id: Optional[UUID] = None  # Sent during run from node UX


class NodeExecutorContext(BaseExecutorContext):
    node_id: Optional[UUID] = None
    node_module: Optional[str] = None
    node_name: Optional[str] = None

    @model_validator(mode="after")
    def validate_node_identification(self) -> Self:
        if not self.node_id and not (self.node_module and self.node_name):
            raise ValueError("Either node_id or both node_module and node_name must be provided")
        return self
