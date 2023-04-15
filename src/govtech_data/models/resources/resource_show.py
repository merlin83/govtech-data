# generated by datamodel-codegen:
#   filename:  resource_show.json
#   timestamp: 2023-04-14T09:27:05+00:00

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Extra


class NullValues(BaseModel):
    class Config:
        extra = Extra.allow

    count: Optional[int] = None


class Field(BaseModel):
    class Config:
        extra = Extra.allow

    name: Optional[str] = None
    format: Optional[str] = None
    coordinate_system: Optional[str] = None
    null_values: Optional[NullValues] = None
    detected_types: Optional[str] = None
    title: Optional[str] = None
    total: Optional[int] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    unit_of_measure: Optional[str] = None


class Result(BaseModel):
    class Config:
        extra = Extra.allow

    cache_last_updated: Optional[Any] = None
    coverage_start: Optional[str] = None
    package_id: Optional[str] = None
    validation_state: Optional[str] = None
    coverage_end: Optional[str] = None
    datastore_active: Optional[bool] = None
    id: Optional[str] = None
    size: Optional[Any] = None
    reject_reason: Optional[str] = None
    redo_approval: Optional[bool] = None
    state: Optional[str] = None
    hash: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    mimetype_inner: Optional[Any] = None
    url_type: Optional[str] = None
    mimetype: Optional[Any] = None
    cache_url: Optional[Any] = None
    name: Optional[str] = None
    created: Optional[str] = None
    url: Optional[str] = None
    fields: Optional[List[Field]] = None
    last_modified: Optional[str] = None
    position: Optional[int] = None
    revision_id: Optional[str] = None
    resource_type: Optional[Any] = None


class ResourceShowModel(BaseModel):
    class Config:
        extra = Extra.allow

    help: Optional[str] = None
    success: Optional[bool] = None
    result: Optional[Result] = None