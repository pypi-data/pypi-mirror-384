import logging
from pyquery import PyQuery
from weathergrabber.domain.today_details import TodayDetails
from weathergrabber.domain.temperature_hight_low import TemperatureHighLow
from weathergrabber.domain.uv_index import UVIndex
from weathergrabber.domain.moon_phase import MoonPhase
from weathergrabber.domain.moon_phase_enum import MoonPhaseEnum
from weathergrabber.domain.label_value import LabelValue
from weathergrabber.domain.sunrise_sunset import SunriseSunset

class ExtractTodayDetailsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def execute(self, weather_data: PyQuery) -> TodayDetails:
        self.logger.debug("Extracting today's details...")

        today_details_data = weather_data.find("div#todayDetails")
        feelslike = PyQuery(today_details_data).find("div[data-testid='FeelsLikeSection'] span")
        sunrise_sunset = PyQuery(today_details_data).find("div[data-testid='sunriseSunsetContainer'] div p[class*='TwcSunChart']")

        feelslike_label = feelslike.eq(0).text()  #'Feels Like'
        feelslike_value = feelslike.eq(1).text()  #'60°'

        sunrise = sunrise_sunset.eq(0).text()  #'6:12 AM'
        sunset = sunrise_sunset.eq(1).text()  #'7:45 PM'

        icons = today_details_data.find('svg[class*="WeatherDetailsListItem--icon"]')
        labels = today_details_data.find('div[class*="WeatherDetailsListItem--label"]')
        values = today_details_data.find('div[data-testid="wxData"]')

        self.logger.debug(f"Parsing today details values...")
        high_low_label = labels.eq(0).text()  #'High / Low'
        high_low_value = values.eq(0).text() #'--/54°'

        wind_label = labels.eq(1).text()  #'Wind'
        wind_value = values.eq(1).text()  #'7\xa0mph'

        humidity_label = labels.eq(2).text()  #'Humidity'
        humidity_value = values.eq(2).text()  #'100%'

        dew_point_label = labels.eq(3).text()  #'Dew Point'
        dew_point_value = values.eq(3).text()  #'60°'
            
        pressure_label = labels.eq(4).text()  #'Pressure'
        pressure_value = values.eq(4).text()  #'30.31\xa0in'

        uv_index_label = labels.eq(5).text()  #'UV Index'
        uv_index_value = values.eq(5).text()  #'5 of 10'

        visibility_label = labels.eq(6).text()  #'Visibility'
        visibility_value = values.eq(6).text()  #'10.0 mi'

        moon_phase_label = labels.eq(7).text()  #'Moon Phase'
        moon_phase_icon = icons.eq(7).attr('name')  #'phase-2'
        moon_phase_value = values.eq(7).text()  #'Waxing Crescent'

        self.logger.debug(f"Creating domain objects for today details...")

        sunrise_sunset = SunriseSunset(sunrise=sunrise, sunset=sunset)
        high_low = TemperatureHighLow.from_string(high_low_value, label=high_low_label)
        uv_index = UVIndex.from_string(uv_index_value, label=uv_index_label)
        moon_phase = MoonPhase(MoonPhaseEnum.from_name(moon_phase_icon), moon_phase_value, moon_phase_label)

        today_details = TodayDetails(
            feelslike=LabelValue(label=feelslike_label, value=feelslike_value),
            sunrise_sunset=sunrise_sunset,
            high_low=high_low,
            wind=LabelValue(label=wind_label, value=wind_value),
            humidity=LabelValue(label=humidity_label, value=humidity_value),
            dew_point=LabelValue(label=dew_point_label, value=dew_point_value),
            pressure=LabelValue(label=pressure_label, value=pressure_value),
            uv_index=uv_index,
            visibility=LabelValue(label=visibility_label, value=visibility_value),
            moon_phase=moon_phase
        )

        self.logger.debug(f"Extracted today's details: {today_details}")
        return today_details