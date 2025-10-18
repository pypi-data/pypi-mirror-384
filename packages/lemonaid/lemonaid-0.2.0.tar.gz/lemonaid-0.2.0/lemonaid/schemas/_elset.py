from datetime import datetime
from uuid import UUID

from keplemon.bodies import Constellation, Satellite
from keplemon.elements import KeplerianElements, KeplerianState
from keplemon.enums import KeplerianType, ReferenceFrame, TimeSystem
from keplemon.propagation import ForceProperties, b_star_to_drag_coefficient
from keplemon.time import Epoch
from pydantic import field_serializer, field_validator

from lemonaid.enums import CitraElsetType
from lemonaid.schemas._citra_base_model import CitraBaseModel, CitraBaseModelList
from lemonaid.schemas._satellite_alias import SatelliteAlias
from lemonaid.schemas.normalization import normalize_datetime, serialize_datetime


class ElsetRead(CitraBaseModel):

    id: UUID
    creation_epoch: datetime
    epoch: datetime
    type: CitraElsetType
    satellite_alias: SatelliteAlias
    semi_major_axis: float
    inclination: float
    raan: float
    eccentricity: float
    argument_of_perigee: float
    mean_anomaly: float
    mean_motion_dot: float = 0.0
    mean_motion_dot_dot: float = 0.0
    b_star: float = 0.0
    ballistic_coefficient: float = 0.0
    srp_coefficient: float = 0.0
    rms: float | None = None

    @field_validator("epoch", "creation_epoch")
    def validate_required_epochs(cls, v: datetime) -> datetime:
        return normalize_datetime(v)

    @field_serializer("epoch", "creation_epoch")
    def serialize_required_epochs(self, v: datetime) -> str:
        return serialize_datetime(v)

    @field_serializer("id")
    def serialize_id(self, v: UUID) -> str:
        return str(v)

    def to_keplemon_satellite(self) -> Satellite:
        sat = Satellite()
        sat.id = str(self.satellite_alias.satellite_id)
        if self.satellite_alias.provider == "18th SPCS":
            sat.norad_id = int(self.satellite_alias.provider_satellite_id)
        elements = KeplerianElements(
            semi_major_axis=self.semi_major_axis,
            eccentricity=self.eccentricity,
            inclination=self.inclination,
            raan=self.raan,
            argument_of_perigee=self.argument_of_perigee,
            mean_anomaly=self.mean_anomaly,
        )
        epoch = Epoch.from_iso(serialize_datetime(self.epoch), TimeSystem.UTC)
        if self.type == CitraElsetType.MEAN_BROUWER_GP or self.type == CitraElsetType.MEAN_BROUWER_GP.value:
            elements_type = KeplerianType.MeanBrouwerGP
        elif self.type == CitraElsetType.MEAN_BROUWER_XP or self.type == CitraElsetType.MEAN_BROUWER_XP.value:
            elements_type = KeplerianType.MeanBrouwerXP
        elif self.type == CitraElsetType.MEAN_KOZAI_GP or self.type == CitraElsetType.MEAN_KOZAI_GP.value:
            elements_type = KeplerianType.MeanKozaiGP
        else:
            elements_type = KeplerianType.Osculating

        gp_types = {
            CitraElsetType.MEAN_BROUWER_GP,
            CitraElsetType.MEAN_BROUWER_GP.value,
            CitraElsetType.MEAN_KOZAI_GP,
            CitraElsetType.MEAN_KOZAI_GP.value,
        }

        if self.type in gp_types:
            drag_coefficient = b_star_to_drag_coefficient(self.b_star)
        else:
            drag_coefficient = self.ballistic_coefficient
        sat.force_properties = ForceProperties(
            self.srp_coefficient,
            1.0,
            drag_coefficient,
            1.0,
            1.0,
            self.mean_motion_dot,
            self.mean_motion_dot_dot,
        )
        sat.keplerian_state = KeplerianState(epoch, elements, ReferenceFrame.TEME, elements_type)
        sat.name = self.satellite_alias.provider_satellite_name

        return sat


class ElsetReadList(CitraBaseModelList[ElsetRead]):
    def to_keplemon_constellation(self) -> Constellation:
        constellation = Constellation()
        for elset in self.root:
            constellation[str(elset.satellite_alias.satellite_id)] = elset.to_keplemon_satellite()
        return constellation
