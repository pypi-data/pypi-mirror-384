import logging
from weathergrabber.domain.adapter.params import Params
from weathergrabber.service.search_location_service import SearchLocationService
from weathergrabber.service.read_weather_service import ReadWeatherService
from weathergrabber.service.extract_current_conditions_service import ExtractCurrentConditionsService
from weathergrabber.service.extract_today_details_service import ExtractTodayDetailsService
from weathergrabber.service.extract_aqi_service import ExtractAQIService
from weathergrabber.service.extract_health_activities_service import ExtractHealthActivitiesService
from weathergrabber.service.extract_hourly_forecast_service import ExtractHourlyForecastService
from weathergrabber.service.extract_hourly_forecast_oldstyle_service import ExtractHourlyForecastOldstyleService
from weathergrabber.service.extract_daily_forecast_service import ExtractDailyForecastService
from weathergrabber.service.extract_daily_forecast_oldstyle_service import ExtractDailyForecastOldstyleService
from weathergrabber.domain.search import Search
from weathergrabber.domain.forecast import Forecast

class UseCase:
    def __init__(
        self,
        search_location_service: SearchLocationService,
        read_weather_service: ReadWeatherService,
        extract_current_conditions_service: ExtractCurrentConditionsService,
        extract_today_details_service: ExtractTodayDetailsService,
        extract_aqi_service: ExtractAQIService,
        extract_health_activities_service: ExtractHealthActivitiesService,
        extract_hourly_forecast_service: ExtractHourlyForecastService,
        extract_hourly_forecast_oldstyle_service: ExtractHourlyForecastOldstyleService,
        extract_daily_forecast_service: ExtractDailyForecastService,
        extract_daily_forecast_oldstyle_service: ExtractDailyForecastOldstyleService,

    ):
        self.logger = logging.getLogger(__name__)
        self.read_weather_service = read_weather_service
        self.extract_current_conditions_service = extract_current_conditions_service
        self.extract_today_details_service = extract_today_details_service
        self.search_location_service = search_location_service
        self.extract_aqi_service = extract_aqi_service
        self.extract_health_activities_service = extract_health_activities_service
        self.extract_hourly_forecast_service = extract_hourly_forecast_service
        self.extract_hourly_forecast_oldstyle_service = extract_hourly_forecast_oldstyle_service
        self.extract_daily_forecast_service = extract_daily_forecast_service
        self.extract_daily_forecast_oldstyle_service = extract_daily_forecast_oldstyle_service

    def execute(self, params: Params) -> Forecast:

        self.logger.debug("Starting usecase")

        location_id = params.location.id
        search_name = params.location.search_name
        if not location_id:
            location_id = self.search_location_service.execute(params.location.search_name, params.language)

        weather_data = self.read_weather_service.execute(params.language, location_id)

        current_conditions = self.extract_current_conditions_service.execute(weather_data)
        today_details = self.extract_today_details_service.execute(weather_data)
        air_quality_index = self.extract_aqi_service.execute(weather_data)
        health_activities = self.extract_health_activities_service.execute(weather_data)
        
        try:
            hourly_predictions = self.extract_hourly_forecast_oldstyle_service.execute(weather_data)
        except ValueError:
            self.logger.warning("Falling back to new style hourly forecast extraction")
            hourly_predictions = self.extract_hourly_forecast_service.execute(weather_data)

        try:
            daily_predictions = self.extract_daily_forecast_oldstyle_service.execute(weather_data)
        except ValueError:
            self.logger.warning("Falling back to new style daily forecast extraction")
            daily_predictions = self.extract_daily_forecast_service.execute(weather_data)

        forecast = Forecast(
            search = Search(
                id = location_id,
                search_name = search_name
            ),
            current_conditions = current_conditions,
            today_details = today_details,
            air_quality_index = air_quality_index,
            health_activities = health_activities,
            hourly_predictions = hourly_predictions,
            daily_predictions = daily_predictions
        )

        self.logger.debug("Forecast data obtained %s", forecast)

        return forecast
        