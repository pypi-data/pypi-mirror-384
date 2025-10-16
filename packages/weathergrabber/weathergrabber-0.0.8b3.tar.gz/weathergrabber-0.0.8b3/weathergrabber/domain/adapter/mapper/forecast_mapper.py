from weathergrabber.domain.forecast import Forecast

from weathergrabber.domain.adapter.mapper.search_mapper import search_to_dict
from weathergrabber.domain.adapter.mapper.current_conditions_mapper import current_conditions_to_dict
from weathergrabber.domain.adapter.mapper.today_details_mapper import today_details_to_dict
from weathergrabber.domain.adapter.mapper.air_quality_index_mapper import air_quality_index_to_dict
from weathergrabber.domain.adapter.mapper.health_activities_mapper import health_activities_to_dict
from weathergrabber.domain.adapter.mapper.hourly_predictions_mapper import hourly_predictions_to_dict
from weathergrabber.domain.adapter.mapper.daily_predictions_mapper import daily_predictions_to_dict

def forecast_to_dict(forecast: Forecast) -> dict:
    return {
        "search": search_to_dict(forecast.search) if forecast.search else None,
        "current_conditions": current_conditions_to_dict(forecast.current_conditions) if forecast.current_conditions else None,
        "today_details": today_details_to_dict(forecast.today_details) if forecast.today_details else None,
        "air_quality_index": air_quality_index_to_dict(forecast.air_quality_index) if forecast.air_quality_index else None,
        "health_activities": health_activities_to_dict(forecast.health_activities) if forecast.health_activities else None,
        "hourly_predictions": [hourly_predictions_to_dict(h) for h in forecast.hourly_predictions],
        "daily_predictions": [daily_predictions_to_dict(d) for d in forecast.daily_predictions],
    }
