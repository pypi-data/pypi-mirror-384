class UVIndex:

    def __init__(self, string_value: str, index: str, of: str = None, label:str = None):
        self._string_value = string_value
        self._index = index
        self._of = of
        self._label = label

    @property
    def string_value(self) -> str:
        return self._string_value

    @property
    def index(self) -> str:
        return self._index
    
    @property
    def of(self) -> str:
        return self._of

    @property
    def label(self) -> str:
        return self._label

    @classmethod
    def from_string(cls, data: str, label: str = None) -> 'UVIndex':
        parts = data.split(' ')
        if len(parts) == 1:
            return cls(string_value = data, index= parts[0].strip(), of="", label=label)
        elif len(parts) == 3:
            index, of, some = parts
            return cls(string_value = data, index=index.strip(), of=some.strip(), label=label)
        elif len(data) == 0:
            raise ValueError("UV Index string cannot be empty")
        else:
            return cls(string_value = data, index="", of="", label=label)
    
    def __repr__(self) -> str:
        return f"UVIndex(string_value={self.string_value!r}, index={self.index!r}, of={self.of!r}, label={self.label!r})"
    
    def __str__(self) -> str:
        if self.string_value:
            return f"{self.label} {self.string_value}"
        elif self.index and self.of:
            return f"{self.label} {self.index} {self.of}" if self.label else f"{self.index} {self.of}"