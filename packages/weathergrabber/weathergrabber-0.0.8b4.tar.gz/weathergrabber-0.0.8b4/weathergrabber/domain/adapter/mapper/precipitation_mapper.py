from weathergrabber.domain.precipitation import Precipitation

def precipitation_to_dict(p: Precipitation) -> dict:
    return {
        "percentage": p.percentage,
        "amount": p.amount,
    }
