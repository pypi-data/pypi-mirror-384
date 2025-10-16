from weathergrabber.adapter.client.weather_api import WeatherApi
import logging
from pyquery import PyQuery

class ReadWeatherService:
    def __init__(
            self,
            weather_api: WeatherApi
        ):
        self.weather_api = weather_api
        self.logging = logging.getLogger(__name__)

    def execute(self, language: str, location: str) -> PyQuery:

        self.logging.debug(f"Executing WeatherDataService with language: {language}, location: {location}")

        weather_data = self.weather_api.get_weather(language, location)

        self.logging.debug(f"Weather data retrieved.")

        return weather_data

        