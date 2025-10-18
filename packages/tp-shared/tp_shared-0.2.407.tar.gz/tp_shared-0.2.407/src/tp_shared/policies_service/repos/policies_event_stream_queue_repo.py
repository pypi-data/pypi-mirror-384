from redis.asyncio import Redis
from tp_helper.base_queues.base_stream_queue_repo import BaseStreamQueueRepo

from tp_shared.policies_service.schemas.policies_result_message import (
    PoliciesResultMessage,
)


class PoliciesResultsStreamQueueRepo(BaseStreamQueueRepo):
    QUEUE_NAME = "policies:service:results:stream"

    def __init__(self, redis_client: Redis):
        super().__init__(
            redis_client=redis_client,
            schema=PoliciesResultMessage,
            queue_name=self.QUEUE_NAME,
        )
