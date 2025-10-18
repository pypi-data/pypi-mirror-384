from sqlalchemy import Column, Identity, ForeignKey, Integer, DateTime, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Optional, Union
from datetime import datetime
import pytz
from pandas import to_datetime

from sunpeek.components.helpers import ORMBase
from sunpeek.common.errors import ConfigurationError, TimeZoneError


def _validate_tz_aware(dt: datetime, name: str):
    """Ensure datetime is timezone-aware."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ConfigurationError(f"Event {name} must be timezone-aware.")


def _validate_tz_match(dt: datetime, tz_name: Optional[str]):
    """Ensure the datetime's timezone matches the provided one."""
    if dt.tzinfo and tz_name:
        target_zone = pytz.timezone(tz_name)
        expected_offset = target_zone.utcoffset(dt.replace(tzinfo=None))
        if dt.utcoffset() != expected_offset:
            raise TimeZoneError("Datetime timezone doesn't match specified timezone.")


class OperationalEvent(ORMBase):
    __tablename__ = 'operational_events'

    id = Column(Integer, Identity(0), primary_key=True)
    plant_id = Column(Integer, ForeignKey('plant.id', ondelete="CASCADE"))
    plant = relationship("Plant", back_populates="operational_events")
    _event_start = Column(DateTime)
    _event_end = Column(DateTime)
    timezone = Column(String)
    ignored_range = Column(Boolean, default=False)
    description = Column(String)

    def __init__(
        self,
        plant,
        event_start: Union[str, datetime],
        event_end: Optional[Union[str, datetime]] = None,
        timezone: Optional[str] = None,
        description: Optional[str] = None,
        ignored_range: bool = False
    ):
        self.plant = plant
        self.timezone = timezone
        self.description = description
        self.ignored_range = ignored_range

        self.set_start(event_start, timezone)
        if event_end:
            self.set_end(event_end, timezone)

    def _get_event_start(self) -> Optional[datetime]:
        return pytz.utc.localize(self._event_start) if self._event_start else None

    def _set_event_start(self, val: datetime):
        _validate_tz_aware(val, "start")
        utc_val = val.astimezone(pytz.utc).replace(tzinfo=None)
        if self._event_end and utc_val > self._event_end:
            raise ConfigurationError("Event end must be after start.")
        self._event_start = utc_val

    @hybrid_property
    def event_start(self) -> Optional[datetime]:
        return self._get_event_start()

    @event_start.setter
    def event_start(self, value: datetime):
        self._set_event_start(value)

    @event_start.expression
    def event_start(cls):
        return cls._event_start

    # @classmethod
    # def _expr_event_start(cls):
    #     return cls._event_start
    #
    # event_start = hybrid_property(_get_event_start, _set_event_start).expression(_expr_event_start)

    def _get_event_end(self) -> Optional[datetime]:
        return pytz.utc.localize(self._event_end) if self._event_end else None

    def _set_event_end(self, val: Optional[datetime]):
        if val is None:
            self._event_end = None
            return
        _validate_tz_aware(val, "end")
        utc_val = val.astimezone(pytz.utc).replace(tzinfo=None)
        if self._event_start and utc_val < self._event_start:
            raise ConfigurationError("Event end must be after start.")
        self._event_end = utc_val

    @hybrid_property
    def event_end(self) -> Optional[datetime]:
        return self._get_event_end()

    @event_end.setter
    def event_end(self, val: Optional[datetime]):
        self._set_event_end(val)

    @event_end.expression
    def event_end(cls):
        return cls._event_end

    # @classmethod
    # def _expr_event_end(cls):
    #     return cls._event_end
    #
    # event_end = hybrid_property(_get_event_end, _set_event_end).expression(_expr_event_end)

    def set_start(self, val: Union[str, datetime], timezone: Optional[str] = None):
        if val is None:
            raise ConfigurationError("Missing event_start value.")
        dt = to_datetime(val).to_pydatetime()
        tz_used = timezone or self.timezone
        _validate_tz_match(dt, tz_used)
        if dt.tzinfo is None:
            if not tz_used:
                raise ConfigurationError("Naive datetime requires timezone argument.")
            dt = pytz.timezone(tz_used).localize(dt)
        self.event_start = dt

    def set_end(self, val: Union[str, datetime], timezone: Optional[str] = None):
        if val is None:
            self._event_end = None
            return
        dt = to_datetime(val).to_pydatetime()
        tz_used = timezone or self.timezone
        _validate_tz_match(dt, tz_used)
        if dt.tzinfo is None:
            if not tz_used:
                raise ConfigurationError("Naive datetime requires timezone argument.")
            dt = pytz.timezone(tz_used).localize(dt)
        self.event_end = dt

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'plant_id': self.plant_id,
            'event_start': self.event_start.isoformat() if self.event_start else None,
            'event_end': self.event_end.isoformat() if self.event_end else None,
            'timezone': self.timezone,
            'description': self.description,
            'ignored_range': self.ignored_range,
        }
