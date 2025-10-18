from enum import Enum


class PassAllowedZone(str, Enum):
    MKAD = "МКАД"
    SK = "СК"
    TTK = "ТТК"
    MO = "МО"
