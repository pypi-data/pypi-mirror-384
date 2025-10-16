import logging
from pyquery import PyQuery
from weathergrabber.domain.precipitation import Precipitation
from weathergrabber.domain.weather_icon_enum import WeatherIconEnum
from weathergrabber.domain.moon_phase_enum import MoonPhaseEnum
from weathergrabber.domain.moon_phase import MoonPhase
from weathergrabber.domain.temperature_hight_low import TemperatureHighLow
from weathergrabber.domain.daily_predictions import DailyPredictions

from typing import List


class ExtractDailyForecastService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def execute(self, weather_data: PyQuery) -> List[DailyPredictions]:
        try:
            self.logger.debug("Extracting hourly forecast...")

            data = weather_data.find("section[data-testid='DailyForecast'] div[class*='Card'] details")

            if len(data) == 0:
                raise ValueError("Unable to extract daily forecast")

            details = [ { 
                "title": PyQuery(item).find("h2[data-testid='daypartName']").text(),
                "high-low" : PyQuery(item).find("div[data-testid='detailsTemperature']").text(),
                "icon" : PyQuery(item).find("svg[class*='DetailsSummary']").attr("name"),
                "summary" : PyQuery(item).find("span[class*='DetailsSummary--wxPhrase']").text(),
                "precip-percentage": PyQuery(item).find("div[data-testid='Precip'] span[data-testid='PercentageValue']").text(),
                "moon-phase-icon": PyQuery(item).find("li[data-testid='MoonphaseSection'] svg[class*='DetailsTable']").attr('name'),
                "moon-phase-value": PyQuery(item).find("li[data-testid='MoonphaseSection'] span[data-testid='moonPhase']").text(),
            } for item in data ]

            self.logger.debug("Extracted %s register(s)...",len(details))

            daily_predictions = [ 
                DailyPredictions(
                    title=item["title"],
                    high_low = TemperatureHighLow.from_string(item["high-low"]),
                    icon = WeatherIconEnum.from_name(item["icon"]),
                    summary = item["summary"],
                    precipitation = Precipitation(percentage=item["precip-percentage"]),
                    moon_phase = MoonPhase(MoonPhaseEnum.from_name(item["moon-phase-icon"]),item["moon-phase-value"])
            ) for item in details ]

            self.logger.debug("Created list of daily predictions with %s items", len(daily_predictions))

            return daily_predictions


        except Exception as e:
            self.logger.error(f"Error extracting daily forecast: {e}")
            raise ValueError("Could not extract daily forecast.") from e