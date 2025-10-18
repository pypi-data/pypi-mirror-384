from datetime import date

from tp_shared.base.base_message import BaseMessage
from tp_shared.types.pass_allowed_zone import PassAllowedZone
from tp_shared.types.pass_series import PassSeries
from tp_shared.types.pass_time_of_date import PassTimeOfDate


class MosPassesResultPass(BaseMessage):
    reg_number: str
    time_of_day: PassTimeOfDate
    series: PassSeries
    number: str
    allowed_zone: PassAllowedZone
    start_date: date
    end_date: date
    cancel_date: date | None


class MosPassesResultMessage(BaseMessage):
    version: str = "1.0"
    reg_number: str
    passes: list[MosPassesResultPass] = []
