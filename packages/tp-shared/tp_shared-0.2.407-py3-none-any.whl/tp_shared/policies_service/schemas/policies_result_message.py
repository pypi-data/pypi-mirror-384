from datetime import date

from tp_shared.base.base_message import BaseMessage
from tp_shared.types.policy_series import PolicySeries
from tp_shared.types.policy_status import PolicyStatus


class PoliciesResultPolicy(BaseMessage):
    series: PolicySeries
    number: str
    status: PolicyStatus
    start_date: date | None = None
    end_date: date | None = None
    period1_start: date | None = None
    period1_end: date | None = None
    period2_start: date | None = None
    period2_end: date | None = None
    period3_start: date | None = None
    period3_end: date | None = None
    vin: str | None = None
    car_mark: str | None = None
    car_model: str | None = None


class PoliciesResultMessage(BaseMessage):
    version: str = "1.0"
    reg_number: str
    policies: list[PoliciesResultPolicy] = []
