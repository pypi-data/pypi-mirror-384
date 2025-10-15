import urllib.parse

import requests

BASE_TINY_URL = "https://tinyurl.com/api-create.php"


def shorten_url(url: str) -> str:
    encoded_url = urllib.parse.urlencode({"url": url})
    full_url = f"{BASE_TINY_URL}?{encoded_url}"
    res = requests.get(full_url, timeout=5)
    res.raise_for_status()  # Raises HTTPError for non-200 codes
    return res.text
