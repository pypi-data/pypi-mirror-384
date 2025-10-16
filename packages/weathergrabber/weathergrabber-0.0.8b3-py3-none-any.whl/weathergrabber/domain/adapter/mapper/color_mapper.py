from weathergrabber.domain.color import Color

def color_to_dict(color: Color) -> dict:
    return {
        "red": color.red,
        "green": color.green,
        "blue": color.blue,
        "hex": color.hex,
        "rgb": color.rgb,
    }
