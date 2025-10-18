from redis.asyncio import Redis
from tp_helper.base_queues.base_stream_queue_repo import BaseStreamQueueRepo

from tp_shared.rnis_check_service.schemas.rnis_check_result_message import (
    RNISCheckResultMessage,
)


class RNISCheckResultsStreamQueueRepo(BaseStreamQueueRepo):
    QUEUE_NAME = "rnis:check:service:results:stream"

    def __init__(self, redis_client: Redis):
        super().__init__(
            redis_client=redis_client,
            schema=RNISCheckResultMessage,
            queue_name=self.QUEUE_NAME,
        )
