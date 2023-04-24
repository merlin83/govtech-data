import io

import polars as pl
from pydantic import BaseModel

from govtech_data.models.resources import package_show

INFER_SCHEMA_LENGTH = None  # this does a full table scan, which is slow but acceptible since most datasets are small


class PackageShow(BaseModel):
    id: str


class ResourceShow(BaseModel):
    id: str


class DatastoreSearch(BaseModel):
    resource_id: str
    limit: int | None = 100
    offset: int | None = 0
    fields: str | None
    filters: str | None
    q: str | None
    sort: str | None
    records_format: str | None


class SearchPackage(BaseModel):
    package_id: str
    score: int


class PackageResourceContent(BaseModel):
    resource: package_show.Resource
    content: io.StringIO

    class Config:
        arbitrary_types_allowed = True

    def get_dataframe(self):
        self.content.seek(0)
        return pl.read_csv(
            self.content,
            quote_char=None,
            use_pyarrow=True,
            infer_schema_length=INFER_SCHEMA_LENGTH,
        )


class PackageContent(BaseModel):
    package: package_show.Result
    resources: list[PackageResourceContent] | None


class Messages(BaseModel):
    role: str
    content: str
