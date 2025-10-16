from enum import Enum

class WeatherIconEnum(Enum):
    CLEAR = ('clear', chr(0xF0599), '☀️')
    CLEAR_NIGHT = ('clear-night', chr(0xF0594), '🌙')
    CLOUDY = ('cloudy', '\uf0c2', '☁️')
    CLOUDY_FOGGY_DAY = ('cloudy-foggy-day', chr(0xF013), '🌥️')
    CLOUDY_FOGGY_NIGHT = ('cloudy-foggy-night', chr(0xF013), '🌥️')
    DAY = ('day', '\uf185', '🌞')
    DRIZZLE = ('drizzle', '\uf0e9', '🌦️')
    FEEL = ('feel', '\uf2c9', '🥵')
    FOGGY = ('foggy', '\uf74e', '🌫️')
    HUMIDITY = ('humidity', '\uf043', '💧')
    ISOLATED_THUNDERSTORMS = ('isolated-thunderstorms', chr(0x26C8), '⛈️')
    MOSTLY_CLEAR_DAY = ('mostly-clear-day', chr(0xF0599), '☀️')
    MOSTLY_CLEAR_NIGHT = ('mostly-clear-night', chr(0xF0594), '🌙')
    MOSTLY_CLOUDY_DAY = ('mostly-cloudy-day', chr(0xf013), '☁️')
    MOSTLY_CLOUDY_NIGHT = ('mostly-cloudy-night', chr(0xf013), '☁️')
    NIGHT = ('night', '\uf186', '🌜')
    PARTLY_CLOUDY_DAY = ('partly-cloudy-day', chr(0xF0595), '⛅')
    PARTLY_CLOUDY_NIGHT = ('partly-cloudy-night', chr(0xF0F31), '☁️')
    RAIN = ('rain', '\uf0e9', '🌧️')
    RAIN_SHOW_WINTERY_MIX = ('rain-snow-wintery-mix', '\u26c6', '🌨️')
    RAINY_DAY = ('rainy-day', chr(0x1F326), '🌧️')
    RAINY_NIGHT = ('rainy-night', chr(0x1F326), '🌧️')
    SCATTERED_SNOW_SHOWERS_NIGHT = ('scattered-snow-showers-night', '\u26c6', '🌨️')
    SCATTERED_SHOWERS_DAY = ('scattered-showers-day', chr(0x1F326), '🌦️')
    SCATTERED_SHOWERS_NIGHT = ('scattered-showers-night', chr(0x1F326), '🌦️')
    SCATTERED_THUNDERSTORMS_DAY = ('scattered-thunderstorms-day', chr(0x26C8), '⛈️')
    SCATTERED_THUNDERSTORMS_NIGHT = ('scattered-thunderstorms-night', chr(0x26C8), '⛈️')
    SEVERE = ('severe', '\ue317', '🌩️')
    SHOWERS = ('showers', '\u26c6', '🌧️')
    SMOKE = ('smoke', '\uf062', '💨')
    SNOW = ('snow', '\uf2dc', '❄️')
    SNOWY_ICY_DAY = ('snowy-icy-day', '\uf2dc', '❄️')
    SNOWY_ICY_NIGHT = ('snowy-icy-night', '\uf2dc', '❄️')
    SNOW_SHOWERS = ('snow-showers', '\u26c6', '🌨️')
    SUNNY = ('sunny', chr(0xF0599), '☀️')
    SUNRISE = ('sunrise', '\ue34c', '🌅')
    SUNSET = ('sunset', '\ue34d', '🌇')
    THUNDERSTORMS = ('thunderstorms', '\uf0e7', '⛈️')
    VISIBILITY = ('visibility', '\uf06e', '👁️')
    WIND = ('wind', chr(0xf059d), '🌪️')
    WINDY = ('windy', chr(0xf059d), '🌪️')
    # Suggestions from Copilot
    BLIZZARD = ('blizzard', '\u2744', '🌨️')
    DUST = ('dust', '\uf063', '🌪️')
    FLURRIES = ('flurries', '\u2744', '🌨️')
    FREEZING_DRIZZLE = ('freezing-drizzle', '\uf0e9', '🌧️')
    FREEZING_RAIN = ('freezing-rain', '\uf0e9', '🌧️')
    HAIL = ('hail', '\uf015', '🌨️')
    HAZE = ('haze', '\uf0b6', '🌫️')
    HURRICANE = ('hurricane', '\uf073', '🌀')
    ICE = ('ice', '\u2744', '🧊')
    MIXED_RAIN_AND_SLEET = ('mixed-rain-and-sleet', '\uf0e9', '🌧️')
    MIXED_RAIN_AND_SNOW = ('mixed-rain-and-snow', '\uf0e9', '🌧️')
    MIXED_SNOW_AND_SLEET = ('mixed-snow-and-sleet', '\uf2dc', '❄️')
    SAND = ('sand', '\uf063', '🏜️')
    SLEET = ('sleet', '\uf0e9', '🌨️')
    TORNADO = ('tornado', '\uf056', '🌪️')
    TROPICAL_STORM = ('tropical-storm', '\uf073', '🌀')

    def __init__(self, name: str, fa_icon: str, emoji_icon: str):
        self._name = name
        self._fa_icon = fa_icon
        self._emoji_icon = emoji_icon

    @property
    def name(self):
        return self._name
    
    @property
    def fa_icon(self):
        return self._fa_icon
    
    @property
    def emoji_icon(self):   
        return self._emoji_icon

    @staticmethod
    def from_name(name: str):
        for item in WeatherIconEnum:
            if item._name == name:
                return item
        raise ValueError(f'WeatherIconEnum: No icon found for name "{name}"')