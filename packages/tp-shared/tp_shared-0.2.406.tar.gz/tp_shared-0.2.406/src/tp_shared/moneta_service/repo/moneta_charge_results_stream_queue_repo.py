from redis.asyncio import Redis
from tp_helper.base_queues.base_stream_queue_repo import BaseStreamQueueRepo

from tp_shared.moneta_service.schemas.moneta_charge_result_message import (
    MonetaChargeResultMessage,
)


class MonetaChargeResultsStreamQueueRepo(BaseStreamQueueRepo):
    QUEUE_NAME = "moneta:service:moneta:charge:results"

    def __init__(self, redis_client: Redis):
        super().__init__(
            redis_client=redis_client,
            schema=MonetaChargeResultMessage,
            queue_name=self.QUEUE_NAME,
        )
