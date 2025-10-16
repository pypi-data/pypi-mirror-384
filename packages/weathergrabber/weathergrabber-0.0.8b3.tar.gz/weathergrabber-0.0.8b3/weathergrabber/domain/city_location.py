class CityLocation:

    def __init__(self, city: str, state_province: str = None, country: str = None, location = None):
        self._city = city
        self._state_province = state_province
        self._country = country
        self._location = location

    @property
    def city(self) -> str:
        return self._city
    
    @property
    def state_province(self) -> str:
        return self._state_province
    
    @property
    def country(self) -> str:
        return self._country
    
    @property
    def location(self):
        return self._location
    
    def __repr__(self):
        return f"CityLocation(city={self.city}, state_province={self.state_province}, country={self.country}, location={self.location})"
    
    def __str__(self):
        parts = []
        if self.location:
            parts.append(self.location)
        if self.city:
            parts.append(self.city)
        if self.state_province:
            parts.append(self.state_province)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts) if parts else "Unknown Location"

    @classmethod
    def from_string(cls, data: str) -> "CityLocation":
        #'Nova Friburgo, Rio de Janeiro, Brazil'
        #'Macuco, Santos, São Paulo, Brésil'
        #'New York, NY, USA'
        #'Tokyo, Tokyo Prefecture, Japan'
        country, state_province, city, location = None, None, None, None
        parts = data.split(", ")

        if len(parts) > 2:
            i = len(parts) - 1
            while i > 0:
                if not country:
                    country = parts[i]
                elif not state_province:
                    state_province = parts[i]
                elif not city:
                    city = parts[i]
                i -= 1
            # Location is the first registry. If it's different from city, use it.
            if city != parts[0]:
                location = parts[0]
            return cls(city=city, state_province=state_province, country=country, location=location)
        
        if len(parts) == 2:
            city, state_province = parts
            return cls(city=city, state_province=state_province)
        elif len(parts) == 1:
            city = parts[0]
            return cls(city=city)
        else:
            raise ValueError("Invalid city location string format")