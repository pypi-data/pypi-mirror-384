from weathergrabber.domain.daily_predictions import DailyPredictions
from weathergrabber.domain.adapter.mapper.temperature_high_low_mapper import temperature_high_low_to_dict
from weathergrabber.domain.adapter.mapper.weather_icon_enum_mapper import weather_icon_enum_to_dict
from weathergrabber.domain.adapter.mapper.precipitation_mapper import precipitation_to_dict
from weathergrabber.domain.adapter.mapper.moon_phase_mapper import moon_phase_to_dict

def daily_predictions_to_dict(dp: DailyPredictions) -> dict:
    return {
        "title": dp.title,
        "high_low": temperature_high_low_to_dict(dp.high_low) if dp.high_low else None,
        "icon": weather_icon_enum_to_dict(dp.icon) if dp.icon else None,
        "summary": dp.summary,
        "precipitation": precipitation_to_dict(dp.precipitation) if dp.precipitation else None,
        "moon_phase": moon_phase_to_dict(dp.moon_phase) if dp.moon_phase else None,
    }
