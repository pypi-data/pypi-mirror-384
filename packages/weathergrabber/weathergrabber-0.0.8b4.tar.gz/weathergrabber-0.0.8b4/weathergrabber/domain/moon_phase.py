from weathergrabber.domain.moon_phase_enum import MoonPhaseEnum

class MoonPhase:
    def __init__(self, icon: MoonPhaseEnum, phase: str, label:str = None):
        self._label = label
        self._icon = icon
        self._phase = phase

    @property
    def label(self) -> str:
        return self._label

    @property
    def icon(self) -> MoonPhaseEnum:
        return self._icon
    
    @property
    def phase(self) -> str:
        return self._phase
    
    def __repr__(self) -> str:
        return f"MoonPhase(icon={self.icon!r}, phase={self.phase!r},label={self.label!r})"