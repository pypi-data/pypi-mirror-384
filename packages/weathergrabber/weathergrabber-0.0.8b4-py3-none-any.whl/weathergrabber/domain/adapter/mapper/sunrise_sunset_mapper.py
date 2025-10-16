from weathergrabber.domain.sunrise_sunset import SunriseSunset
from weathergrabber.domain.adapter.mapper.weather_icon_enum_mapper import weather_icon_enum_to_dict

def sunrise_sunset_to_dict(ss: SunriseSunset) -> dict:
    def icon_value_to_dict(iv):
        return {
            "icon": weather_icon_enum_to_dict(iv.icon) if iv.icon else None,
            "value": iv.value,
        } if iv else None
    return {
        "sunrise": icon_value_to_dict(ss.sunrise) if ss.sunrise else None,
        "sunset": icon_value_to_dict(ss.sunset) if ss.sunset else None,
    }
