from typing import Any, Optional, Type

import jsonref
from pydantic import BaseModel, Field


class ThoughtsParameter(BaseModel):
    notes: str = Field(description="1. short numbered bulleted list\n2. for notes")
    next_command: str = Field(description="")

    thoughts: str = Field(description="short thoughts in 1 or 2 short sentences")
    reasoning: str = Field(description="short reasoning in 1 or 2 short sentences")
    plan: str = Field(description="1. short numbered bulleted list\n2. that conveys long-term plan")
    criticism: str = Field(description="short constructive self-criticism in 1 or 2 short sentences")
    speak: str = Field(description="thoughts summary to say to user in 1 or 2 short sentences")

    class Config:
        @staticmethod
        def schema_extra(schema: dict[str, Any]) -> None:
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)
            schema.pop("title", None)


class BaseParameter(BaseModel):
    current_thoughts: ThoughtsParameter = Field(description="Current thoughts")

    class Config:
        @staticmethod
        def schema_extra(schema: dict[str, Any]) -> None:
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)
            schema.pop("title", None)


def get_gpt_function(name: str, description: Optional[str], parameters: Optional[Type[BaseParameter]]) -> dict:
    d = {"name": name}
    if description:
        d["description"] = description
    if parameters:
        use_schema = jsonref.replace_refs(parameters.schema(), merge_props=True, proxies=False, lazy_load=False)
        use_schema.pop("definitions", None)
        d["parameters"] = use_schema
    return d


class DatasetSearchParameters(BaseParameter):
    input: str = Field(description="Query")


class GetDatasetSchemaParameters(BaseParameter):
    id: str = Field(description="Dataset id")


class GetAllDistinctValuesInADatasetFieldParameters(BaseParameter):
    id: str = Field(description="Dataset id")
    field: str = Field(description="Field name")


class SearchForRelevantValuesInADatasetFieldParameters(BaseParameter):
    id: str = Field(description="Dataset id")
    field: str = Field(description="Field name")
    value: str = Field(description="Value")


class GenerateFullCodeParameters(BaseParameter):
    code: str = Field(description="Full code")


class GenerateOptimizedCodeParameters(BaseParameter):
    code: str = Field(description="Fixed and optimized code")


class TaskCompleteParameters(BaseParameter):
    reason: str = Field(description="Reason")


class KeywordPhrasesParameter(BaseParameter):
    phrases: list[str] = Field(description="Keywords")


KEYWORD_PHRASES_FUNCTION = [get_gpt_function("phrases", "Get list of phrases", KeywordPhrasesParameter)]

LIST_OF_FUNCTIONS = [
    get_gpt_function("dataset_search", "Search for dataset ids", DatasetSearchParameters),
    get_gpt_function(
        "get_dataset_schema",
        "Get schema for dataset when you have the dataset id. You should NEVER call this function before dataset_search has been called in the conversation",
        GetDatasetSchemaParameters,
    ),
    get_gpt_function(
        "get_all_distinct_values_in_a_dataset_field",
        "Query for unique values and counts in a single field from a dataset when you have the dataset id and schema. You should NEVER call this function before dataset_search has been called in the conversation",
        GetAllDistinctValuesInADatasetFieldParameters,
    ),
    get_gpt_function(
        "search_for_relevant_values_in_a_dataset_field",
        "Search for the most similar values in a single field from a dataset when you have the dataset id and schema. You should NEVER call this function before dataset_search has been called in the conversation",
        SearchForRelevantValuesInADatasetFieldParameters,
    ),
    get_gpt_function("generate_full_code", "Generate full code", GenerateFullCodeParameters),
    get_gpt_function(
        "generate_optimized_code",
        "Fix the existing code and generates optimized code. Ensure that all modules are imported. Ensure that aggregation operations after a groupby are only run on numeric columns based on the dataset's schema.",
        GenerateOptimizedCodeParameters,
    ),
    get_gpt_function("task_complete", "Task Complete (Shutdown)", TaskCompleteParameters),
]
