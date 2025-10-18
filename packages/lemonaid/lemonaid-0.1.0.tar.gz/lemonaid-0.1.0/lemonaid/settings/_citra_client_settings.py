from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from lemonaid.enums import CitraEnvironment


class CitraClientSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CITRA_",
        case_sensitive=False,
    )
    token: SecretStr = SecretStr("")
    environment: CitraEnvironment = CitraEnvironment.PRODUCTION
    base_url: str = "api.citra.space"

    @property
    def url(self) -> str:
        env_prefix = ""
        if self.environment == CitraEnvironment.DEVELOPMENT:
            env_prefix = "dev."
        return f"https://{env_prefix}{self.base_url}"  # noqa: E231

    @property
    def authorization_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token.get_secret_value()}"}
