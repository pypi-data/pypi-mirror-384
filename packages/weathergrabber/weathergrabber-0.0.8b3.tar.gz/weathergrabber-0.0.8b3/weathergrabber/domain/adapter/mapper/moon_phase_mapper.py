from weathergrabber.domain.moon_phase import MoonPhase
from weathergrabber.domain.moon_phase_enum import MoonPhaseEnum

def moon_phase_to_dict(mp: MoonPhase) -> dict:
    return {
        "icon": mp.icon.name if mp.icon else None,
        "phase": mp.phase,
        "label": mp.label,
    }
