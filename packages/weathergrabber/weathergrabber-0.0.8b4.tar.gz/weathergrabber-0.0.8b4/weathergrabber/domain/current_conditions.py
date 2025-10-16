from .city_location import CityLocation
from .timestamp import Timestamp
from .weather_icon_enum import WeatherIconEnum
from .day_night import DayNight
from typing import Optional

class CurrentConditions:
    def __init__(
        self,
        location: Optional[CityLocation],
        timestamp: Optional[Timestamp],
        temperature: str,
        icon: Optional[WeatherIconEnum],
        summary: str,
        day_night: Optional[DayNight]
    ):
        self._location = location
        self._timestamp = timestamp
        self._temperature = temperature
        self._icon = icon
        self._summary = summary
        self._day_night = day_night

    @property
    def location(self) -> Optional[CityLocation]:
        return self._location

    @property
    def timestamp(self) -> Optional[Timestamp]:
        return self._timestamp

    @property
    def temperature(self) -> str:
        return self._temperature

    @property
    def icon(self) -> Optional[WeatherIconEnum]:
        return self._icon

    @property
    def summary(self) -> str:
        return self._summary

    @property
    def day_night(self) -> Optional[DayNight]:
        return self._day_night

    def __repr__(self):
        return (
            f"CurrentConditions(location={self._location!r}, timestamp={self._timestamp!r}, "
            f"temperature={self._temperature!r}, icon={self._icon!r}, summary={self._summary!r}, "
            f"day_night={self._day_night!r})"
        )
