from functools import lru_cache
from typing import Type, Union

import requests

from fuzzywuzzy import process
from loguru import logger
from pydantic import BaseModel

from src.govtech_data.models.api import (
    DatastoreSearch,
    PackageShow,
    ResourceShow,
    SearchPackage,
)
from src.govtech_data.models.resources.datastore_search import DatastoreSearchModel
from src.govtech_data.models.resources.package_list import PackageListModel
from src.govtech_data.models.resources.package_show import PackageShowModel
from src.govtech_data.models.resources.resource_show import ResourceShowModel

API_ENDPOINTS = {
    "ckan_datastore_search": "https://data.gov.sg/api/action/datastore_search",
    "ckan_package_show": "https://data.gov.sg/api/action/package_show",
    "ckan_package_list": "https://data.gov.sg/api/action/package_list",
    "ckan_resource_show": "https://data.gov.sg/api/action/resource_show",
}

COMMON_HEADERS = {"accept": "application/json"}

DEFAULT_TIMEOUT_IN_SECONDS = 30


class GovTechClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GovTechClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        pass

    @classmethod
    def datastore_search(
        cls, resource_id: str, **kwargs
    ) -> Union[BaseModel, DatastoreSearchModel]:
        kwargs["resource_id"] = resource_id
        return cls.get_model_from_json_response(
            API_ENDPOINTS.get("ckan_datastore_search"),
            DatastoreSearch(**kwargs).dict(),
            DatastoreSearchModel,
        )

    @classmethod
    def resource_show(cls, resource_id: str) -> Union[BaseModel, ResourceShowModel]:
        return cls.get_model_from_json_response(
            API_ENDPOINTS.get("ckan_resource_show"),
            ResourceShow(**{"id": resource_id}).dict(),
            ResourceShowModel,
        )

    @classmethod
    def package_show(cls, package_id: str) -> Union[BaseModel, PackageShowModel]:
        return cls.get_model_from_json_response(
            API_ENDPOINTS.get("ckan_package_show"),
            PackageShow(**{"id": package_id}).dict(),
            PackageShowModel,
        )

    @classmethod
    @lru_cache(maxsize=1)
    def package_list(cls) -> Union[BaseModel, PackageListModel]:
        return cls.get_model_from_json_response(
            API_ENDPOINTS.get("ckan_package_list"), {}, PackageListModel
        )

    @classmethod
    def search_package(cls, name: str, limit: int = 10) -> list[SearchPackage]:
        return [
            SearchPackage(package_id=package_id, score=score)
            for (package_id, score) in process.extract(
                name, cls.package_list().result, limit=limit
            )
        ]

    @classmethod
    def get_model_from_json_response(
        cls, url: str, params: dict, model: Type[BaseModel]
    ):
        if url is None:
            raise Exception("url cannot be None!")
        if model is None:
            raise Exception("model cannot be None!")
        logger.debug(f"endpoint name: {url}")
        resp = requests.get(
            url,
            params=params,
            headers=COMMON_HEADERS,
            timeout=DEFAULT_TIMEOUT_IN_SECONDS,
        )
        if not resp.ok:
            resp.raise_for_status()
        return model(**resp.json())
