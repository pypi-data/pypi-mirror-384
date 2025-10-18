import requests  # type: ignore

from lemonaid.settings import CITRA_CLIENT_SETTINGS


def _make_get_request(path: str) -> requests.Response:

    if not path.startswith("/"):
        path = f"/{path}"

    url = f"{CITRA_CLIENT_SETTINGS.url}{path}"
    headers = CITRA_CLIENT_SETTINGS.authorization_header
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response
