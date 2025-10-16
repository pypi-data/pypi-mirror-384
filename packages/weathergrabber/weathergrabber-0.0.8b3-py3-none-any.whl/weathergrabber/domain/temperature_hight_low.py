class TemperatureHighLow:
    def __init__(self, high: str, low: str, label:str = None):
        self._high = high
        self._low = low
        self._label = label

    @classmethod
    def from_string(cls, data: str, label:str = None) -> 'TemperatureHighLow':
        parts = data.split('/')
        if len(parts) == 2:
            high, low = parts
            return cls(high=high.strip(), low=low.strip(), label=label)
        else:
            raise ValueError("Invalid temperature high/low string format")

    @property
    def high(self) -> str:
        return self._high
    
    @property
    def low(self) -> str:
        return self._low

    @property
    def label(self) -> str:
        return self._label

    def __repr__(self):
        return f"TemperatureHighLow(high={self.high!r}, low={self.low!r}, label={self.label!r})"

    def __str__(self):
        return f"{self.high}/{self.low}"