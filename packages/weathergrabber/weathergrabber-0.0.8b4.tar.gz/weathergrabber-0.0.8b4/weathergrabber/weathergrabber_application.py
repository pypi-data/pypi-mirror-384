import logging
from time import sleep
from .domain.adapter.params import Params
from .domain.adapter.output_enum import OutputEnum
from .adapter.client.weather_api import WeatherApi
from .adapter.client.weather_search_api import WeatherSearchApi
from .service.search_location_service import SearchLocationService
from .service.read_weather_service import ReadWeatherService
from .service.extract_current_conditions_service import ExtractCurrentConditionsService
from .service.extract_today_details_service import ExtractTodayDetailsService
from .service.extract_aqi_service import ExtractAQIService
from .service.extract_health_activities_service import ExtractHealthActivitiesService
from .service.extract_hourly_forecast_service import ExtractHourlyForecastService
from .service.extract_hourly_forecast_oldstyle_service import ExtractHourlyForecastOldstyleService
from .service.extract_daily_forecast_service import ExtractDailyForecastService
from .service.extract_daily_forecast_oldstyle_service import ExtractDailyForecastOldstyleService
from .usecase.use_case import UseCase


class WeatherGrabberApplication:

    def _beans(self):
        self.weather_search_api = WeatherSearchApi()
        self.weather_api = WeatherApi()
        self.search_location_service = SearchLocationService(self.weather_search_api)
        self.read_weather_service = ReadWeatherService(self.weather_api)
        self.extract_current_conditions_service = ExtractCurrentConditionsService()
        self.extract_today_details_service = ExtractTodayDetailsService()
        self.extract_aqi_service = ExtractAQIService()
        self.extract_health_activities_service = ExtractHealthActivitiesService()
        self.extract_hourly_forecast_service = ExtractHourlyForecastService()
        self.extract_hourly_forecast_oldstyle_service = ExtractHourlyForecastOldstyleService()
        self.extract_daily_forecast_service = ExtractDailyForecastService()
        self.extract_daily_forecast_oldstyle_service = ExtractDailyForecastOldstyleService()
        self.use_case = UseCase(
                self.search_location_service,
                self.read_weather_service,
                self.extract_current_conditions_service,
                self.extract_today_details_service,
                self.extract_aqi_service,
                self.extract_health_activities_service,
                self.extract_hourly_forecast_service,
                self.extract_hourly_forecast_oldstyle_service,
                self.extract_daily_forecast_service,
                self.extract_daily_forecast_oldstyle_service
            )
        pass
        
    def _define_controller(self, output_format: OutputEnum):
        if output_format == OutputEnum.CONSOLE:
            from weathergrabber.adapter.tty.console_tty import ConsoleTTY
            self.controller = ConsoleTTY(self.use_case)

        elif output_format == OutputEnum.JSON:
            from weathergrabber.adapter.tty.json_tty import JsonTTY
            self.controller = JsonTTY(self.use_case)

        elif output_format == OutputEnum.WAYBAR:
            from weathergrabber.adapter.tty.waybar_tty import WaybarTTY
            self.controller = WaybarTTY(self.use_case)

        else:
            self.logger.error(f"Unsupported output format: {output_format}")
            raise ValueError(f"Unsupported output format: {output_format}")
        
    def __init__(self, params: Params):
        self.logger = logging.getLogger(__name__)
        self._beans()
        self._define_controller(params.output_format)
        self.logger.info("Starting WeatherGrabber Application")
        if params.keep_open:
            self.logger.info("Keep open mode enabled, the application will refresh every 5 minutes")
            while True:
                self.controller.execute(params)
                sleep(1)  # Sleep for 5 minutes
        else:
            self.controller.execute(params)
        self.logger.info("WeatherGrabber Application finished")