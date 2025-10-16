
from weathergrabber.domain.air_quality_index import AirQualityIndex
from weathergrabber.domain.adapter.mapper.color_mapper import color_to_dict

def air_quality_index_to_dict(aqi: AirQualityIndex) -> dict:
    return {
        "title": aqi.title,
        "value": aqi.value,
        "category": aqi.category,
        "description": aqi.description,
        "acronym": aqi.acronym,
        "color": color_to_dict(aqi.color) if aqi.color else None,
    }
