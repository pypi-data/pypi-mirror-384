import logging
from pyquery import PyQuery
from weathergrabber.domain.hourly_predictions import HourlyPredictions
from weathergrabber.domain.weather_icon_enum import WeatherIconEnum
from weathergrabber.domain.uv_index import UVIndex
from weathergrabber.domain.precipitation import Precipitation
from weathergrabber.domain.wind import Wind
from typing import List


class ExtractHourlyForecastService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def execute(self, weather_data: PyQuery) -> List[HourlyPredictions]:
        self.logger.debug("Extracting hourly forecast...")

        data = weather_data.find("section[data-testid='HourlyForecast'] div[class*='Card'] details")

        if len(data) == 0:
            raise ValueError("There's no hourly forecast data available.")

        details = [ { 
            "title": PyQuery(item).find("h2").text(),
            "temperature" : PyQuery(item).find("div[data-testid='detailsTemperature']").text(),
            "icon" : PyQuery(item).find("svg[class*='DetailsSummary']").attr("name"),
            "summary" : PyQuery(item).find("span[class*='DetailsSummary--wxPhrase']").text(),
            "precip-percentage": PyQuery(item).find("div[data-testid='Precip'] span[data-testid='PercentageValue']").text(),
            "wind": PyQuery(item).find("span[data-testid='WindTitle']").next().eq(0).text(),
            "feels-like" : PyQuery(item).find("span[data-testid='FeelsLikeTitle']").next().text(),
            "humidity" : PyQuery(item).find("span[data-testid='HumidityTitle']").next().text(),
            "uv-index" : PyQuery(item).find("span[data-testid='UVIndexValue']").text(),
            "cloud-cover" : PyQuery(item).find("span[data-testid='CloudCoverTitle']").next().text(),
            "rain-amount" : PyQuery(item).find("span[data-testid='AccumulationTitle']").next().text()
        } for item in data ]

        self.logger.debug("Extracted %s register(s)...",len(details))

        hourly_forecasts = [HourlyPredictions(
            title=item["title"],
            temperature=item["temperature"],
            icon=WeatherIconEnum.from_name(item["icon"]),
            summary=item["summary"],
            precipitation=Precipitation(
                percentage=item["precip-percentage"],
                amount=item["rain-amount"]
            ),
            wind=Wind.from_string(item["wind"]),
            feels_like=item["feels-like"],
            humidity=item["humidity"],
            uv_index=UVIndex.from_string(item["uv-index"]),
            cloud_cover=item["cloud-cover"]
        ) for item in details]

        self.logger.debug("Created hourly forecast list with %s registers", len(hourly_forecasts))

        return hourly_forecasts
