from .temperature_hight_low import TemperatureHighLow
from .label_value import LabelValue
from typing import Optional
from .uv_index import UVIndex
from .moon_phase import MoonPhase
from .sunrise_sunset import SunriseSunset

class TodayDetails:

    def __init__(
            self,
            feelslike: LabelValue,
            sunrise_sunset: Optional["SunriseSunset"],
            high_low: Optional[TemperatureHighLow],
            wind: LabelValue,
            humidity: LabelValue,
            dew_point: LabelValue,
            pressure: LabelValue,
            uv_index: Optional[UVIndex],
            visibility: LabelValue,
            moon_phase: Optional[MoonPhase]
        ):
        self._feelslike = feelslike
        self._sunrise_sunset = sunrise_sunset
        self._high_low = high_low
        self._wind = wind
        self._humidity = humidity
        self._dew_point = dew_point
        self._pressure = pressure
        self._uv_index = uv_index
        self._visibility = visibility
        self._moon_phase = moon_phase

    @property
    def feelslike(self) -> LabelValue:
        return self._feelslike

    @property
    def sunrise_sunset(self) -> Optional[SunriseSunset]:
        return self._sunrise_sunset

    @property
    def high_low(self) -> Optional[TemperatureHighLow]:
        return self._high_low
    
    @property
    def wind(self) -> LabelValue:
        return self._wind
    
    @property
    def humidity(self) -> LabelValue:
        return self._humidity
    
    @property
    def dew_point(self) -> LabelValue:
        return self._dew_point
    
    @property
    def pressure(self) -> LabelValue:
        return self._pressure
    
    @property
    def uv_index(self) -> Optional[UVIndex]:
        return self._uv_index
    
    @property
    def visibility(self) -> LabelValue:
        return self._visibility
    
    @property
    def moon_phase(self) -> Optional[MoonPhase]:
        return self._moon_phase

    def __repr__(self):
        return (f"TodayDetails(feelslike={self.feelslike!r}, sunrise_sunset={self.sunrise_sunset!r},"
                f"high_low={self.high_low!r}, wind={self.wind!r}, "
                f"humidity={self.humidity!r}, dew_point={self.dew_point!r}, "
                f"pressure={self.pressure!r}, uv_index={self.uv_index!r}, "
                f"visibility={self.visibility!r}, moon_phase={self.moon_phase!r})")