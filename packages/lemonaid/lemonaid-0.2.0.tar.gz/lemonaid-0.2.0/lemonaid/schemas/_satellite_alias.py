from datetime import datetime
from uuid import UUID

from pydantic import field_serializer, field_validator

from lemonaid.schemas._citra_base_model import CitraBaseModel
from lemonaid.schemas.normalization import normalize_datetime, serialize_datetime


class SatelliteAlias(CitraBaseModel):

    id: UUID
    creation_epoch: datetime
    provider_alias_epoch: datetime
    satellite_id: UUID
    provider_satellite_name: str | None = None
    provider: str
    provider_satellite_id: str

    @field_validator("provider_alias_epoch", "creation_epoch")
    def validate_required_epochs(cls, v: datetime) -> datetime:
        return normalize_datetime(v)

    @field_serializer("provider_alias_epoch", "creation_epoch")
    def serialize_required_epochs(self, v: datetime) -> str:
        return serialize_datetime(v)

    @field_serializer("id", "satellite_id")
    def serialize_id(self, v: UUID) -> str:
        return str(v)
