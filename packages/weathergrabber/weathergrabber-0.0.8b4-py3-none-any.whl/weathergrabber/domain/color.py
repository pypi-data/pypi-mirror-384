import re

class Color:

    def __init__(self, red: str | int, green: str | int, blue: str | int):
        self._red = self._int_or_hex(red)
        self._green = self._int_or_hex(green)
        self._blue = self._int_or_hex(blue)

    def _int_or_hex(self, value: str | int) -> int:
        if type(value) == int:
            if not (0 <= value <= 255):
                raise ValueError("RGB integer values must be between 0 and 255")
            return value
        return int(value, 16)

    @property
    def red(self) -> int:
        return self._red
    
    @property
    def green(self) -> int:
        return self._green
    
    @property
    def blue(self) -> int:
        return self._blue
    
    @classmethod
    def from_string(cls,string_value: str) -> "Color":

        color_pattern = r"#([0-9A-Fa-f]{6})"        
        
        try:
            match = re.search(color_pattern, string_value)
            color = f"#{match.group(1)}"
            hex_color = color.lstrip('#')
            r, g, b = hex_color[:2], hex_color[2:4], hex_color[4:]
            return cls(r, g, b)
        except (AttributeError, ValueError):
            raise ValueError(f"Invalid color string: {string_value}")

    @property
    def hex(self) -> str:
        return f"{self.red:02x}{self.green:02x}{self.blue:02x}".upper()
    
    @property
    def rgb(self) -> str:
        return f"rgb({self.red}, {self.green}, {self.blue})"
    
    def __str__(self):
        return f"{self.hex}"
    
    def __repr__(self):
        return f"Color(red='{self.red}', green='{self.green}', blue='{self.blue}')"