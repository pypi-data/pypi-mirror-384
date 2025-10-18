from redis.asyncio import Redis
from tp_helper.base_queues.base_ack_list_queue_repo import BaseAckListQueueRepo

from tp_shared.nsis_service.schemas.nsis_result_message import (
    NsisResultMessage,
)


class NsisResultsAckListQueueRepo(BaseAckListQueueRepo):
    QUEUE_NAME = "nsis:service:results:ack:list"

    def __init__(self, redis_client: Redis):
        super().__init__(redis_client, message_type=NsisResultMessage)
