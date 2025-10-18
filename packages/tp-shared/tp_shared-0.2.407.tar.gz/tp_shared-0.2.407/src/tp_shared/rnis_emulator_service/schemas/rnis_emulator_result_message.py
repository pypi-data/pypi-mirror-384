import uuid
from datetime import date

from pydantic import model_validator
from tp_helper.base_items.base_schema import BaseSchema

from tp_shared.rnis_emulator_service.types.rnis_emulator_types import (
    RnisEmulatorActionType,
    RnisEmulatorResultType,
    RnisEmulatorSubscriptionStatus,
    RnisEmulatorTaskStatus,
)
from tp_shared.types.pass_time_of_date import PassTimeOfDate


class RnisEmulatorResultTask(BaseSchema):
    task_id: uuid.UUID
    subscription_id: uuid.UUID
    reg_number: str
    is_test_drive: bool
    time_of_day: PassTimeOfDate
    status: RnisEmulatorTaskStatus
    error_message: str | None = None
    started_at: int | None = None
    ended_at: int | None = None


class RnisEmulatorResultSubscription(BaseSchema):
    subscription_id: uuid.UUID
    reg_number: str
    time_of_day: PassTimeOfDate
    status: RnisEmulatorSubscriptionStatus
    monthly_run_count: int
    start_date: date
    end_date: date
    created_at: int

    @model_validator(mode="after")
    def _check_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date не может быть позже end_date")
        return self


class RnisEmulatorResultMessage(BaseSchema):
    type: RnisEmulatorResultType
    task: RnisEmulatorResultTask | None = None
    subscription: RnisEmulatorResultSubscription | None = None
    action_type: RnisEmulatorActionType

    @model_validator(mode="after")
    def _one_of_task_or_subscription(self):
        if (self.task is None) and (self.subscription is None):
            raise ValueError(
                "Должно быть заполнено хотя бы одно поле: 'task' или 'subscription'."
            )
        return self
