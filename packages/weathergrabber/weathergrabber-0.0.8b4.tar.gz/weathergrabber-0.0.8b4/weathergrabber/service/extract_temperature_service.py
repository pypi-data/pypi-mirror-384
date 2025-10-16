import logging
from pyquery import PyQuery


class ExtractTemperatureService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def execute(self, weather_data: PyQuery) -> str:
        try:
            temperature = weather_data("div[class*='CurrentConditions--tempIconContainer'] span[data-testid='TemperatureValue']").text()
            self.logger.debug(f"Extracted temperature: {temperature}")
            return temperature
            
        except Exception as e:
            self.logger.error(f"Error temperature: {e}")
            raise ValueError("Could not extract temperature.")