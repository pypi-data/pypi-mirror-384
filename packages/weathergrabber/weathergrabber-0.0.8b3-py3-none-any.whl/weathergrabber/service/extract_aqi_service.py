import logging
from weathergrabber.domain.air_quality_index import AirQualityIndex
from pyquery import PyQuery

class ExtractAQIService:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        pass

    def execute(self, weather_data: PyQuery) -> AirQualityIndex | None:

        self.logger.debug("Extracting Air Quality Index (AQI)...")

        try:
            # 'Air Quality Index\n27\nGood\nAir quality is considered satisfactory, and air pollution poses little or no risk.\nSee Details\nInfo'
            aqi_data = weather_data("section[data-testid='AirQualityModule']").text()
            
            # 'stroke-width:5;stroke-dasharray:10.021680564951442 172.78759594743863;stroke:#00E838'
            color_data = weather_data("section[data-testid='AirQualityModule'] svg[data-testid='DonutChart'] circle:nth-of-type(2)").attr("style")
            
            air_quality_index = AirQualityIndex.aqi_color_from_string(aqi_data,color_data)
            
            self.logger.debug(f"Extracted AQI data: {air_quality_index}")
            
            return air_quality_index
        except Exception as e:
            self.logger.error(f"Error extracting AQI data: {e}")
            raise ValueError("Could not extract AQI data") from e
        