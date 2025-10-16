import logging
from pyquery import PyQuery
from weathergrabber.domain.hourly_predictions import HourlyPredictions
from weathergrabber.domain.weather_icon_enum import WeatherIconEnum
from weathergrabber.domain.precipitation import Precipitation
from typing import List

class ExtractHourlyForecastOldstyleService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def execute(self, weather_data: PyQuery) -> List[HourlyPredictions]:
        self.logger.debug("Extracting hourly forecast, oldstyle...")
        
        try:

            data = weather_data.find("div[class*='TodayWeatherCard'] > ul li")

            if len(data) == 0:
                raise ValueError("Unable to extract hourly forecast using old style")

            details = [ {
                "title": PyQuery(item).find("h3 > span").text(),
                "temperature" : PyQuery(item).find("span[data-testid='TemperatureValue']").text(),
                "icon" : PyQuery(item).find("svg").attr("name"),
                "summary" : PyQuery(item).find("span[class*='Column--iconPhrase']").text(),
                "precip-percentage" : PyQuery(item).find("div[data-testid='SegmentPrecipPercentage'] span[class*='Column--precip']").contents().eq(1).text()
            } for item in data ]

            self.logger.debug("Extracted %s register(s)...",len(details))

            hourly_forecasts = [HourlyPredictions(
                title=item["title"],
                temperature=item["temperature"],
                icon=WeatherIconEnum.from_name(item["icon"]),
                summary=item["summary"],
                precipitation=Precipitation(
                    percentage=item["precip-percentage"]
                )
            ) for item in details]

            self.logger.debug("Created hourly forecast list with %s registers", len(hourly_forecasts))

            return hourly_forecasts
        
        except Exception as e:

            self.logger.error(f"Error extracting hourly forecast: {e}")
            raise ValueError("Could not extract hourly forecast.") from e
