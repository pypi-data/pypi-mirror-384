from lemonaid.client._requests import _make_get_request
from lemonaid.schemas import ElsetReadList


class _CitraElsetClient:
    @staticmethod
    def latest() -> ElsetReadList:
        response = _make_get_request("elsets/latest")
        return ElsetReadList.model_validate(response.json())
