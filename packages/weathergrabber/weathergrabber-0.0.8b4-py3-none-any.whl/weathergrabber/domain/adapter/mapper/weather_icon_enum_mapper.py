from weathergrabber.domain.weather_icon_enum import WeatherIconEnum

def weather_icon_enum_to_dict(icon: WeatherIconEnum) -> dict:
    return {
        "name": icon.name,
        "fa_icon": icon.fa_icon,
        "emoji_icon": icon.emoji_icon,
    }
