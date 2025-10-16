class Wind:

    def __init__(self,direction: str,speed: str):
        self._direction = direction
        self._speed = speed

    @property
    def direction(self) -> str:
        return self._direction
    
    @property
    def speed(self) -> str:
        return self._speed
    
    def __str__(self):
        return f"Wind Speed: {self.direction} {self.speed}"
    
    def __repr__(self):
        return f"Wind(direction:'{self.direction}', speed: '{self.speed}')"
    
    @classmethod
    def from_string(cls, data: str) -> 'Wind':
        parts = data.split(" ")
        if len(parts) == 2:
            direction, speed = parts
            return cls(direction=direction.strip(), speed=speed.strip())
        else:
            raise ValueError("Invalid Wind Speed string format")