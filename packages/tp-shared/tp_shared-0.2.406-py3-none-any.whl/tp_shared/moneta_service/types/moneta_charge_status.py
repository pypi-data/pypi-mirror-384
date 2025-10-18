from enum import Enum


class MonetaServiceChargeStatus(Enum):
    NEW = 1
    CLARIFICATION = 2
    ANNULATION = 3
    DEANNULATION = 4
