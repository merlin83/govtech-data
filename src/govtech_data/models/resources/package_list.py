# generated by datamodel-codegen:
#   filename:  package_list.json
#   timestamp: 2023-04-14T09:27:05+00:00

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Extra


class PackageListModel(BaseModel):
    class Config:
        extra = Extra.allow

    help: Optional[str] = None
    success: Optional[bool] = None
    result: Optional[List[str]] = None