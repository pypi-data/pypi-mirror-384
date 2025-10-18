from datetime import date

from tp_helper.base_items.base_schema import BaseSchema

from tp_shared.nsis_service.types.nsis_task_type import NsisTaskType
from tp_shared.types.policy_series import PolicySeries
from tp_shared.types.policy_status import PolicyStatus


class NsisResultPolicy(BaseSchema):
    status: PolicyStatus
    series: PolicySeries
    number: str
    start_date: date | None = None
    end_date: date | None = None
    insurer_name: str


class NsisResultMessage(BaseSchema):
    task_type: NsisTaskType
    query: str
    request_date: date
    policies: list[NsisResultPolicy] = []
