from datetime import datetime

from pydantic import ConfigDict
from tp_helper.base_items.base_schema import BaseSchema

from tp_shared.moneta_service.types.moneta_charge_status import (
    MonetaServiceChargeStatus,
)


class MonetaChargeResultMessage(BaseSchema):
    payer_identifier: str
    additional_payer_identifier: str | None = None
    supplier_bill_id: str
    sts_number: str
    reg_number: str
    amount_to_pay: float
    date_time: datetime
    wire_kpp: str
    signature: str | None = None
    discount_date: datetime | None = None
    discount_size: float | None = None
    wire_kbk: str
    wire_user_inn: str
    discount_amount: float
    department_code: str | None = None
    legal_act: str | None = None
    offense_date: datetime | None = None
    offense_place: str | None = None
    department_name: str | None = None
    offense_coordinates: str | None = None
    bill_date: datetime
    wire_bank_account: str
    total_amount: float
    payee_name: str
    wire_bank_name: str
    wire_oktmo: str
    wire_bank_ks: str
    wire_payment_purpose: str
    acknowledgment_status: int
    payer_name: str
    change_status: MonetaServiceChargeStatus
    wire_bank_bik: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
