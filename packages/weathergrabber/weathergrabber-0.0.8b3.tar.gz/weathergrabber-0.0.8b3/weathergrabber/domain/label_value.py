class LabelValue:
    def __init__(self, label: str, value: str):
        self._label = label
        self._value = value

    @property
    def label(self) -> str:
        return self._label

    @property
    def value(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"LabelValue(label={self.label!r}, value={self.value!r})"
    

    def __str__(self) -> str:
        return f"{self.label} {self.value}"