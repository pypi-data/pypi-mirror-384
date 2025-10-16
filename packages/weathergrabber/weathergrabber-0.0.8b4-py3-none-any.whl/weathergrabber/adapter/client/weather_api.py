from pyquery import PyQuery
from urllib.error import HTTPError
import logging

class WeatherApi:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def get_weather(self,language: str, location: str) -> PyQuery:
        url = f"https://weather.com/{language}/weather/today/l/{location}"

        if location == None:
            url = f"https://weather.com/{language}/weather/today"       
        elif len(location) < 64 :
            raise ValueError("Invalid location id")
        
        if language == None:
            raise ValueError("language must be specified")
        
        try:
            self.logger.debug(f"Fetching weather data from URL: %s.", url)
            return PyQuery(url=url)
        except HTTPError as e:
            self.logger.error("HTTP '%s' error when fetching weather data from URL: '%s'.", e.code, url)
            raise ValueError(f"HTTP error {e.code} when fetching weather data.")