import logging
import requests

class WeatherSearchApi:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}

    def search(self, location_name: str, lang: str = 'en-US'):

        if not location_name or len(location_name) < 1:
            raise ValueError("Location name must be provided and cannot be empty.")
        if len(location_name) > 100:
            raise ValueError("Location name is too long.")
        
        key = (location_name, lang)
        
        if key in self.cache:
            self.logger.debug("Cache hit for location '%s' and language '%s'.", location_name, lang)
            return self.cache[key]

        url = "https://weather.com/api/v1/p/redux-dal"
        headers = {"content-type": "application/json"}

        payload = [
            {
                "name": "getSunV3LocationSearchUrlConfig",
                "params": {
                    "query": location_name,
                    "language": lang,
                    "locationType": "locale"
                }
            }
        ]

        self.logger.debug("Sending request to Weather Search API '%s' for location '%s' with language '%s'...", url, location_name, lang)

        resp = requests.post(url, json=payload, headers=headers)

        if resp.status_code != 200:
            self.logger.error("HTTP '%s' error when searching for location '%s' with language '%s'.", resp.status_code, location_name, lang)
            raise ValueError(f"HTTP error {resp.status_code} when searching for location.")
        
        self.logger.debug("Received successful response from Weather Search API.")

        data = resp.json()

        self.cache[key] = data

        return data