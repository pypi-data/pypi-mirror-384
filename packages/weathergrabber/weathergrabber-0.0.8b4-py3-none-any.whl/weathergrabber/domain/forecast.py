from typing import Optional, List
from .search import Search
from .weather_icon_enum import WeatherIconEnum
from .today_details import TodayDetails
from .air_quality_index import AirQualityIndex
from .health_activities import HealthActivities
from .hourly_predictions import HourlyPredictions
from .daily_predictions import DailyPredictions
from .current_conditions import CurrentConditions


class Forecast:
    def __init__(
        self,
        search: Optional[Search],
        current_conditions: Optional[CurrentConditions],
        today_details: Optional[TodayDetails],
        air_quality_index: Optional[AirQualityIndex],
        health_activities: Optional[HealthActivities],
        hourly_predictions: List[HourlyPredictions],
        daily_predictions: List[DailyPredictions],
    ):
        self._search = search
        self._current_conditions = current_conditions
        self._today_details = today_details
        self._air_quality_index = air_quality_index
        self._health_activities = health_activities
        self._hourly_predictions = hourly_predictions
        self._daily_predictions = daily_predictions

    @property
    def search(self) -> Optional[Search]:
        return self._search

    @property
    def current_conditions(self) -> Optional[CurrentConditions]:
        return self._current_conditions

    @property
    def today_details(self) -> Optional[TodayDetails]:
        return self._today_details

    @property
    def air_quality_index(self) -> Optional[AirQualityIndex]:
        return self._air_quality_index

    @property
    def health_activities(self) -> Optional[HealthActivities]:
        return self._health_activities

    @property
    def hourly_predictions(self) -> List[HourlyPredictions]:
        return self._hourly_predictions

    @property
    def daily_predictions(self) -> List[DailyPredictions]:
        return self._daily_predictions

    def __repr__(self) -> str:
        return (
            f"Forecast(search={self._search}, "
            f"current_conditions={self._current_conditions}, "
            f"today_details={self._today_details}, "
            f"air_quality_index={self._air_quality_index}, "
            f"health_activities={self._health_activities}, "
            f"hourly_predictions={len(self._hourly_predictions)} items, "
            f"daily_predictions={len(self._daily_predictions)} items)"
        )
