from .color import Color
from typing import Optional

class AirQualityIndex:
    def __init__(self,
            title: str, 
            value: int, 
            category: Optional[str] = None, 
            description: Optional[str] = None, 
            acronym: Optional[str] = None, 
            color: Optional[Color] = None
        ):
        self._title = title
        self._value = value
        self._category = category
        self._description = description
        self._acronym = acronym
        self._color = color

    @property
    def title(self) -> str:
        return self._title

    @property
    def value(self) -> int:
        return self._value
    
    @property
    def category(self) -> str | None:
        return self._category
    
    @property
    def description(self) -> str | None:
        return self._description
    
    @property
    def acronym(self) -> str | None:
        return self._acronym
    
    @property
    def color(self) -> Color | None:
        return self._color
    
    def __str__(self) -> str:
        return f"Title: {self.title}. AQI: {self.value}, Category: {self.category}, Description: {self.description}, Acronym: {self.acronym}, Color: {self.color}"
    
    def __repr__(self) -> str:
        return f"AirQualityIndex(title={self.title}, value={self.value}, category={self.category}, description={self.description}, acronym:{self.acronym}, color={self.color})"
    
    @staticmethod
    def _extract_aqi(data: str):
        parts = data.split('\n')
        title = parts[0].strip()
        aqi = int(parts[1].strip())
        category = parts[2].strip() if len(parts) > 2 else None
        description = parts[3].strip() if len(parts) > 3 else None
        acronym = ''.join(word[0].strip().upper() for word in title.split())

        return title, aqi, category, description, acronym
    
    # 'Air Quality Index\n26\nGood\nAir quality is considered satisfactory, and air pollution poses little or no risk.'
    @classmethod
    def from_string(cls, data: str) -> 'AirQualityIndex':
        try:
            title, aqi, category, description, acronym = AirQualityIndex._extract_aqi(data)
            return cls(title, aqi, category, description, acronym)
        except (ValueError, IndexError) as e:
            raise ValueError("Invalid AQI data format") from e
        
    @classmethod
    def aqi_color_from_string(cls, aqi_data: str, color_data: str):
        try:
            title, aqi, category, description, acronym = AirQualityIndex._extract_aqi(aqi_data)
            color = Color.from_string(color_data)
            return cls(title, aqi, category, description, acronym, color)
        except(ValueError, IndexError) as e:
            raise ValueError("Invalid AQI data format or color data format") from e

