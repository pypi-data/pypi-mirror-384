from .temperature_hight_low import TemperatureHighLow
from .weather_icon_enum import WeatherIconEnum
from .moon_phase import MoonPhase
from .precipitation import Precipitation
from typing import Optional

class DailyPredictions:
    def __init__(
        self,
        title: str,
        high_low: Optional[TemperatureHighLow],
        icon: Optional[WeatherIconEnum],
        summary: str,
        precipitation: Optional[Precipitation],
        moon_phase: Optional[MoonPhase] = None
    ):
        self._title = title
        self._high_low = high_low
        self._icon = icon
        self._summary = summary
        self._precipitation = precipitation
        self._moon_phase = moon_phase

    # ---- Properties ----
    @property
    def title(self) -> str:
        return self._title

    @property
    def high_low(self) -> Optional[TemperatureHighLow]:
        return self._high_low

    @property
    def icon(self) -> Optional[WeatherIconEnum]:
        return self._icon

    @property
    def summary(self) -> str:
        return self._summary

    @property
    def precipitation(self) -> Optional[Precipitation]:
        return self._precipitation

    @property
    def moon_phase(self) -> Optional[MoonPhase]:
        return self._moon_phase

    def __repr__(self) -> str:
        return (
            f"DailyPredictions("
            f"title={self._title!r}, "
            f"high_low={self._high_low!r}, "
            f"icon={self._icon!r}, "
            f"summary={self._summary!r}, "
            f"precipitation={self._precipitation!r}, "
            f"moon_phase={self._moon_phase!r})"
        )