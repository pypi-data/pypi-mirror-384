from datetime import datetime
from uuid import UUID

from keplemon.bodies import Observatory
from pydantic import field_serializer, field_validator

from lemonaid.schemas._citra_base_model import CitraBaseModel, CitraBaseModelList
from lemonaid.schemas.normalization import normalize_datetime, serialize_datetime


class GroundStationRead(CitraBaseModel):

    id: UUID
    user_id: UUID
    group_id: UUID | None = None
    creation_epoch: datetime
    update_epoch: datetime
    name: str
    latitude: float
    longitude: float
    altitude: float

    @field_validator("creation_epoch", "update_epoch")
    def validate_required_epochs(cls, v: datetime) -> datetime:
        return normalize_datetime(v)

    @field_serializer("creation_epoch", "update_epoch")
    def serialize_required_epochs(self, v: datetime) -> str:
        return serialize_datetime(v)

    @field_serializer("id", "user_id", "group_id")
    def serialize_id(self, v: UUID) -> str:
        return str(v)

    def to_keplemon_observatory(self) -> Observatory:
        site = Observatory(self.latitude, self.longitude, self.altitude * 1e-3)
        site.id = str(self.id)
        site.name = self.name
        return site


class GroundStationReadList(CitraBaseModelList[GroundStationRead]):
    pass
