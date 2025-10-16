class DayNight:
    class Temperature:
        def __init__(self, label: str, value: str):
            self._label = label
            self._value = value

        @property
        def label(self):
            return self._label
        
        @property
        def value(self):
            return self._value
        
        @classmethod
        def from_string(cls, text:str) -> 'DayNight.Temperature':
            label, value = text.split("\xa0")
            return cls(label.strip(), value.strip())

        def __repr__(self):
            return f"DayNight.Temperature(label={self.label!r}, value={self.value!r})"
        
        def __str__(self):
            return f"{self.label}: {self.value}"


    def __init__(self, day: "DayNight.Temperature", night: "DayNight.Temperature"):
        self._day = day
        self._night = night

    @property
    def day(self):
        return self._day
    
    @property
    def night(self):
        return self._night
    
    @classmethod
    def from_string(cls, text: str) -> 'DayNight':
        day_label, night_label = text.split("•")
        day = DayNight.Temperature.from_string(day_label.strip())
        night = DayNight.Temperature.from_string(night_label.strip())
        return cls(day, night)
    
    def __repr__(self):
        return f"DayNight(day={self.day!r}, night={self.night!r})"
    
    def __str__(self):
        return f"Day: {self.day}, Night: {self.night}"