import time

from typing import Union

import pandas as pd
import shapely

from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from pydantic import SecretStr, BaseModel, computed_field, field_validator, PrivateAttr

class AccesToken(BaseModel):
    access_token: SecretStr
    expires_in: int
    token_type: str
    _now: int = PrivateAttr(default_factory=time.time)

    @field_validator('token_type')
    @classmethod
    def token_must_be_bearer(cls, v: str) -> str:
        if v.lower() != 'bearer':
            raise ValueError('token type must be bearer')
        return v.title()

    @computed_field
    @property
    def expires_at(self) -> int:
        return self._now + self.expires_in

class TimeRange:
    """"Class for time range represented by two dates.

    Args:
        start_time (Union[str, pd.Timestamp]): Start date.
        end_time (Union[str, pd.Timestamp]): End date.
    """

    def __init__(self,
                 start_time: Union[str, pd.Timestamp],
                 end_time: Union[str, pd.Timestamp]):

        start_time = self.convert_time(start_time)
        end_time = self.convert_time(end_time)

        if start_time > end_time:
            raise ValueError("start_time must be smaller or equal to end_time")

        self._start_time = start_time
        self._end_time = end_time

    def __repr__(self):
        obj_name = f'<ddc_utility.{type(self).__name__}>'
        rep = f"{obj_name}\nstart_time: {self.start_time}\nend_time: {self.end_time}\n"
        return rep

    @property
    def time_range(self):
        """Return time range."""
        return [self._start_time, self._end_time]

    @property
    def start_time(self):
        """Return start time."""
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        """Set start time."""
        start_time = self.convert_time(value)
        if start_time <= self._end_time:
            self._start_time = start_time
        else:
            raise ValueError('start_time must be smaller or '
                             'equal to end_time')

    @property
    def end_time(self):
        """Return end time."""
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        """Set start time."""
        end_time = self.convert_time(value)
        if end_time >= self._start_time:
            self._end_time = end_time
        else:
            raise ValueError('end_time must be greater or '
                             'equal to start_time')

    def to_string(self, only_date=True):
        """Return custom string representation of the time range.

        Args:
            only_date (bool): Wheter to return only the date part of time range.
                Defaults to True.
        """
        if only_date:
            return [self._start_time.isoformat(sep='T').split('T')[0],
                    self._end_time.isoformat(sep='T').split('T')[0]]

        return [self._start_time.isoformat(sep='T'),
                self._end_time.isoformat(sep='T')]

    def convert_to_full_months(self):
        """
        Convert date to full months.
        For example, in the case of start time '2021-01-04' to '2021-01-01' or
        in the case of end time '2021-05-15' to '2021-05-31'.
        """
        self._start_time = self._start_time.replace(day=1)
        self._end_time = (self._end_time if self._end_time.is_month_end
                          else self._end_time + pd.offsets.MonthEnd())

    @classmethod
    def convert_time(cls,
                     datetime: Union[str, pd.Timestamp],
                     utc: bool = False):
        """Convert time to pandas Timestamp."""
        try:
            return pd.to_datetime(datetime, utc=utc)
        except Exception as error:
            raise ValueError(
                "Invalid input parameters -- must be convertable to pandas.TimeStamp") from error


class Geometry:
    """Class for WKT/GeoJson type geometry.

        Args:
            geometry (Union[str, dict, Polygon, MultiPolygon]): Geometry.
    """

    def __init__(self,
                 geometry: Union[str, dict, Polygon, MultiPolygon]):

        if not isinstance(geometry, (Polygon, MultiPolygon)):
            geometry = self.convert_geometry(geometry)

        if not geometry.is_valid:
            raise ValueError(
                "Invalid geometry -- must be valid based on shapely's definition")

        self._geometry = geometry

    def __repr__(self):
        obj_name = f'<ddc_utility.{type(self).__name__}>'
        rep = f"{obj_name}\ngeometry: {self._geometry}\n"
        return rep

    @property
    def geometry(self):
        """Return geometry."""
        return self._geometry

    def to_string(self):
        """Return WKT string representation of the geometry."""
        return self._geometry.wkt
    
    def to_json(self):
        """Return GeoJson representation of the geometry."""
        return shapely.geometry.mapping(self._geometry)

    @classmethod
    def convert_geometry(cls,
                         geometry: str | dict):
        """Convert geometry to Shapely object."""
        try:
            if isinstance(geometry, dict):
                geometry = shapely.geometry.shape(geometry)
                # geometry = MultiPolygon(shapely.from_geojson(geometry))
            else:
                geometry = shapely.from_wkt(geometry)
        except Exception as error:
            raise ValueError(
                "Invalid input parameters -- must be convertable to Shapely.geometry") from error

        if geometry.geom_type not in ['Polygon', 'MultiPolygon']:
            raise ValueError(
                "Invalid geometry type -- must be Polygon or MultiPolygon")

        return geometry


class IrrigationSchedule:
    """"Class for defining irrigation schedule.

        Args:
            date (Union[str, pd.Timestamp]): Irrigation date.
            amount (float): Amount of irrigated water in mm.
    """

    def __init__(self, date: Union[str, pd.Timestamp], amount: float):

        try:
            date = pd.to_datetime(date)
        except Exception as error:
            raise ValueError(
                "Invalid input parameters -- 'date' must be convertable to pandas.TimeStamp") from error

        try:
            amount = float(amount)
        except ValueError as error:
            raise ValueError(
                "Invalid input parameters -- 'amount must be convertable to float") from error

        self._date = pd.to_datetime(date)
        self._amount = float(amount)

    def __repr__(self):
        obj_name = f'<ddc_utility.{type(self).__name__}>'
        rep = f"{obj_name}\ndate: {self._date}\namount: {self._amount}\n"
        return rep

    @property
    def date(self):
        """Return geometry."""
        return self._date

    @property
    def amount(self):
        """Return geometry."""
        return self._amount

    def to_string(self, only_date=True):
        """Return the tuple string representation of the object."""
        if only_date:
            return (self._date.isoformat(sep='T').split('T')[0], self._amount)
        else:
            return (self._date.isoformat(sep='T'), self._amount)
