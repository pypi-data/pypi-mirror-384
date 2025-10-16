from .weather_icon_enum import WeatherIconEnum

class SunriseSunset:
    class IconValue:
        def __init__(self, icon: WeatherIconEnum, value: str):
            self._icon = icon
            self._value = value

        @property
        def icon(self) -> WeatherIconEnum:
            return self._icon
        
        @property
        def value(self) -> str:
            return self._value
        
        def __str__(self):
            return f"{self._icon.emoji_icon} {self._value}"
        
        def __repr__(self):
            return f"IconValue(icon={self._icon}, value='{self._value}')"


    def __init__(self, sunrise: str, sunset: str):
        self._sunrise = SunriseSunset.IconValue(WeatherIconEnum.SUNRISE, sunrise)
        self._sunset = SunriseSunset.IconValue(WeatherIconEnum.SUNSET, sunset)

    @property
    def sunrise(self) -> "SunriseSunset.IconValue":
        return self._sunrise

    @property
    def sunset(self) -> "SunriseSunset.IconValue":
        return self._sunset

    def __str__(self):
        return f"Sunrise: {self._sunrise}, Sunset: {self._sunset}"
    
    def __repr__(self):
        return f"SunriseSunset(sunrise={self._sunrise}, sunset={self._sunset})"