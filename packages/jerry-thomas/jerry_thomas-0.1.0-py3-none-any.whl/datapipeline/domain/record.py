from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass
class Record:
    pass


@dataclass
class TemporalRecord(Record):
    """Canonical time-series payload used throughout the pipeline."""

    time: datetime
    value: Any

    def __post_init__(self) -> None:
        if self.time.tzinfo is None:
            raise ValueError("time must be timezone-aware")
        self.time = self.time.astimezone(timezone.utc)

    def _identity_fields(self) -> dict:
        """Return a mapping of domain fields excluding 'time' and 'value'."""
        data = asdict(self)
        data.pop("time", None)
        data.pop("value", None)
        return data
