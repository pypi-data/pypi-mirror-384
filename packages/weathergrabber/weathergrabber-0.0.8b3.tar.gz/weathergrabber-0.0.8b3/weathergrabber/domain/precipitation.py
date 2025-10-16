class Precipitation:

    def __init__(
            self,
            percentage: str,
            amount: str = None
        ):
        self._percentage = percentage
        self._amount = amount

    @property
    def percentage(self) -> str:
        return self._percentage
    
    @property
    def amount(self) -> str:
        return self._amount

    def __repr__(self):
        return f"Precipitation(percentage='{self.percentage}', amount='{self.amount}')" 