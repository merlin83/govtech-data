import json
from typing import Any

from fuzzywuzzy import process

from govtech_data import GovTechClient
from govtech_data.models.resources.package_show import PackageShowModel


def dataset_search(input_str: str) -> str:
    return f"Datasets found for {input_str}: " + json_dumps(
        [
            {"id": result.package_id, "score": result.score}
            for result in GovTechClient.search_package(input_str)
        ]
    )


def get_dataset_metadata(package_id: str) -> str:
    package_show: PackageShowModel = GovTechClient.package_show(package_id)
    return f"Metadata for {package_id}: " + json_dumps(
        {
            "id": package_id,
            "description": package_show.result.description,
        }
    )


def get_dataset_schema(package_id: str) -> str:
    df = GovTechClient.fetch_dataframe_from_package(package_id)
    if df is None:
        return ""
    return f"Schema for {package_id}: " + str(df.schema)


def get_all_distinct_values_and_counts_in_a_dataset_field(
    package_id: str, field_name: str
) -> list[(str, int)]:
    df = GovTechClient.fetch_dataframe_from_package(package_id)
    if df is None:
        return []
    return [
        (i.get(field_name), i.get("count"))
        for i in df.groupby(field_name, maintain_order=True).count().to_dicts()
    ]


def get_all_distinct_values_in_a_dataset_field(package_id: str, field_name: str) -> str:
    return f"All distinct values in {field_name}: " + json_dumps(
        [
            i[0]
            for i in get_all_distinct_values_and_counts_in_a_dataset_field(
                package_id, field_name
            )
        ]
    )


def search_for_relevant_values_in_a_dataset_field(
    package_id: str, field_name: str, field_value: str
) -> str:
    unique_values = [
        i[0]
        for i in get_all_distinct_values_and_counts_in_a_dataset_field(
            package_id, field_name
        )
    ]
    if field_value is None or len(field_value) == 0:
        return json_dumps([{"name": i[0], "score": 100} for i in unique_values])
    return f"Similar values found in {field_name}: " + json_dumps(
        [
            {"name": i[0], "score": i[1]}
            for i in process.extract(field_value, unique_values, limit=10)
        ]
    )


def json_dumps(obj: Any):
    return json.dumps(obj, separators=(",", ":"))
