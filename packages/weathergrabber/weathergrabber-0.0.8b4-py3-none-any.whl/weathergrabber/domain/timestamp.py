import re

class Timestamp:

    def __init__(self, time: str, gmt: str, text: str = None):
        self._time = time
        self._gmt = gmt
        self._text = text

    @property
    def time(self) -> str:
        return self._time
    
    @property
    def gmt(self) -> str:
        return self._gmt
    
    @property
    def text(self) -> str:
        return self._text
    
    def __repr__(self):
        return f"Timestamp(time='{self.time}', gmt='{self.gmt}', text='{self.text}')"
    
    def __str__(self):
        if self.text != None:
            return self.text
        return f"As of {self.time} {self.gmt}"
    
    @classmethod
    def from_string(cls, text) -> "Timestamp":
        # "As of 4:23 pm GMT-03:00",
        # "As of 4:23 pm EDT",
        # "As of 16:37 GMT-03:00",
        # "Até 16:38 GMT-03:00"
        # "Até 20:44 EDT"
        # Simplified: just match time (with optional am/pm) and timezone (GMT offset or abbreviation)
        pattern = re.compile(r'(\d{1,2}:\d{2}(?: ?[ap]m)?)\s*((?:GMT[+-]\d{2}:\d{2})|[A-Z]{2,4})', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            time, gmt = match.groups()
            return cls(time=time, gmt=gmt, text=text)