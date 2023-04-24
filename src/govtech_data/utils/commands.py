import json
from typing import Any

import yaml
from thefuzz import fuzz, process

from govtech_data import GovTechClient
from govtech_data.models.resources.package_show import PackageShowModel

SEARCH_SCORE_THRESHOLD = 50


def dataset_search(input_str: str) -> str:
    return dataset_search_batch([input_str])


def dataset_search_batch(input_strs: list[str]) -> str:
    dupes = {}
    for input_str in input_strs:
        for result in GovTechClient.search_package(input_str):
            if result.package_id in dupes and dupes[result.package_id] <= result.score:
                continue
            if result.score <= SEARCH_SCORE_THRESHOLD:
                continue
            # results.append({"id": result.package_id, "score": result.score})
            dupes[result.package_id] = result.score
    # results = sorted(
    #     [{"id": k, "score": v} for k, v in dupes.items()],
    #     key=lambda x: x.get("score"),
    #     reverse=True,
    # )
    ordered_dict = {}
    for k, v in sorted(dupes.items(), key=lambda x: x[1], reverse=True):
        ordered_dict[k] = v
    return f"Datasets found for {json_dump(input_strs)}:\n\n" + json_dump(ordered_dict)


def get_dataset_metadata(package_id: str) -> str:
    package_show: PackageShowModel = GovTechClient.package_show(package_id)
    return f"Metadata for {package_id}: " + yaml_dump(
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
    return f"All distinct values in {package_id}: {field_name}:\n\n" + json_dump(
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
        return yaml_dump({"values": {i[0]: 100 for i in unique_values}})
    ordered_dict = {
        n: s
        for n, s in process.extract(
            field_value, unique_values, scorer=fuzz.token_set_ratio, limit=10
        )
    }
    return f"Similar values found in {field_name}:\n\n" + json_dump(ordered_dict)


def json_dump(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"))


def yaml_dump(obj: Any) -> str:
    return yaml.dump(obj, sort_keys=False)
