from redis.asyncio import Redis
from tp_helper.base_queues.base_stream_queue_repo import BaseStreamQueueRepo

from tp_shared.gibdd_service.schemas.gibdd_fine_result_message import (
    GibddFineResultMessage,
)


class GibddFineResultsStreamQueueRepo(BaseStreamQueueRepo):
    QUEUE_NAME = "gibdd:service:fine:results:stream"

    def __init__(self, redis_client: Redis):
        super().__init__(
            redis_client=redis_client,
            schema=GibddFineResultMessage,
            queue_name=self.QUEUE_NAME,
        )
