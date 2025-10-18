from redis.asyncio import Redis
from tp_helper.base_queues.base_ack_list_queue_repo import BaseAckListQueueRepo

# from src.config import config
from tp_shared.autoins_mpg_service.schemas.autoins_result_message import (
    AutoinsResultMessage,
)


class AutoinsResultsAckListQueueRepo(BaseAckListQueueRepo):
    QUEUE_NAME = "autoins:service:results:ack:list"

    def __init__(self, redis_client: Redis):
        super().__init__(redis_client=redis_client, message_type=AutoinsResultMessage)
