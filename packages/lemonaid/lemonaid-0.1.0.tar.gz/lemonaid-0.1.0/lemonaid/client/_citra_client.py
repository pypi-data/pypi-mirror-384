from pydantic import SecretStr

from lemonaid.client._citra_elset_client import _CitraElsetClient
from lemonaid.enums import CitraEnvironment
from lemonaid.settings import CITRA_CLIENT_SETTINGS


class CitraClient:
    def __init__(self, token: str | None = None, environment: CitraEnvironment | None = None):
        if token:
            CITRA_CLIENT_SETTINGS.token = SecretStr(token)
        if environment:
            CITRA_CLIENT_SETTINGS.environment = environment

    elsets = _CitraElsetClient
