import os
from typing import Any, Dict, List, Union

import requests


def get_resp(url: str) -> requests.Response:
    req = requests.Request("GET", url).prepare()
    s = requests.Session()
    resp = s.send(req)
    assert resp.status_code == 200, f"Error: {resp.status_code}"
    return resp


def download_json(url: str) -> Union[List[Any], Dict[str, Any]]:
    return get_resp(url).json()


def download_file(url: str, file: str) -> None:
    base = os.path.split(file)[0]
    os.makedirs(base, exist_ok=True)

    resp = get_resp(url)
    with open(file, "wb") as f:
        f.write(resp.content)
