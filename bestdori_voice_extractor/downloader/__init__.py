import json

import requests

from bestdori_voice_extractor.config import BESTDORI_INFO_URL, PROXY


def load(url: str):
    response = requests.get(url, proxies=PROXY)
    if response.status_code != 200:
        raise Exception(f"Failed to load {url}: {response.status_code}")
    return json.loads(response.text)

bestdori_info = load(BESTDORI_INFO_URL)