from enum import Enum, StrEnum


class RnisEmulatorResultType(StrEnum):
    TASK = "TASK"
    SUBSCRIPTION = "SUBSCRIPTION"


class RnisEmulatorActionType(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class RnisEmulatorTaskStatus(str, Enum):
    WAITING = "WAITING"
    CALCULATING = "CALCULATING"
    CALCULATED = "CALCULATED"  # Расчёт проведён, готова к эмуляции
    IN_WORK = "IN_WORK"
    UNLOADING = "UNLOADING"
    PARKING = "PARKING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    ERROR = "ERROR"


class RnisEmulatorSubscriptionStatus(str, Enum):
    # первичный, только что создана, ещё не активна
    CREATED = "CREATED"
    # работает
    ACTIVE = "ACTIVE"
    # вручную приостановлена
    SUSPENDED = "SUSPENDED"
    # закончилась по сроку
    EXPIRED = "EXPIRED"
