
from weathergrabber.domain.today_details import TodayDetails
from weathergrabber.domain.adapter.mapper.label_value_mapper import label_value_to_dict
from weathergrabber.domain.adapter.mapper.sunrise_sunset_mapper import sunrise_sunset_to_dict
from weathergrabber.domain.adapter.mapper.temperature_high_low_mapper import temperature_high_low_to_dict
from weathergrabber.domain.adapter.mapper.uv_index_mapper import uv_index_to_dict
from weathergrabber.domain.adapter.mapper.moon_phase_mapper import moon_phase_to_dict

def today_details_to_dict(td: TodayDetails) -> dict:
    return {
        "feelslike": label_value_to_dict(td.feelslike) if td.feelslike else None,
        "sunrise_sunset": sunrise_sunset_to_dict(td.sunrise_sunset) if td.sunrise_sunset else None,
        "high_low": temperature_high_low_to_dict(td.high_low) if td.high_low else None,
        "wind": label_value_to_dict(td.wind) if td.wind else None,
        "humidity": label_value_to_dict(td.humidity) if td.humidity else None,
        "dew_point": label_value_to_dict(td.dew_point) if td.dew_point else None,
        "pressure": label_value_to_dict(td.pressure) if td.pressure else None,
        "uv_index": uv_index_to_dict(td.uv_index) if td.uv_index else None,
        "visibility": label_value_to_dict(td.visibility) if td.visibility else None,
        "moon_phase": moon_phase_to_dict(td.moon_phase) if td.moon_phase else None,
    }
