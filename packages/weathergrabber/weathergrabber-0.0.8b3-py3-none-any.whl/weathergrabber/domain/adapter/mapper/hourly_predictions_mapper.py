from weathergrabber.domain.hourly_predictions import HourlyPredictions
from weathergrabber.domain.adapter.mapper.weather_icon_enum_mapper import weather_icon_enum_to_dict
from weathergrabber.domain.adapter.mapper.precipitation_mapper import precipitation_to_dict
from weathergrabber.domain.adapter.mapper.wind_mapper import wind_to_dict
from weathergrabber.domain.adapter.mapper.uv_index_mapper import uv_index_to_dict

def hourly_predictions_to_dict(hp: HourlyPredictions) -> dict:
    return {
        "title": hp.title,
        "temperature": hp.temperature,
        "icon": weather_icon_enum_to_dict(hp.icon) if hp.icon else None,
        "summary": hp.summary,
        "precipitation": precipitation_to_dict(hp.precipitation) if hp.precipitation else None,
        "wind": wind_to_dict(hp.wind) if hp.wind else None,
        "feels_like": hp.feels_like,
        "humidity": hp.humidity,
        "uv_index": uv_index_to_dict(hp.uv_index) if hp.uv_index else None,
        "cloud_cover": hp.cloud_cover,
    }
