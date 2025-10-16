class HealthActivities:
    def __init__(self, category_name: str, title: str, description: str):
        self._category_name = category_name
        self._title = title
        self._description = description
    
    @property
    def category_name(self) -> str:
        return self._category_name
    
    @property
    def title(self) -> str:
        return self._title
    
    @property
    def description(self) -> str:
        return self._description
    
    def __str__(self) -> str:
        return f"{self._category_name}: {self._title} - {self._description}"
    
    def __repr__(self) -> str:
        return f"HealthActivities(category_name={self._category_name!r}, title={self._title!r}, description={self._description!r})"
    
    # 'Health & Activities\nGrass\nSeasonal Allergies and Pollen Count Forecast\nGrass pollen is low in your area'
    @staticmethod
    def from_text(text: str):
        try:
            lines = text.split('\n')
            if len(lines) >= 4:
                category_name = lines[0].strip()
                #Ignore the "grass" line
                title = lines[2].strip()
                description = ' '.join(line.strip() for line in lines[3:]).strip()
                return HealthActivities(category_name, title, description)
            else:
                raise ValueError("Insufficient data to parse HealthActivities")
        except Exception as e:
            raise ValueError("Could not parse HealthActivities from text") from e
