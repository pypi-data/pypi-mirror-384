"""Endpoints related to pipelines."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import Pipeline

PipelineInput = Union[Pipeline, Mapping[str, Any]]


def _serialize_pipelines(pipelines: Iterable[PipelineInput]) -> List[dict]:
    return [
        pipeline.dict(exclude_none=True)
        if isinstance(pipeline, Pipeline)
        else Pipeline.model_validate(pipeline).dict(exclude_none=True)
        for pipeline in pipelines
    ]


async def post_pipelines(
    client: BaseWazzupClient, pipelines: Iterable[PipelineInput]
) -> Any:
    payload = _serialize_pipelines(pipelines)
    return await client._request("POST", "/v3/pipelines", json=payload)


async def get_pipelines(
    client: BaseWazzupClient
) -> Any:
    return await client._request("GET", "/v3/pipelines")
