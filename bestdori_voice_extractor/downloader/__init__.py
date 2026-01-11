import json

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from bestdori_voice_extractor.config import BESTDORI_INFO_URL, MAX_WORKERS, PROXY

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 500, 502, 503, 504 ])
adapter = HTTPAdapter(max_retries=retries, pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS)
session.mount('http://', adapter)
session.mount('https://', adapter)
session.proxies.update(PROXY)


def load(url: str):
    response = session.get(url, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Failed to load {url}: {response.status_code}")
    return json.loads(response.text)

bestdori_info = load(BESTDORI_INFO_URL)