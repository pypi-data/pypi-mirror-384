from enum import Enum


class PolicyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WAITING_ACTIVATION = "WAITING_ACTIVATION"
    EXPIRED = "EXPIRED"
