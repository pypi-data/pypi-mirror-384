import logging
from pyquery import PyQuery
from weathergrabber.domain.health_activities import HealthActivities

class ExtractHealthActivitiesService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def execute(self, weather_data: PyQuery) -> HealthActivities | None:
        
        self.logger.debug("Extracting Health & Activities...")

        try:
            # 'Health & Activities\nGrass\nSeasonal Allergies and Pollen Count Forecast\nGrass pollen is low in your area'
            data = weather_data("section[data-testid='HealthAndActivitiesModule']").text()

            health_activities = HealthActivities.from_text(data) if data else None

            self.logger.debug(f"Extracted Health & Activities data: {health_activities}")

            return health_activities
        
        except Exception as e:
            self.logger.error(f"Error extracting Health & Activities data: {e}")
            raise ValueError("Could not extract Health & Activities data") from e