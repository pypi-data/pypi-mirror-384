from uuid import UUID

from lemonaid.client._requests import _make_get_request
from lemonaid.schemas import GroundStationRead


class _CitraGroundStationClient:
    @staticmethod
    def read(station_id: UUID) -> GroundStationRead | None:
        response = _make_get_request(f"ground-stations/{station_id}")
        if response.status_code != 200:
            return None
        return GroundStationRead.model_validate(response.json())
