import hashlib

import requests


def get_raised(url: str) -> requests.Response:
    r = requests.get(url)
    r.raise_for_status()
    return r


def create_download_checksum(url: str, algorithm: str) -> str:
    # Todo: convert to streaming
    h = hashlib.new(algorithm)
    r = get_raised(url)
    h.update(r.content)
    checksum = h.hexdigest()
    return checksum
