from weathergrabber.usecase.use_case import UseCase
from weathergrabber.domain.adapter.params import Params
from weathergrabber.domain.adapter.icon_enum import IconEnum
from weathergrabber.domain.weather_icon_enum import WeatherIconEnum
import logging
import json

class WaybarTTY:

    def __init__(self, use_case: UseCase):
        self.logger = logging.getLogger(__name__)
        self.use_case = use_case
        pass

    def execute(self, params: Params) -> None:
        self.logger.info("Executing Waybar output")

        is_fa = params.icons == IconEnum.FA
        forecast = self.use_case.execute(params)

        # Forecast icon and temperature
        icon = forecast.current_conditions.icon.fa_icon if is_fa else forecast.current_conditions.icon.emoji_icon
        temperature = forecast.current_conditions.temperature
        rain_icon = WeatherIconEnum.RAIN.fa_icon if is_fa else WeatherIconEnum.RAIN.emoji_icon


        # City and state/province
        city_location = forecast.current_conditions.location

        # Summary
        summary = forecast.current_conditions.summary

        #Day/Night temperatures
        day_temp_label = WeatherIconEnum.DAY.fa_icon if is_fa else WeatherIconEnum.DAY.emoji_icon
        day_temp_value = forecast.current_conditions.day_night.day.value
        night_temp_label = WeatherIconEnum.NIGHT.fa_icon if is_fa else WeatherIconEnum.NIGHT.emoji_icon
        night_temp_value = forecast.current_conditions.day_night.night.value

        # Feels like
        feelslike_icon = WeatherIconEnum.FEEL.fa_icon if is_fa else WeatherIconEnum.FEEL.emoji_icon
        feelslike = forecast.today_details.feelslike.value

        # Sunrise and Sunset
        sunrise_icon = forecast.today_details.sunrise_sunset.sunrise.icon.fa_icon if is_fa else forecast.today_details.sunrise_sunset.sunrise.icon.emoji_icon
        sunrise_value = forecast.today_details.sunrise_sunset.sunrise.value
        sunset_icon = forecast.today_details.sunrise_sunset.sunset.icon.fa_icon if is_fa else forecast.today_details.sunrise_sunset.sunset.icon.emoji_icon
        sunset_value = forecast.today_details.sunrise_sunset.sunset.value

        # Moon phase
        moon_icon = forecast.today_details.moon_phase.icon.fa_icon if is_fa else forecast.today_details.moon_phase.icon.emoji_icon
        moon_phase = forecast.today_details.moon_phase.phase

        #Summary data
        wind_icon = WeatherIconEnum.WIND.fa_icon if is_fa else WeatherIconEnum.WIND.emoji_icon
        wind = forecast.today_details.wind.value
        uv_index = forecast.today_details.uv_index
        humidity_icon = WeatherIconEnum.HUMIDITY.fa_icon if is_fa else WeatherIconEnum.HUMIDITY.emoji_icon
        humidity = forecast.today_details.humidity.value
        pressure = forecast.today_details.pressure
        visibility_icon = WeatherIconEnum.VISIBILITY.fa_icon if is_fa else WeatherIconEnum.VISIBILITY.emoji_icon
        visibility = forecast.today_details.visibility.value

        #Air quality index
        color = forecast.air_quality_index.color.hex
        aqi_category = f" <span color=\"{color}\">{forecast.air_quality_index.category}</span>"
        aqi_acronym = forecast.air_quality_index.acronym
        aqi_value = forecast.air_quality_index.value

        hourly_predictions_format = [{
            'title': h.title if len(h.title) < 10 else h.title[:9] + '.',
            'temperature' : h.temperature,
            'icon': h.icon.fa_icon if is_fa else h.icon.emoji_icon,
            'precipitation': f"{h.precipitation.percentage if h.precipitation.percentage else ''}"
        } for h in forecast.hourly_predictions]

        daily_predictions_format = [
            {
                'title': d.title if len(d.title) < 10 else d.title[:9] + '.',
                'high_low': f"{d.high_low.high}/<span size='small'>{d.high_low.low}</span>",
                'icon': d.icon.fa_icon if is_fa else d.icon.emoji_icon,
                'precipitation': f"{d.precipitation.percentage}"
            } for d in forecast.daily_predictions
        ]

        # Hourly predictions and daily predictions
        hourly_predictions = [
                f"{h['title']}"
                f"{'\t\t' if len(h['title']) < 4 else '\t'}"
                f"{h['temperature']}"
                "\t\t"
                f"{h['icon']}\t"
                f"{rain_icon} {h['precipitation']}"
            for h in hourly_predictions_format
        ]

        daily_predictions = [
                f"{d['title']}"
                f"\t{'\t' if len(d['title']) < 6 else ' '}"
                f"{d['high_low']}"
                f"\t{'\t' if len(d['high_low']) < 33 else ''}"
                f"{d['icon']}\t"
                f"{rain_icon} {d['precipitation']}"
            for d in daily_predictions_format
        ]

        tooltip = (
            f"{city_location}\n"
            "\n"
            f"<span size='xx-large'>{icon}\t\t{temperature}</span>\n"
            "\n"
            f"{summary}\n"
            "\n"
            f"{day_temp_label}{day_temp_value} {night_temp_label}{night_temp_value}\t\t {feelslike_icon} {feelslike}\n"
            "\n"
            f"{sunrise_icon} {sunrise_value} • {sunset_icon} {sunset_value}\n"
            "\n"
            f"{moon_icon} {moon_phase}\n"
            "\n"
            f"{wind_icon} {wind}\t"
            f"{'\t' if len(wind) < 7 else ''}"
            f"{uv_index}\n"
            f"{humidity_icon} {humidity}\t\t{pressure}\n"
            f"{visibility_icon} {visibility}\t{aqi_acronym} {aqi_category} {aqi_value}\n"
            "\n"
            f"{'\n'.join(hourly_predictions)}\n"
            "\n"
            f"{'\n'.join(daily_predictions)}\n"
            "\n"
            f"<span size='small' style='italic' weight='light'>{forecast.current_conditions.timestamp}</span>"
        )

        waybar_output = {
            "text" : f"{icon} {temperature}",
            "alt": f"{summary}",
            "tooltip": f"{tooltip}",
            "class": f"{forecast.current_conditions.icon.name.lower() if forecast.current_conditions.icon else 'na'}",
        }

        print(json.dumps(waybar_output))
