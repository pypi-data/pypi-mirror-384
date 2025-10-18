from datetime import datetime, timezone


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc)
    else:
        value = value.replace(tzinfo=timezone.utc)
    return value


def serialize_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
