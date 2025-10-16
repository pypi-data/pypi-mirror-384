from weathergrabber.domain.day_night import DayNight

def day_night_to_dict(dn: DayNight) -> dict:
    def temp_to_dict(temp):
        return {
            "label": temp.label,
            "value": temp.value,
        } if temp else None
    return {
        "day": temp_to_dict(dn.day) if dn.day else None,
        "night": temp_to_dict(dn.night) if dn.night else None,
    }
