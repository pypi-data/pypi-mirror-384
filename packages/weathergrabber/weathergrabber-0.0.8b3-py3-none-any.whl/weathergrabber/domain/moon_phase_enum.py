from enum import Enum

class MoonPhaseEnum(Enum):
# New Moon
    PHASE_0 = ("phase-0", "\uf186", "🌑")
    # Waxing Crescent
    PHASE_1 = ("phase-1", "\uf186", "🌒")
    PHASE_2 = ("phase-2", "\uf186", "🌒")
    PHASE_3 = ("phase-3", "\uf186", "🌒")
    PHASE_4 = ("phase-4", "\uf186", "🌒")
    # First Quarter
    PHASE_5 = ("phase-5", "\uf186", "🌓")
    PHASE_6 = ("phase-6", "\uf186", "🌓")
    PHASE_7 = ("phase-7", "\uf186", "🌓")
    # Waxing Gibbous
    PHASE_8 = ("phase-8", "\uf186", "🌔")
    PHASE_9 = ("phase-9", "\uf186", "🌔")
    PHASE_10 = ("phase-10", "\uf186", "🌔")
    PHASE_11 = ("phase-11", "\uf186", "🌔")
    PHASE_12 = ("phase-12", "\uf186", "🌔")
    PHASE_13 = ("phase-13", "\uf186", "🌕")
    # Full Moon
    PHASE_14 = ("phase-14", "\uf186", "🌕")
    PHASE_15 = ("phase-15", "\uf186", "🌕")
    # Waning Gibbous
    PHASE_16 = ("phase-16", "\uf186", "🌖")
    PHASE_17 = ("phase-17", "\uf186", "🌖")
    PHASE_18 = ("phase-18", "\uf186", "🌖")
    PHASE_19 = ("phase-19", "\uf186", "🌖")
    PHASE_20 = ("phase-20", "\uf186", "🌖")
    # Last Quarter
    PHASE_21 = ("phase-21", "\uf186", "🌗")
    PHASE_22 = ("phase-22", "\uf186", "🌗")
    PHASE_23 = ("phase-23", "\uf186", "🌗")
    PHASE_24 = ("phase-24", "\uf186", "🌗")
    
    PHASE_25 = ("phase-25", "\uf186", "🌘")
    PHASE_26 = ("phase-26", "\uf186", "🌘")
    PHASE_27 = ("phase-27", "\uf186", "🌘")
    PHASE_28 = ("phase-28", "\uf186", "🌘")
    DEFAULT = ("default", "\uf186", "🌑")

    def __init__(self, name: str, fa_icon: str, emoji_icon: str):
        self._name = name
        self._fa_icon = fa_icon
        self._emoji_icon = emoji_icon

    @property
    def name(self):
        return self._name

    @property
    def fa_icon(self):
        return self._fa_icon

    @property
    def emoji_icon(self):
        return self._emoji_icon

    @staticmethod
    def from_name(name: str):
        for item in MoonPhaseEnum:
            if item._name == name:
                return item
        return None
