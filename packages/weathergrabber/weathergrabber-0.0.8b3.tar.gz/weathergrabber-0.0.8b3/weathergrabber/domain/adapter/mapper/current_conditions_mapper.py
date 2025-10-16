
from weathergrabber.domain.current_conditions import CurrentConditions
from weathergrabber.domain.adapter.mapper.city_location_mapper import city_location_to_dict
from weathergrabber.domain.adapter.mapper.timestamp_mapper import timestamp_to_dict
from weathergrabber.domain.adapter.mapper.weather_icon_enum_mapper import weather_icon_enum_to_dict
from weathergrabber.domain.adapter.mapper.day_night_mapper import day_night_to_dict

def current_conditions_to_dict(cc: CurrentConditions) -> dict:
    return {
        "location": city_location_to_dict(cc.location) if cc.location else None,
        "timestamp": timestamp_to_dict(cc.timestamp) if cc.timestamp else None,
        "temperature": cc.temperature,
        "icon": weather_icon_enum_to_dict(cc.icon) if cc.icon else None,
        "summary": cc.summary,
        "day_night": day_night_to_dict(cc.day_night) if cc.day_night else None,
    }
