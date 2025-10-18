import requests  # type: ignore

from lemonaid.schemas import ElsetReadList
from lemonaid.settings import CITRA_CLIENT_SETTINGS


class _CitraElsetClient:
    @staticmethod
    def latest() -> ElsetReadList:
        url = f"{CITRA_CLIENT_SETTINGS.url}/elsets/latest"
        headers = CITRA_CLIENT_SETTINGS.authorization_header
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return ElsetReadList.model_validate(response.json())
