from datetime import datetime
from uuid import UUID

from pydantic import RootModel

from lemonaid.enums import CitraElsetType
from lemonaid.schemas._citra_base_model import CitraBaseModel


class ElsetRead(CitraBaseModel):

    id: UUID
    creation_epoch: datetime
    epoch: datetime
    type: CitraElsetType
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


class ElsetReadList(RootModel[list[ElsetRead]]):
    pass
