from io import StringIO
import requests
from loguru import logger


def fetch_url(
    url: str, params: dict = None, requests_session: requests.Session = None
) -> requests.Response:
    use_session = requests.Session() if requests_session is None else requests_session
    logger.debug(f"Fetching url - {url}")
    return use_session.get(url, params=params, timeout=30)


def convert_response_to_io(response: requests.Response) -> StringIO:
    return StringIO(response.content.decode("utf-8"))
