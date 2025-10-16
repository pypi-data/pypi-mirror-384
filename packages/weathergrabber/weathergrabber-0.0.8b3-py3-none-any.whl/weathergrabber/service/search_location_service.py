from weathergrabber.adapter.client.weather_search_api import WeatherSearchApi
import logging

class SearchLocationService:
    def __init__(self, api: WeatherSearchApi):
        self.api = api
        self.logger = logging.getLogger(__name__)
        pass

    def execute(self, location_name: str, lang: str) -> str | None:
        self.logger.debug(f"Searching for location: {location_name} with language: {lang}")

        if not location_name:
            self.logger.debug("No location name provided. Bypassing search.")
            return None
        
        try:
            data = self.api.search(location_name, lang)
            if not data:
                self.logger.error(f"No data found for location: {location_name}")
                raise ValueError(f"Location '{location_name}' not found.")
            
            dal = data["dal"]["getSunV3LocationSearchUrlConfig"]

            # Pick the first (arbitrary) key, then get the value
            first_key = next(iter(dal))
            location_id = dal[first_key]["data"]["location"]["placeId"][0]
            
            self.logger.debug(f"Found location ID: {location_id} for location name: {location_name}")
            
            return location_id
        except Exception as e:
            self.logger.error(f"Error searching for location '{location_name}': {e}")
            raise ValueError(f"Could not find location '{location_name}'.")

