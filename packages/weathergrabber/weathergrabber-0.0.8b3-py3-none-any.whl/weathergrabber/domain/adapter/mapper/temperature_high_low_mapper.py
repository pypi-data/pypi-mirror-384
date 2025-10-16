from weathergrabber.domain.temperature_hight_low import TemperatureHighLow

def temperature_high_low_to_dict(thl: TemperatureHighLow) -> dict:
    return {
        "high": thl.high,
        "low": thl.low,
        "label": thl.label,
    }
