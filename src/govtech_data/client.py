from functools import lru_cache
from typing import Type, Union

import requests
from loguru import logger
from polars import DataFrame
from pydantic import BaseModel, validate_arguments
from thefuzz import fuzz, process

from govtech_data.models.api import (
    DatastoreSearch,
    PackageShow,
    ResourceShow,
    SearchPackage,
    PackageResourceContent,
    PackageContent,
)
from govtech_data.models.resources.datastore_search import DatastoreSearchModel
from govtech_data.models.resources.package_list import PackageListModel
from govtech_data.models.resources.package_show import (
    PackageShowModel,
    Result as PackageShowModelResult,
)
from govtech_data.models.resources.resource_show import ResourceShowModel
from govtech_data.utils.content import fetch_url, convert_response_to_io

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
    @validate_arguments
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
    @lru_cache(maxsize=512)
    @validate_arguments
    def resource_show(cls, resource_id: str) -> Union[BaseModel, ResourceShowModel]:
        return cls.get_model_from_json_response(
            API_ENDPOINTS.get("ckan_resource_show"),
            ResourceShow(**{"id": resource_id}).dict(),
            ResourceShowModel,
        )

    @classmethod
    @lru_cache(maxsize=512)
    @validate_arguments
    def package_show(cls, package_id: str) -> Union[BaseModel, PackageShowModel]:
        return cls.get_model_from_json_response(
            API_ENDPOINTS.get("ckan_package_show"),
            PackageShow(**{"id": package_id}).dict(),
            PackageShowModel,
        )

    @classmethod
    @lru_cache(maxsize=1)
    @validate_arguments
    def package_list(cls) -> Union[BaseModel, PackageListModel]:
        return cls.get_model_from_json_response(
            API_ENDPOINTS.get("ckan_package_list"), {}, PackageListModel
        )

    @classmethod
    @validate_arguments
    def search_package(cls, name: str, limit: int = 10) -> list[SearchPackage]:
        return [
            SearchPackage(package_id=package_id, score=score)
            for (package_id, score) in process.extract(
                name,
                cls.package_list().result,
                scorer=fuzz.token_set_ratio,
                limit=limit,
            )
        ]

    @classmethod
    @validate_arguments
    def get_model_from_json_response(
        cls, url: str, params: dict, model: Type[BaseModel]
    ):
        if url is None:
            raise Exception("url cannot be None!")
        if model is None:
            raise Exception("model cannot be None!")
        logger.debug(f"endpoint: {url}")
        resp = requests.get(
            url,
            params=params,
            headers=COMMON_HEADERS,
            timeout=DEFAULT_TIMEOUT_IN_SECONDS,
        )
        if not resp.ok:
            resp.raise_for_status()
        return model(**resp.json())

    @classmethod
    @validate_arguments
    def fetch_resources_from_package_result(
        cls, package_result: PackageShowModelResult, limit: int = 0
    ) -> list[PackageResourceContent]:
        r = []
        for resource in package_result.resources:
            if limit != 0 and len(r) >= limit:
                break
            resp = fetch_url(resource.url)
            r.append(
                PackageResourceContent(
                    resource=resource, content=convert_response_to_io(resp)
                )
            )
        return r

    @classmethod
    @validate_arguments
    def fetch_content_from_package(cls, package_name: str, limit: int = 0):
        package_show_model: Union[PackageShowModel, None] = cls.package_show(
            package_name
        )
        if package_show_model.result is None:
            return None
        return PackageContent(
            package=package_show_model.result,
            resources=cls.fetch_resources_from_package_result(
                package_show_model.result, limit
            ),
        )

    @classmethod
    @validate_arguments
    def fetch_dataframe_from_package(cls, package_name: str) -> Union[DataFrame, None]:
        package_content = cls.fetch_content_from_package(package_name, 1)
        if len(package_content.resources) == 0:
            return None
        return package_content.resources[0].get_dataframe()
