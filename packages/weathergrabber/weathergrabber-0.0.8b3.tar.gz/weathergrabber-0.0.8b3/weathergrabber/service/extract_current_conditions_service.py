import logging
from pyquery import PyQuery
from weathergrabber.domain.weather_icon_enum import WeatherIconEnum
from weathergrabber.domain.city_location import CityLocation
from weathergrabber.domain.timestamp import Timestamp
from weathergrabber.domain.day_night import DayNight
from weathergrabber.domain.current_conditions import CurrentConditions

class ExtractCurrentConditionsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def execute(self, weather_data: PyQuery) -> dict:
        self.logger.debug("Extracting Current Conditions")

        data = PyQuery(weather_data('div[data-testid="CurrentConditionsContainer"]'))
    
        city_location_data = data.find('h1').text() #'Nova Friburgo, Rio de Janeiro, Brazil'
        timestamp_data = data.find('span[class*="timestamp"]').text() # 'As of 8:01 pm GMT-03:00'
        icon_data = data.find('svg[class*="wxIcon"]').attr('name') # 'partly-cloudy-night'
        temp_day_night = data.find('div[class*="tempHiLoValue"]').text() #'Day\xa063°\xa0•\xa0Night\xa046°'

        city_location = CityLocation.from_string(city_location_data)
        timestamp = Timestamp.from_string(timestamp_data)
        temperature = data.find('span[class*="tempValue"]').text() # '48°'
        icon = WeatherIconEnum.from_name(icon_data)
        phrase = data.find('div[data-testid*="wxPhrase"]').text() # 'Partly Cloudy'
        day_night = DayNight.from_string(temp_day_night)

        current_conditions = CurrentConditions(
            location=city_location,
            timestamp=timestamp,
            temperature=temperature,
            icon=icon,
            summary=phrase,
            day_night=day_night
        )

        self.logger.debug(f"Extracted current conditions: {current_conditions}")

        return current_conditions