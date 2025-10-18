from redis.asyncio import Redis
from tp_helper.base_queues.base_stream_queue_repo import BaseStreamQueueRepo

from tp_shared.mos_passes_service.schemas.mos_passes_result_message import (
    MosPassesResultMessage,
)


class MosPassesResultsStreamQueueRepo(BaseStreamQueueRepo):
    QUEUE_NAME = "mos:passes:service:results:stream"

    def __init__(self, redis_client: Redis):
        super().__init__(
            redis_client=redis_client,
            schema=MosPassesResultMessage,
            queue_name=self.QUEUE_NAME,
        )
