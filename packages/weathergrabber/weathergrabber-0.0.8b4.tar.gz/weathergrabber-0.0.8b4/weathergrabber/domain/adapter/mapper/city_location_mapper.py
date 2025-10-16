from weathergrabber.domain.city_location import CityLocation

def city_location_to_dict(loc: CityLocation) -> dict:
    return {
        "city": loc.city,
        "state_province": loc.state_province,
        "country": loc.country,
    }
