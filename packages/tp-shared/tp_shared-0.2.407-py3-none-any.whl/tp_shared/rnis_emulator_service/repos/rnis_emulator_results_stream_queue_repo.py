from redis.asyncio import Redis
from tp_helper.base_queues.base_stream_queue_repo import BaseStreamQueueRepo

from tp_shared.rnis_emulator_service.schemas.rnis_emulator_result_message import (
    RnisEmulatorResultMessage,
)


class RnisEmulatorResultsStreamQueueRepo(BaseStreamQueueRepo):
    QUEUE_NAME = "rnis:emulator:service:results:stream"

    def __init__(self, redis_client: Redis):
        super().__init__(
            redis_client=redis_client,
            schema=RnisEmulatorResultMessage,
            queue_name=self.QUEUE_NAME,
        )
