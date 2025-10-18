from datetime import date

from pydantic import BaseModel

from tp_shared.types.policy_series import PolicySeries


class AutoinsResultPolicy(BaseModel):
    insurer_name: str
    reg_number: str
    series: PolicySeries
    number: str
    start_date: date
    end_date: date
    period1_start: date | None = None
    period1_end: date | None = None
    period2_start: date | None = None
    period2_end: date | None = None
    period3_start: date | None = None
    period3_end: date | None = None
    vin: str | None = None
    body_number: str | None = None
    chassis_number: str | None = None
    car_mark: str | None = None
    car_model: str | None = None
    external_policy_id: int | None = None
    policy_state: str | None = None
    policy_status_t_use: str | None = None


class AutoinsResultMessage(BaseModel):
    series: PolicySeries
    number: str
    policies: list[AutoinsResultPolicy] = []
