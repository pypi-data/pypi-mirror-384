from datetime import date, datetime

from tp_helper.base_items.base_schema import BaseSchema

from tp_shared.base.base_message import BaseMessage


class GibddVehicleSchema(BaseSchema):
    reg_number: str
    sts_number: str
    is_valid: bool
    invalided_at: int | None = None


class GibddFineResultSchema(BaseSchema):
    supplier_bill_id: str | None = None
    reg_number: str
    sts_number: str
    discount: bool | None = None
    discount_date: datetime | None = None
    decision_date: datetime | None = None
    law: str | None = None
    law_text: str | None = None
    vehicle_model: str | None = None
    breach_year: int | None = None
    act_num: str | None = None
    summa: int | None = None
    division: int | None = None
    post_id: str | None = None
    act_date: date | None = None
    ssp_date: date | None = None


class GibddFineResultMessage(BaseMessage):
    version: str = "1.0"
    vehicle: GibddVehicleSchema
    fines: list[GibddFineResultSchema]
