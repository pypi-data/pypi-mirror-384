def wind_to_dict(wind):
    if wind is None:
        return None
    return {
        "direction": wind.direction,
        "speed": wind.speed
    }
