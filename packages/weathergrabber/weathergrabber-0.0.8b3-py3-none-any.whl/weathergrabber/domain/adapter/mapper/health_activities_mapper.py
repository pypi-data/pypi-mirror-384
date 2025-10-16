from weathergrabber.domain.health_activities import HealthActivities

def health_activities_to_dict(ha: HealthActivities) -> dict:
    return {
        "category_name": ha.category_name,
        "title": ha.title,
        "description": ha.description,
    }
