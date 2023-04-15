from pydantic import BaseModel


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
