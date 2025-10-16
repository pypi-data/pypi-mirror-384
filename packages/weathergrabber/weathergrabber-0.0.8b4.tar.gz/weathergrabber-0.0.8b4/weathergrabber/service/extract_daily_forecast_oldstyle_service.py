import logging
from pyquery import PyQuery
from weathergrabber.domain.daily_predictions import DailyPredictions
from weathergrabber.domain.temperature_hight_low import TemperatureHighLow
from weathergrabber.domain.weather_icon_enum import WeatherIconEnum
from weathergrabber.domain.precipitation import Precipitation
from typing import List

class ExtractDailyForecastOldstyleService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def execute(self, weather_data: PyQuery) -> List[DailyPredictions]:
        self.logger.debug("Extracting daily forecast, oldstyle...")
        
        try:

            data = weather_data.find("div[class*='DailyWeatherCard'] > ul li")

            if len(data) == 0:
                raise ValueError("Unable to extract hourly forecast using old style")

            details = [ {
                "title": PyQuery(item).find("h3 > span").text(),
                "high-low" : PyQuery(item).find("div[data-testid='SegmentHighTemp']").text(),
                "icon" : PyQuery(item).find("svg").attr("name"),
                "summary" : PyQuery(item).find("span[class*='Column--iconPhrase']").text(),
                "precip-percentage" : PyQuery(item).find("div[data-testid='SegmentPrecipPercentage'] span[class*='Column--precip']").contents().eq(1).text()
            } for item in data ]

            self.logger.debug("Extracted %s register(s)...",len(details))

            daily_predictions = [DailyPredictions(
                title=item["title"],
                high_low=TemperatureHighLow.from_string(item["high-low"]),
                icon=WeatherIconEnum.from_name(item["icon"]),
                summary=item["summary"],
                precipitation=Precipitation(
                    percentage=item["precip-percentage"]
                )
            ) for item in details]

            self.logger.debug("Created daily forecast list with %s registers", len(daily_predictions))

            return daily_predictions
        
        except Exception as e:

            self.logger.error(f"Error extracting daily forecast: {e}")
            raise ValueError("Could not extract daily forecast.") from e
