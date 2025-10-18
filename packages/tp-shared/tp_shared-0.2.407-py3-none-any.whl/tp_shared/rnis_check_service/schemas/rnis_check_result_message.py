from tp_shared.base.base_message import BaseMessage


class RNISCheckResultMessage(BaseMessage):
    version: str = "1.0"
    reg_number: str
    exists: bool
    last_mark: int | None
    terminals_amount: int
