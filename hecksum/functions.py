import requests


def get_raised(url: str) -> requests.Response:
    r = requests.get(url)
    r.raise_for_status()
    return r
