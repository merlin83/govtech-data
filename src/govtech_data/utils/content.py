from functools import lru_cache
from io import StringIO

import requests
from loguru import logger


@lru_cache(maxsize=128)
def fetch_url(url: str, params: dict = None) -> requests.Response:
    use_session = requests.Session()
    logger.debug(f"Fetching url - {url}")
    return use_session.get(url, params=params, timeout=30)


def convert_response_to_io(response: requests.Response) -> StringIO:
    return StringIO(response.content.decode("utf-8"))
