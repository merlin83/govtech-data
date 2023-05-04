# govtech-data: An easy-to-use, unofficial library to access data.gov.sg

## Features

- govtech-data
  - An easy search function to find the datasets you are looking for!
  - Smart caching to reduce the number of API calls!
- govtech-data[openai]
  - An easy-to-use client that uses OpenAI models to answer your questions from any of the datasets available on data.gov.sg!


## Optional requirements

- [OPENAI_API_KEY](https://platform.openai.com/account/api-keys) exported as an environment variable or via dotenv

## Installation

To install the client library
```bash
pip install govtech-data
```

To install the client library with OpenAI functionality
```bash
pip install govtech-data[openai]
```

## Examples

### To search for a dataset
```python
In [1]: from govtech_data import GovTechClient

In [2]: GovTechClient.search_package("resale prices", limit=5)
2023-04-17 16:09:27.818 | DEBUG    | govtech_data.client:get_model_from_json_response:109 - endpoint: https://data.gov.sg/api/action/package_list
Out[2]:
[SearchPackage(package_id='resale-flat-prices', score=95),
 SearchPackage(package_id='median-resale-prices-for-registered-applications-by-town-and-flat-type', score=90),
 SearchPackage(package_id='average-retail-prices-of-selected-consumer-items-monthly', score=86),
 SearchPackage(package_id='average-retail-prices-of-selected-items-annual', score=86),
 SearchPackage(package_id='changes-in-value-added-per-worker-at-current-market-prices-by-industry-ssic-2015-quarterly', score=86)]
 ```

### To read from a dataset
```python
In [1]: from govtech_data import GovTechClient

In [2]: df = GovTechClient.fetch_dataframe_from_package("resale-flat-prices")
2023-04-17 16:10:35.600 | DEBUG    | govtech_data.client:get_model_from_json_response:109 - endpoint: https://data.gov.sg/api/action/package_show
2023-04-17 16:10:36.529 | DEBUG    | govtech_data.utils.content:fetch_url:11 - Fetching url - https://storage.data.gov.sg/resale-flat-prices/resources/resale-flat-prices-based-on-registration-date-from-jan-2017-onwards-2023-04-17T03-28-08Z.csv

In [3]: df
Out[3]:
shape: (151_157, 11)
┌─────────┬────────────┬───────────┬───────┬───┬────────────────┬─────────────────────┬────────────────────┬──────────────┐
│ month   ┆ town       ┆ flat_type ┆ block ┆ … ┆ flat_model     ┆ lease_commence_date ┆ remaining_lease    ┆ resale_price │
│ ---     ┆ ---        ┆ ---       ┆ ---   ┆   ┆ ---            ┆ ---                 ┆ ---                ┆ ---          │
│ str     ┆ str        ┆ str       ┆ str   ┆   ┆ str            ┆ i64                 ┆ str                ┆ f64          │
╞═════════╪════════════╪═══════════╪═══════╪═══╪════════════════╪═════════════════════╪════════════════════╪══════════════╡
│ 2017-01 ┆ ANG MO KIO ┆ 2 ROOM    ┆ 406   ┆ … ┆ Improved       ┆ 1979                ┆ 61 years 04 months ┆ 232000.0     │
│ 2017-01 ┆ ANG MO KIO ┆ 3 ROOM    ┆ 108   ┆ … ┆ New Generation ┆ 1978                ┆ 60 years 07 months ┆ 250000.0     │
│ 2017-01 ┆ ANG MO KIO ┆ 3 ROOM    ┆ 602   ┆ … ┆ New Generation ┆ 1980                ┆ 62 years 05 months ┆ 262000.0     │
│ 2017-01 ┆ ANG MO KIO ┆ 3 ROOM    ┆ 465   ┆ … ┆ New Generation ┆ 1980                ┆ 62 years 01 month  ┆ 265000.0     │
│ …       ┆ …          ┆ …         ┆ …     ┆ … ┆ …              ┆ …                   ┆ …                  ┆ …            │
│ 2023-04 ┆ YISHUN     ┆ EXECUTIVE ┆ 258   ┆ … ┆ Maisonette     ┆ 1985                ┆ 61 years 02 months ┆ 808000.0     │
│ 2023-04 ┆ YISHUN     ┆ EXECUTIVE ┆ 293   ┆ … ┆ Apartment      ┆ 1992                ┆ 68 years 04 months ┆ 892000.0     │
│ 2023-04 ┆ YISHUN     ┆ EXECUTIVE ┆ 723   ┆ … ┆ Apartment      ┆ 1986                ┆ 62 years 02 months ┆ 780000.0     │
│ 2023-04 ┆ YISHUN     ┆ EXECUTIVE ┆ 828   ┆ … ┆ Apartment      ┆ 1988                ┆ 63 years 10 months ┆ 865000.0     │
└─────────┴────────────┴───────────┴───────┴───┴────────────────┴─────────────────────┴────────────────────┴──────────────┘
```

### Ask OpenAI to generate code for a question
```python
In [1]: from govtech_data.utils.openai import OpenAIClient

In [2]: govtech_openai_client = OpenAIClient()

In [3]: govtech_openai_client.query("get average resale flat prices in bedok for different flat-types in a dataframe")
2023-04-18 01:25:17.135 | DEBUG    | govtech_data.utils.openai:query:56 - Request:
{'role': 'user', 'content': 'get average resale flat prices in bedok for different flat-types in a dataframe'}
2023-04-18 01:25:17.270 | WARNING  | govtech_data.utils.openai:num_tokens_from_messages:192 - Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.
2023-04-18 01:25:17.271 | DEBUG    | govtech_data.utils.openai:simple_query_openai:233 - Total number of tokens in messages: 603
2023-04-18 01:25:33.830 | DEBUG    | govtech_data.utils.openai:query:70 - ChatGPT content response:
{'thoughts': {'text': 'I need to get the dataset id that contains resale flat prices in Bedok and then extract the required information using pandas.', 'reasoning': "I will need to query the dataset using 'dataset_search' and 'get_dataset' commands to get the dataset id and then use 'get_all_distinct_values_in_a_dataset_field' to get the different flat types available in the dataset. I can then filter the dataset using pandas to get the average resale flat prices for each flat type in Bedok.", 'plan': ["Search for dataset containing resale flat prices in Bedok using 'dataset_search' command", "Extract dataset id using 'get_dataset' command", "Get all distinct flat types in the dataset using 'get_all_distinct_values_in_a_dataset_field' command", 'Filter dataset using pandas to get average resale flat prices for each flat type in Bedok'], 'criticism': 'I need to ensure that I am using the correct dataset and field names to get the required information.', 'speak': "I will use 'dataset_search', 'get_dataset' and 'get_all_distinct_values_in_a_dataset_field' commands to extract the required information."}, 'command': {'name': 'dataset_search', 'args': {'input': 'resale flat prices bedok'}}}
2023-04-18 01:25:33.833 | DEBUG    | govtech_data.client:get_model_from_json_response:109 - endpoint: https://data.gov.sg/api/action/package_list
2023-04-18 01:25:35.197 | DEBUG    | govtech_data.utils.openai:query:56 - Request:
{'role': 'user', 'content': 'Datasets found for resale flat prices bedok: [{"id":"resale-flat-prices","score":95},{"id":"age-of-hdb-population-by-ethnic-group-and-flat-type-in-age-groups","score":86},{"id":"average-and-median-size-of-hdb-households-by-ethnic-group-and-flat-type","score":86},{"id":"average-number-of-income-earners-of-hdb-households-by-ethnic-group-and-flat-type","score":86},{"id":"average-retail-prices-of-selected-consumer-items-monthly","score":86},{"id":"average-retail-prices-of-selected-items-annual","score":86},{"id":"changes-in-value-added-per-worker-at-current-market-prices-by-industry-ssic-2015-quarterly","score":86},{"id":"compensation-of-employees-by-industry-at-current-prices-annual","score":86},{"id":"construction-material-market-prices-monthly","score":86},{"id":"dependency-ratio-of-hdb-resident-population-by-ethnic-group-and-flat-type","score":86}]'}
2023-04-18 01:25:35.197 | WARNING  | govtech_data.utils.openai:num_tokens_from_messages:192 - Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.
2023-04-18 01:25:35.198 | DEBUG    | govtech_data.utils.openai:simple_query_openai:233 - Total number of tokens in messages: 1082
2023-04-18 01:25:53.001 | DEBUG    | govtech_data.utils.openai:query:70 - ChatGPT content response:
{'thoughts': {'text': "From the search results, we can see that the first dataset 'resale-flat-prices' is the dataset we need. I will now extract the dataset id using 'get_dataset' command and then use 'get_dataset_schema' command to get the schema of the dataset and extract the required field names.", 'reasoning': "I will need the schema of the dataset to get the field names for flat type and town. Once I have the field names, I can then use 'get_all_distinct_values_in_a_dataset_field' command to get the different flat types available in the dataset and then filter the dataset using pandas to get the average resale flat prices for each flat type in Bedok.", 'plan': ["Extract dataset id for 'resale-flat-prices' using 'get_dataset' command", "Get the schema of the dataset using 'get_dataset_schema' command to get the required field names", "Use 'get_all_distinct_values_in_a_dataset_field' command to get the different flat types available in the dataset", 'Filter dataset using pandas to get average resale flat prices for each flat type in Bedok'], 'criticism': 'I need to ensure that I am using the correct field names and values to extract the required information.', 'speak': "I will use 'get_dataset' and 'get_dataset_schema' commands to extract the required field names and 'get_all_distinct_values_in_a_dataset_field' command to get the different flat types available in the dataset."}, 'command': {'name': 'get_dataset', 'args': {'id': 'resale-flat-prices'}}}
2023-04-18 01:25:53.003 | DEBUG    | govtech_data.client:get_model_from_json_response:109 - endpoint: https://data.gov.sg/api/action/package_show
2023-04-18 01:25:53.972 | DEBUG    | govtech_data.utils.content:fetch_url:11 - Fetching url - https://storage.data.gov.sg/resale-flat-prices/resources/resale-flat-prices-based-on-registration-date-from-jan-2017-onwards-2023-04-17T03-28-08Z.csv
2023-04-18 01:25:56.195 | DEBUG    | govtech_data.utils.openai:query:56 - Request:
{'role': 'user', 'content': "Schema for resale-flat-prices: {'month': Utf8, 'town': Utf8, 'flat_type': Utf8, 'block': Utf8, 'street_name': Utf8, 'storey_range': Utf8, 'floor_area_sqm': Float64, 'flat_model': Utf8, 'lease_commence_date': Int64, 'remaining_lease': Utf8, 'resale_price': Float64}"}
2023-04-18 01:25:56.195 | WARNING  | govtech_data.utils.openai:num_tokens_from_messages:192 - Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.
2023-04-18 01:25:56.197 | DEBUG    | govtech_data.utils.openai:simple_query_openai:233 - Total number of tokens in messages: 1495
2023-04-18 01:26:10.913 | DEBUG    | govtech_data.utils.openai:query:70 - ChatGPT content response:
{'thoughts': {'text': "The schema shows that the required field names are 'flat_type', 'town' and 'resale_price'. I can now use 'get_all_distinct_values_in_a_dataset_field' command to get the different flat types available in the dataset and then filter the dataset using pandas to get the average resale flat prices for each flat type in Bedok.", 'reasoning': "I will extract the different flat types available in the dataset using 'get_all_distinct_values_in_a_dataset_field' command and then filter the dataset using pandas to get the average resale flat prices for each flat type in Bedok.", 'plan': ["Use 'get_all_distinct_values_in_a_dataset_field' command to get the different flat types available in the dataset", 'Filter dataset using pandas to get average resale flat prices for each flat type in Bedok'], 'criticism': 'I need to ensure that I am filtering the data based on the correct town name, i.e. Bedok.', 'speak': "I will now use 'get_all_distinct_values_in_a_dataset_field' command to get the different flat types and then filter the dataset using pandas."}, 'command': {'name': 'get_all_distinct_values_in_a_dataset_field', 'args': {'id': 'resale-flat-prices', 'field': 'flat_type'}}}
2023-04-18 01:26:10.963 | DEBUG    | govtech_data.utils.openai:query:56 - Request:
{'role': 'user', 'content': 'All distinct values in flat_type: ["3 ROOM","4 ROOM","5 ROOM","2 ROOM","EXECUTIVE","1 ROOM","MULTI-GENERATION"]'}
2023-04-18 01:26:10.963 | WARNING  | govtech_data.utils.openai:num_tokens_from_messages:192 - Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.
2023-04-18 01:26:10.965 | DEBUG    | govtech_data.utils.openai:simple_query_openai:233 - Total number of tokens in messages: 1797
2023-04-18 01:26:26.786 | DEBUG    | govtech_data.utils.openai:query:70 - ChatGPT content response:
{'thoughts': {'text': 'Now that we have the different flat types available in the dataset, I will filter the dataset using pandas to get the average resale flat prices for each flat type in Bedok.', 'reasoning': 'I will first filter the dataset to only include transactions in Bedok using pandas. Then, I will group the data by flat type and calculate the average resale price for each flat type.', 'plan': ['Filter dataset to only include transactions in Bedok using pandas', 'Group the data by flat type and calculate the average resale price for each flat type'], 'criticism': 'I need to ensure that I am correctly calculating the average resale flat prices for each flat type.', 'speak': 'I will now filter the dataset using pandas to get the average resale flat prices for each flat type in Bedok.'}, 'command': {'name': 'evaluate_full_code', 'args': {'code': "import matplotlib.pyplot as plt\nfrom govtech_data import GovTechClient\nimport pandas as pd\n\ndataset_id = 'resale-flat-prices'\ndataset_df = GovTechClient.fetch_dataframe_from_package(dataset_id).to_pandas()\n\nbedok_df = dataset_df[dataset_df['town'] == 'BEDOK']\nflat_type_grouped = bedok_df.groupby(['flat_type'])\naverage_prices = flat_type_grouped['resale_price'].mean().reset_index()\n\nprint(average_prices)"}}}
Out[3]: True

In [4]: print(govtech_openai_client.get_generated_code_from_history())
import matplotlib.pyplot as plt
from govtech_data import GovTechClient
import pandas as pd

dataset_id = 'resale-flat-prices'
dataset_df = GovTechClient.fetch_dataframe_from_package(dataset_id).to_pandas()

bedok_df = dataset_df[dataset_df['town'] == 'BEDOK']
flat_type_grouped = bedok_df.groupby(['flat_type'])
average_prices = flat_type_grouped['resale_price'].mean().reset_index()

print(average_prices)

In [5]: exec(govtech_openai_client.get_generated_code_from_history())
   flat_type   resale_price
0     2 ROOM  234414.740385
1     3 ROOM  315348.718331
2     4 ROOM  465674.532707
3     5 ROOM  606324.855910
4  EXECUTIVE  759893.882775
```

### Ask OpenAI to generate a trend graph for average resale flat prices
![Test123](img/example.png)

## Credits

This library adopts some ideas from the [Auto-GPT](https://github.com/Significant-Gravitas/Auto-GPT) project to perform Chain-of-Thought reasoning.
