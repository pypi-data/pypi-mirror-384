from .weather_icon_enum import WeatherIconEnum
from .precipitation import Precipitation
from .wind import Wind
from .uv_index import UVIndex
from typing import Optional
class HourlyPredictions:

    def __init__(
            self,
            title: str,
            temperature: str,
            icon: WeatherIconEnum,
            summary: str,
            precipitation: Optional[Precipitation],
            wind: Optional[Wind] = None,
            feels_like: str = None,
            humidity: str = None,
            uv_index: Optional[UVIndex] = None,
            cloud_cover: str = None
        ):
        self._title = title
        self._temperature = temperature
        self._icon = icon
        self._summary = summary
        self._precipitation = precipitation
        self._wind = wind
        self._feels_like = feels_like
        self._humidity = humidity
        self._uv_index = uv_index
        self._cloud_cover = cloud_cover

    @property
    def title(self) -> str:
        return self._title

    @property
    def temperature(self) -> str:
        return self._temperature

    @property
    def icon(self) -> WeatherIconEnum:
        return self._icon

    @property
    def summary(self) -> str:
        return self._summary

    @property
    def precipitation(self) -> Optional[Precipitation]:
        return self._precipitation

    @property
    def wind(self) -> Optional[Wind]:
        return self._wind

    @property
    def feels_like(self) -> str:
        return self._feels_like

    @property
    def humidity(self) -> str:
        return self._humidity

    @property
    def uv_index(self) -> Optional[UVIndex]:
        return self._uv_index

    @property
    def cloud_cover(self) -> str:
        return self._cloud_cover

    def __repr__(self):
        return (f"HourlyPredictions(title={self._title!r}, temperature={self._temperature!r}, icon={self._icon!r}, "
                f"summary={self._summary!r}, precipitation={self._precipitation!r}, wind={self._wind!r}, "
                f"feels_like={self._feels_like!r}, humidity={self._humidity!r}, uv_index={self._uv_index!r}, "
                f"cloud_cover={self._cloud_cover!r})")